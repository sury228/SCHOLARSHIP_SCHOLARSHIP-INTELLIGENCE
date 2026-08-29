import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, user_agent: str = None, timeout: int = 5):
        self.headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.timeout = timeout


    def fetch_page(self, url: str) -> Dict:
        """
        Fetches web page content, cleans text, extracts title and application links.
        Returns dictionary containing HTML, cleaned text, status_code, and links.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            status_code = response.status_code
            
            if status_code != 200:
                return {
                    "url": url,
                    "status_code": status_code,
                    "is_success": False,
                    "raw_html": "",
                    "cleaned_text": "",
                    "title": "",
                    "links": []
                }

            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove scripts, styles, nav, footer for clean extraction
            for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                element.decompose()

            # Clean text
            text = soup.get_text(separator=" ")
            cleaned_text = re.sub(r"\s+", " ", text).strip()
            
            title = soup.title.string.strip() if soup.title and soup.title.string else ""

            # Extract external application/registration links
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "apply" in href.lower() or "register" in href.lower() or "portal" in href.lower():
                    links.append(href)

            return {
                "url": url,
                "status_code": status_code,
                "is_success": True,
                "raw_html": html_content,
                "cleaned_text": cleaned_text,
                "title": title,
                "links": links
            }

        except Exception as e:
            logger.warning(f"Error fetching URL {url}: {e}")
            return {
                "url": url,
                "status_code": 0,
                "is_success": False,
                "raw_html": "",
                "cleaned_text": "",
                "title": "",
                "links": [],
                "error": str(e)
            }

    @staticmethod
    def get_mock_scholarship_pages() -> Dict[str, Dict]:
        """Provides realistic mock HTML content for testing and demo offline pipeline runs."""
        return {
            "https://scholarships.gov.in/post_matric_2026": {
                "url": "https://scholarships.gov.in/post_matric_2026",
                "status_code": 200,
                "is_success": True,
                "title": "National Post-Matric Scholarship Scheme 2026 for SC/ST/OBC Students",
                "cleaned_text": (
                    "Official Portal National Post-Matric Scholarship Scheme 2026 for SC/ST/OBC Students. "
                    "Provided by Ministry of Social Justice and Empowerment Government of India. "
                    "Financial assistance amount is Rs. 12,000 per annum for tuition fees and maintenance. "
                    "Eligibility Criteria: Student must be studying in Class 11, 12, Diploma, Graduation, or Post Graduation in India. "
                    "Annual family income must not exceed Rs. 2,50,000 per annum from all sources. "
                    "Application Deadline: 31st October 2026. "
                    "Apply online through NSP portal at https://scholarships.gov.in/apply."
                ),
                "links": ["https://scholarships.gov.in/apply"]
            },
            "https://www.tatatrusts.org/education-grant-2026": {
                "url": "https://www.tatatrusts.org/education-grant-2026",
                "status_code": 200,
                "is_success": True,
                "title": "Tata Trusts Higher Education Grant 2026",
                "cleaned_text": (
                    "Tata Trusts Higher Education Grant 2026. Provider: Tata Trusts Foundation. "
                    "Grant support up to Rs. 60,000 for undergraduate and postgraduate students in India. "
                    "Academic eligibility: Minimum 60% marks in previous qualifying examination. "
                    "Income criteria: Family income below Rs. 4,00,000 per year. "
                    "Application Deadline: 15th November 2026. "
                    "Registration link: https://www.tatatrusts.org/grants/apply-now"
                ),
                "links": ["https://www.tatatrusts.org/grants/apply-now"]
            }
        }
