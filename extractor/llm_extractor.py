import json
import logging
import os
import re
import requests
from typing import Dict, Optional, List
from extractor.prompt_templates import SYSTEM_PROMPT, EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

class LLMExtractor:
    def __init__(
        self,
        provider: str = "groq",
        model_name: str = "openai/gpt-oss-120b",
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.provider = (provider or "groq").lower()
        self.model_name = model_name or ("openai/gpt-oss-120b" if self.provider == "groq" else "qwen2.5:3b")
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "").strip()
        self.timeout = timeout

        if endpoint:
            self.endpoint = endpoint.rstrip("/")
        elif self.provider == "groq":
            self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        else:
            self.endpoint = "http://localhost:11434"

    def extract_scholarship_data(self, page_data: Dict) -> Dict:
        """
        Extracts structured scholarship JSON from scraped web page data.
        Tries configured LLM provider (Groq or Ollama) with fallback to regex extraction.
        """
        title = page_data.get("title", "")
        url = page_data.get("url", "")
        text = page_data.get("cleaned_text", "")
        links = page_data.get("links", [])

        llm_result = None

        if self.provider == "groq":
            if self.api_key:
                logger.info(f"Extracting with Groq LLM ({self.model_name}) for {url}...")
                llm_result = self._call_groq(title, url, text)
            else:
                logger.warning("Groq provider selected but GROQ_API_KEY is not set in .env. Falling back to regex.")
        elif self.provider == "ollama":
            logger.info(f"Extracting with local Ollama LLM ({self.model_name}) for {url}...")
            llm_result = self._call_ollama(title, url, text)

        if llm_result:
            return self._normalize_extracted_data(llm_result, title, url, links)

        logger.info(f"Using rule-based regex fallback extractor for {url}.")
        return self._regex_fallback_extractor(title, url, text, links)

    def _call_groq(self, title: str, url: str, text: str) -> Optional[Dict]:
        """Calls Groq Cloud API with OpenAI-compatible chat completion schema and JSON mode."""
        try:
            prompt = EXTRACTION_PROMPT.format(
                title=title,
                url=url,
                text_snapshot=text[:6000] # Safe snapshot for context
            )

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }

            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)

            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
            else:
                logger.warning(f"Groq API call failed with HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Exception during Groq API call: {e}")

        return None

    def _call_ollama(self, title: str, url: str, text: str) -> Optional[Dict]:
        """Calls local Ollama API for structured extraction."""
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

            resp = requests.post(f"{self.endpoint}/api/generate", json=payload, timeout=self.timeout)

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

    def _normalize_extracted_data(self, data: Dict, title: str, url: str, links: list) -> Dict:
        """Sanitizes and normalizes LLM output to guarantee expected schema."""
        quotes = data.get("quotes") or {}
        if not isinstance(quotes, dict):
            quotes = {}

        app_url = data.get("application_url")
        if not app_url:
            app_url = links[0] if links else url

        normalized = {
            "name": data.get("name") or title or "Scholarship Scheme",
            "provider": data.get("provider") or "Official Provider",
            "amount": data.get("amount"),
            "eligibility_academic": data.get("eligibility_academic"),
            "eligibility_income": data.get("eligibility_income"),
            "eligibility_other": data.get("eligibility_other") or "Indian Students",
            "deadline": data.get("deadline"),
            "application_url": app_url,
            "quotes": quotes,
            "evidence_quotes": quotes
        }
        return normalized

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

        quotes_dict = {
            "name": name_quote,
            "provider": provider_quote,
            "amount": amount_quote,
            "eligibility_academic": academic_quote,
            "eligibility_income": income_quote,
            "deadline": deadline_quote
        }

        return {
            "name": name,
            "provider": provider,
            "amount": amount,
            "eligibility_academic": academic,
            "eligibility_income": income,
            "eligibility_other": "Indian Students",
            "deadline": deadline,
            "application_url": app_url,
            "quotes": quotes_dict,
            "evidence_quotes": quotes_dict
        }
