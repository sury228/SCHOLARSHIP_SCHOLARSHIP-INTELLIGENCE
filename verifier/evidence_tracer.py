import re
from typing import Dict, List

class EvidenceTracer:
    @staticmethod
    def verify_field_evidence(extracted_data: Dict, raw_text: str) -> List[Dict]:
        """
        Anti-Hallucination Evidence Tracer:
        Programmatically checks if the LLM's `source_quotes` exist as valid substrings in the raw webpage text.
        Returns a list of verification records for each field.
        """
        evidence_records = []
        quotes = extracted_data.get("quotes", {})
        cleaned_raw_text = EvidenceTracer._normalize_text(raw_text)

        fields_to_verify = [
            ("name", extracted_data.get("name")),
            ("provider", extracted_data.get("provider")),
            ("amount", extracted_data.get("amount")),
            ("eligibility_academic", extracted_data.get("eligibility_academic")),
            ("eligibility_income", extracted_data.get("eligibility_income")),
            ("deadline", extracted_data.get("deadline"))
        ]

        for field_name, val in fields_to_verify:
            if not val:
                continue

            quote = quotes.get(field_name, "")
            is_verified = False

            if quote:
                norm_quote = EvidenceTracer._normalize_text(quote)
                # Check if exact or normalized quote is in raw text
                if norm_quote in cleaned_raw_text or quote.strip().lower() in raw_text.lower():
                    is_verified = True
                else:
                    # Fallback check: see if the extracted value itself is directly in raw text
                    norm_val = EvidenceTracer._normalize_text(str(val))
                    if norm_val and norm_val in cleaned_raw_text:
                        is_verified = True
                        quote = f"Value substring match: '{val}'"
            else:
                # If no quote was provided, try direct substring match of value
                norm_val = EvidenceTracer._normalize_text(str(val))
                if norm_val and norm_val in cleaned_raw_text:
                    is_verified = True
                    quote = f"Direct match: '{val}'"

            evidence_records.append({
                "field_name": field_name,
                "extracted_value": str(val),
                "source_quote": quote or "No quote provided",
                "is_verified_substring": is_verified
            })

        return evidence_records

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip().lower()
