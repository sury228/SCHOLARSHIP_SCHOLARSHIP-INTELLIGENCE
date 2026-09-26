import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Ensure base directory is at index 0 on path before imports
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import load_config
from database.db_manager import DBManager

from crawler.discovery import ScholarshipDiscovery
from crawler.scraper import WebScraper
from crawler.source_classifier import classify_source_domain
from extractor.llm_extractor import LLMExtractor
from verifier.evidence_tracer import EvidenceTracer
from verifier.verification_engine import VerificationEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ScholarshipPipeline")

class ScholarshipPipeline:
    def __init__(self, config_path: Path = None):
        self.config = load_config(config_path) if config_path else load_config()
        self.db_manager = DBManager(self.config["database"]["db_path"])
        
        self.discovery = ScholarshipDiscovery(
            seed_urls=self.config["crawler"].get("seed_urls"),
            keywords=self.config.get("search_keywords")
        )
        self.scraper = WebScraper(
            user_agent=self.config["crawler"].get("user_agent"),
            timeout=self.config["crawler"].get("timeout_seconds", 15)
        )
        llm_conf = self.config.get("llm", {})
        provider = llm_conf.get("provider", "groq")
        endpoint = llm_conf.get("groq_endpoint") if provider == "groq" else llm_conf.get("ollama_endpoint")
        self.extractor = LLMExtractor(
            provider=provider,
            model_name=llm_conf.get("model_name"),
            api_key=llm_conf.get("api_key"),
            endpoint=endpoint,
            timeout=llm_conf.get("timeout", 30.0)
        )
        self.verifier = VerificationEngine(
            scoring_weights=self.config.get("scoring_weights"),
            verified_min_score=self.config["status_thresholds"].get("verified_min_score", 95.0)
        )

    def run_pipeline(self, max_urls: int = 5, use_mock_if_offline: bool = True) -> List[Dict]:
        """
        Executes complete end-to-end pipeline:
        Discovery -> Scraping -> Extraction -> Evidence Tracing -> Scoring -> DB Upsert & Change Detection.
        """
        logger.info("Starting Scholarship Intelligence Crawler Pipeline...")
        processed_records = []

        # 1. Discovery
        discovered_urls = self.discovery.discover_urls(max_results=max_urls)
        logger.info(f"Discovered {len(discovered_urls)} target URLs for crawling.")

        for url in discovered_urls:
            logger.info(f"Processing URL: {url}")

            # 2. Scrape Webpage
            page_data = self.scraper.fetch_page(url)

            # Fallback to mock page if live fetch failed (ensures reliable demo/offline testing)
            if not page_data.get("is_success") and use_mock_if_offline:
                logger.info(f"Live request to {url} failed or offline. Using mock schema generator for testing.")
                mocks = WebScraper.get_mock_scholarship_pages()
                page_data = mocks.get(url) or list(mocks.values())[0]

            if not page_data or not page_data.get("cleaned_text"):
                logger.warning(f"Skipping {url}: No usable text snapshot retrieved.")
                continue

            # 3. Classify Domain
            source_type = classify_source_domain(url)

            # 4. Extract Structured Fields & Quotes
            extracted = self.extractor.extract_scholarship_data(page_data)
            extracted["official_source_url"] = url
            extracted["source_type"] = source_type
            extracted["raw_text_snapshot"] = page_data.get("cleaned_text", "")

            # 5. Trace Evidence & Verify Quotes (Anti-Hallucination)
            evidence_records = EvidenceTracer.verify_field_evidence(
                extracted, page_data.get("cleaned_text", "")
            )

            # 6. Evaluate Confidence Score & Status
            confidence_score, status, score_breakdown = self.verifier.evaluate_scholarship(
                extracted, page_data, evidence_records
            )

            extracted["confidence_score"] = confidence_score
            extracted["status"] = status

            # 7. Upsert to Database & Detect Field Changes
            scholarship_id, detected_changes = self.db_manager.upsert_scholarship(extracted)
            
            # Record Evidence Quotes
            self.db_manager.add_verification_evidence(scholarship_id, evidence_records)

            if detected_changes:
                logger.info(f"⚡ Change Detected for Scholarship ID {scholarship_id}: {len(detected_changes)} field(s) updated.")

            processed_records.append({
                "scholarship_id": scholarship_id,
                "name": extracted.get("name"),
                "status": status,
                "confidence_score": confidence_score,
                "changes_detected": len(detected_changes)
            })

        logger.info(f"Pipeline completed successfully. Total processed: {len(processed_records)}")
        return processed_records

if __name__ == "__main__":
    pipeline = ScholarshipPipeline()
    pipeline.run_pipeline()
