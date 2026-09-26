# Scholarship Intelligence Crawler

An automated crawler and verification engine built for Indian students to discover, extract, verify, and monitor scholarship opportunities. It checks scraped information against raw webpage text to prevent AI hallucinations, logs historical updates (like deadline extensions or amount changes), and provides an interactive Streamlit dashboard for browsing verified listings.

---

## Key Features

1. **Anti-Hallucination Evidence Verification**
   * Every extracted attribute (deadline, award amount, academic criteria, income limits) is programmatically matched against exact quotes from the raw webpage text.
   * If a quote cannot be verified in the source text, the evidence fails, the confidence score drops, and the record is flagged for review.

2. **Deterministic Verification Scoring**
   * Evaluates listings using a transparent 100-point scoring model:
     * **Official Source Domain** (25 pts): Belongs to `.gov.in`, `.edu.in`, or recognized official CSR foundation.
     * **Active Live Webpage** (20 pts): Webpage returns HTTP 200 OK.
     * **Critical Fields Extracted** (15 pts): Key details like name, provider, amount, and deadline are present.
     * **Evidence Traceability** (20 pts): Ratio of quotes successfully verified in raw text.
     * **Valid Application Link** (10 pts): Direct application/registration URL available.
     * **Timeline Validity** (10 pts): Deadline is in the future.
   * Listings with scores **95% or higher** are marked as `VERIFIED`. Listings below 95% are marked as `REVIEW REQUIRED`.

3. **Change Tracking & Expiry Alerts**
   * Automatically compares re-crawled listings against database records.
   * Logs modifications (such as extended deadlines or updated amounts) into an audit history table.
   * Categorizes listing statuses into `ACTIVE`, `EXPIRING SOON` (within 7 days), `EXPIRED`, or `NO LONGER VERIFIABLE`.

4. **High-Speed LLM Extraction via Groq (with Ollama & Regex Fallback)**
   * Uses **Groq API** (`llama-3.3-70b-versatile`) with native JSON mode for blazing fast, highly accurate extraction.
   * Seamlessly falls back to local Ollama or deterministic regex parsing if no API key is provided or when offline.

---

## Project Architecture

```
scholarship_crawler/
├── .env                     # Private environment variables (GROQ_API_KEY)
├── .env.example             # Template for environment configuration
├── config/
│   ├── config.yaml          # Seed URLs, search keywords, LLM provider & scoring weights
│   └── settings.py          # Configuration loader & .env reader
├── database/
│   ├── db_manager.py        # SQLite / SQLAlchemy database manager
│   └── models.py            # Database tables schema
├── crawler/
│   ├── discovery.py         # Seed URL & web search discovery
│   ├── scraper.py           # Web fetcher, HTML cleaner, and text extractor
│   └── source_classifier.py # Domain category classifier (.gov.in, .ac.in, CSR)
├── extractor/
│   ├── prompt_templates.py  # Strict extraction prompts
│   └── llm_extractor.py     # Groq API + Ollama + regex fallback extractor
├── verifier/
│   ├── evidence_tracer.py   # Substring evidence verification
│   └── verification_engine.py # Deterministic confidence scoring
├── dashboard/
│   ├── app.py               # Streamlit web dashboard UI
│   └── components.py        # Reusable UI badges, evidence cards, and timeline
├── pipeline.py              # Main orchestrator script
├── requirements.txt         # Dependencies
└── README.md                # Documentation
```

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Your Groq API Key
Add your Groq API key to the [`.env`](.env) file:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```
*(You can get a free Groq API key at [console.groq.com/keys](https://console.groq.com/keys). If left empty, the pipeline will automatically fall back to the built-in rule-based extractor.)*

### 3. Run the Crawler Pipeline
To crawl seed sites, extract scholarship records, verify evidence, and save results to SQLite:
```bash
python pipeline.py
```

### 4. Launch the Dashboard
To start the Streamlit web app in your browser:
```bash
streamlit run dashboard/app.py
```

---

## Database Tables

* **`scholarships`**: Primary table containing verified scholarship opportunities, confidence scores, and current status.
* **`change_history`**: Audit trail logging field modifications over time (`old_value`, `new_value`, change date, evidence).
* **`verification_evidence`**: Quote verification records linking extracted fields to exact webpage text.
