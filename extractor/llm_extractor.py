import json
import logging
import re
import requests
from typing import Dict
from extractor.prompt_templates import SYSTEM_PROMPT, EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

class LLMExtractor:
    def __init__(self, model_name: str = "qwen2.5:3b", endpoint: str = "http://localhost:11434"):
        self.model_name = model_name
        self.endpoint = endpoint.rstrip("/")

    def extract_scholarship_data(self, page_data: Dict) -> Dict:
        """
        Extracts structured scholarship JSON from scraped web page data.
        Uses local Ollama LLM if available; falls back to regex extraction if unreachable.
        """
        title = page_data.get("title", "")
        url = page_data.get("url", "")
        text = page_data.get("cleaned_text", "")

        # Try local LLM extraction via Ollama API
        llm_result = self._call_ollama(title, url, text)
        if llm_result:
            return llm_result

        logger.info(f"Ollama LLM unreachable or failed. Falling back to rule-based regex extractor for {url}.")
        return self._regex_fallback_extractor(title, url, text, page_data.get("links", []))

    def _call_ollama(self, title: str, url: str, text: str) -> Optional[Dict]:
        try:
            prompt = EXTRACTION_PROMPT.format(
                title=title,
                url=url,
                text_snapshot=text[:4000] # Cap text length for local LLM context window
            )
            
            payload = {
                "model": self.model_name,
                "system": SYSTEM_PROMPT,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }

            resp = requests.post(f"{self.endpoint}/api/generate", json=payload, timeout=2.0)

            if resp.status_code == 200:
                response_json = resp.json()
                raw_response = response_json.get("response", "")
                
                # Extract JSON block if surrounded by markdown
                json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
        except Exception as e:
            logger.debug(f"Ollama call exception: {e}")
            
        return None

    def _regex_fallback_extractor(self, title: str, url: str, text: str, links: list) -> Dict:
        """Deterministic regex-based fallback extractor for reliable, grounded extraction."""
        # Scholarship Name
        name = title or "Scholarship Scheme"
        name_quote = title
        
        # Provider
        provider = "Official Provider"
        provider_quote = ""
        provider_match = re.search(r"(Ministry of [A-Za-z\s]+|Tata Trusts|UGC|Reliance Foundation|Government of [A-Za-z\s]+)", text, re.IGNORECASE)
        if provider_match:
            provider = provider_match.group(0).strip()
            provider_quote = provider_match.group(0)

        # Amount
        amount = None
        amount_quote = ""
        amount_match = re.search(r"(Rs\.?\s*[\d,]+|INR\s*[\d,]+|\$[\d,]+|\d+\s*rupees|Rs\.\s*[\d,]+\s*per\s*[a-z]+)", text, re.IGNORECASE)
        if amount_match:
            amount = amount_match.group(0).strip()
            amount_quote = amount_match.group(0)

        # Academic Eligibility
        academic = None
        academic_quote = ""
        academic_match = re.search(r"(Class\s*\d+|Graduation|Diploma|Minimum\s*\d+%\s*marks|\d+%\s*in\s*previous)", text, re.IGNORECASE)
        if academic_match:
            academic = academic_match.group(0).strip()
            academic_quote = academic_match.group(0)

        # Income Eligibility
        income = None
        income_quote = ""
        income_match = re.search(r"(income\s*(must\s*not\s*exceed|below|less\s*than|criteria|up\s*to)\s*(Rs\.?\s*[\d,]+|INR\s*[\d,]+|[\d,]+\s*per\s*annum))", text, re.IGNORECASE)
        if income_match:
            income = income_match.group(0).strip()
            income_quote = income_match.group(0)

        # Deadline
        deadline = None
        deadline_quote = ""
        deadline_match = re.search(r"(Deadline|Closing Date|Last Date|Valid Up to|Apply before)\s*:?\s*([\d]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+[\d]{4}|[\d]{4}-[\d]{2}-[\d]{2}|[\d]{2}/[\d]{2}/[\d]{4})", text, re.IGNORECASE)
        if deadline_match:
            deadline = deadline_match.group(2).strip()
            deadline_quote = deadline_match.group(0)

        # Application URL
        app_url = links[0] if links else url

        return {
            "name": name,
            "provider": provider,
            "amount": amount,
            "eligibility_academic": academic,
            "eligibility_income": income,
            "eligibility_other": "Indian Students",
            "deadline": deadline,
            "application_url": app_url,
            "quotes": {
                "name": name_quote,
                "provider": provider_quote,
                "amount": amount_quote,
                "eligibility_academic": academic_quote,
                "eligibility_income": income_quote,
                "deadline": deadline_quote
            }
        }
