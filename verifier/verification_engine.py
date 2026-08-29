from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple
from crawler.source_classifier import classify_source_domain, is_official_domain

class VerificationEngine:
    def __init__(self, scoring_weights: Dict = None, verified_min_score: float = 95.0):
        self.weights = scoring_weights or {
            "official_source_domain": 25,
            "active_live_page": 20,
            "critical_fields_present": 15,
            "evidence_traceability": 20,
            "valid_application_link": 10,
            "timeline_validity": 10
        }
        self.verified_min_score = verified_min_score

    def evaluate_scholarship(
        self,
        extracted_data: Dict,
        page_fetch_result: Dict,
        evidence_records: List[Dict]
    ) -> Tuple[float, str, Dict]:
        """
        Computes deterministic confidence score (0 - 100%) and determines status.
        Returns tuple of (confidence_score, status_string, score_breakdown).
        """
        score_breakdown = {}
        url = page_fetch_result.get("url", "")
        status_code = page_fetch_result.get("status_code", 0)

        # 1. Official Source Domain (25%)
        is_official = is_official_domain(url)
        score_breakdown["official_source_domain"] = self.weights["official_source_domain"] if is_official else 10.0

        # 2. Active Live Page (20%)
        if status_code == 200 and page_fetch_result.get("is_success"):
            score_breakdown["active_live_page"] = float(self.weights["active_live_page"])
        else:
            score_breakdown["active_live_page"] = 0.0

        # 3. Critical Fields Extracted (15%)
        critical_fields = ["name", "provider", "amount", "deadline"]
        present_count = sum(1 for f in critical_fields if extracted_data.get(f))
        score_breakdown["critical_fields_present"] = (present_count / len(critical_fields)) * self.weights["critical_fields_present"]

        # 4. Evidence Traceability (20%)
        if evidence_records:
            verified_count = sum(1 for rec in evidence_records if rec.get("is_verified_substring"))
            score_breakdown["evidence_traceability"] = (verified_count / len(evidence_records)) * self.weights["evidence_traceability"]
        else:
            score_breakdown["evidence_traceability"] = 0.0

        # 5. Valid Application Link (10%)
        app_url = extracted_data.get("application_url")
        if app_url and app_url.startswith("http"):
            score_breakdown["valid_application_link"] = float(self.weights["valid_application_link"])
        else:
            score_breakdown["valid_application_link"] = 0.0

        # 6. Timeline Validity (10%)
        deadline_str = extracted_data.get("deadline")
        timeline_score, deadline_status = self._evaluate_timeline(deadline_str)
        score_breakdown["timeline_validity"] = timeline_score

        # Calculate Total Confidence Score
        total_score = sum(score_breakdown.values())
        total_score = round(min(100.0, max(0.0, total_score)), 2)

        # Determine Final Status
        if status_code != 200:
            status = "NO_LONGER_VERIFIABLE"
        elif deadline_status == "EXPIRED":
            status = "EXPIRED"
        elif deadline_status == "EXPIRING_SOON":
            status = "EXPIRING_SOON"
        elif total_score >= self.verified_min_score:
            status = "VERIFIED"
        else:
            status = "REVIEW_REQUIRED"

        return total_score, status, score_breakdown

    def _evaluate_timeline(self, deadline_str: str) -> Tuple[float, str]:
        """Parses deadline string and evaluates validity against current date."""
        if not deadline_str:
            return 0.0, "UNKNOWN"

        try:
            # Match common ISO or date patterns
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", deadline_str)
            if date_match:
                parsed_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            else:
                # Try parsing readable date format e.g. "31st October 2026"
                clean_str = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", deadline_str)
                parsed_date = None
                for fmt in ["%d %B %Y", "%d %b %Y", "%d/%m/%Y"]:
                    try:
                        parsed_date = datetime.strptime(clean_str.strip(), fmt)
                        break
                    except ValueError:
                        continue
                if not parsed_date:
                    return 5.0, "FUTURE" # Text present but unparsed

            now = datetime.now()
            days_remaining = (parsed_date - now).days

            if days_remaining < 0:
                return 0.0, "EXPIRED"
            elif days_remaining <= 7:
                return 8.0, "EXPIRING_SOON"
            else:
                return float(self.weights["timeline_validity"]), "ACTIVE"

        except Exception:
            return 5.0, "FUTURE"
