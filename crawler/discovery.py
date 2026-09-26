import logging
from typing import List
from urllib.parse import urlparse
from crawler.source_classifier import classify_source_domain

logger = logging.getLogger(__name__)

class ScholarshipDiscovery:
    def __init__(self, seed_urls: List[str] = None, keywords: List[str] = None):
        self.seed_urls = seed_urls or [
            "https://scholarships.gov.in/post_matric_2026",
            "https://www.tatatrusts.org/education-grant-2026",
            "https://scholarships.gov.in/",
            "https://www.ugc.gov.in/"
        ]

        self.keywords = keywords or [
            "Indian student scholarship 2026 apply online",
            "government scholarship engineering medical India"
        ]

    def discover_urls(self, max_results: int = 10) -> List[str]:
        """Combines seed URLs and dynamic search results to return target scholarship URLs."""
        discovered = list(self.seed_urls)
        
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                for kw in self.keywords:
                    try:
                        results = list(ddgs.text(kw, max_results=3))
                        for r in results:
                            href = r.get("href")
                            if href and href not in discovered:
                                discovered.append(href)
                    except Exception as err:
                        logger.warning(f"DuckDuckGo search error for '{kw}': {err}")
        except Exception as e:
            logger.info(f"DuckDuckGo search not available or limited ({e}). Using seed URLs.")

        # Filter out invalid URLs
        valid_urls = [u for u in discovered if self._is_valid_url(u)]
        return valid_urls[:max_results]

    def _is_valid_url(self, url: str) -> bool:
        if not url or not url.startswith("http"):
            return False
        parsed = urlparse(url)
        if not parsed.netloc:
            return False
            
        domain = parsed.netloc.lower()
        full_url = url.lower()
        
        # Block obvious non-scholarship domains
        blocked_keywords = [
            "motorcycle", "bike", "automobile", "cars", "casino", "poker",
            "clothing", "shoes", "flights", "hotel", "travel", "amazon", "flipkart",
            "aliexpress", "ebay", "walmart", "fashion"
        ]
        if any(kw in domain or kw in parsed.path.lower() for kw in blocked_keywords):
            return False
            
        # Prioritize relevant domains/paths
        relevant_indicators = [
            "scholarship", "grant", "fellowship", "education", "student",
            ".gov.in", ".nic.in", ".ac.in", ".edu.in", ".edu", ".org", "trust", "foundation", "ugc"
        ]
        return any(ind in full_url for ind in relevant_indicators)
