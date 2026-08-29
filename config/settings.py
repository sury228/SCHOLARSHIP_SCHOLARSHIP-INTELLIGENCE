import os
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

def load_config(config_path: Path = CONFIG_PATH) -> dict:
    """Loads configuration settings from YAML file with sensible fallbacks."""
    if not config_path.exists():
        return get_default_config()
    
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = yaml.safe_load(f)
            return config or get_default_config()
        except Exception as e:
            print(f"[Warning] Failed to parse config YAML: {e}. Using defaults.")
            return get_default_config()

def get_default_config() -> dict:
    return {
        "crawler": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "timeout_seconds": 15,
            "max_search_results": 10,
            "seed_urls": [
                "https://scholarships.gov.in/",
                "https://www.ugc.gov.in/"
            ]
        },
        "search_keywords": [
            "Indian student scholarship apply online"
        ],
        "llm": {
            "model_name": "qwen2.5:3b",
            "ollama_endpoint": "http://localhost:11434",
            "temperature": 0.1,
            "timeout": 30
        },
        "scoring_weights": {
            "official_source_domain": 25,
            "active_live_page": 20,
            "critical_fields_present": 15,
            "evidence_traceability": 20,
            "valid_application_link": 10,
            "timeline_validity": 10
        },
        "status_thresholds": {
            "verified_min_score": 95.0,
            "expiring_soon_days": 7
        },
        "database": {
            "db_path": str(BASE_DIR / "scholarships.db")
        }
    }
