import os
import yaml
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
ENV_PATH = BASE_DIR / ".env"

def load_env_file(env_path: Path = ENV_PATH) -> None:
    """Loads environment variables from .env file into os.environ."""
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        # Fallback manual parser if python-dotenv is not yet installed
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass

# Load .env automatically upon importing settings
load_env_file()

def get_groq_api_key() -> str:
    """
    Reads GROQ_API_KEY using a priority chain:
      1. Streamlit secrets (st.secrets) — used when deployed on Streamlit Cloud
      2. Environment variable GROQ_API_KEY — used locally via .env or system env
    Returns an empty string if not found anywhere.
    """
    # 1. Try Streamlit secrets first (available on Streamlit Cloud)
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        # Streamlit not running or secrets not configured — silently skip
        pass

    # 2. Fall back to environment variable (loaded from .env locally)
    return os.environ.get("GROQ_API_KEY", "").strip()

def load_config(config_path: Path = CONFIG_PATH) -> dict:
    """Loads configuration settings from YAML file with sensible fallbacks and env injection."""
    if not config_path.exists():
        config = get_default_config()
    else:
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = yaml.safe_load(f) or get_default_config()
            except Exception as e:
                print(f"[Warning] Failed to parse config YAML: {e}. Using defaults.")
                config = get_default_config()

    # Inject GROQ_API_KEY — checks Streamlit secrets first, then .env / os.environ
    llm_conf = config.setdefault("llm", {})
    if not llm_conf.get("api_key"):
        llm_conf["api_key"] = get_groq_api_key()

    return config

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
            "provider": "groq",
            "model_name": "llama-3.3-70b-versatile",
            "groq_endpoint": "https://api.groq.com/openai/v1/chat/completions",
            "ollama_endpoint": "http://localhost:11434",
            "api_key": get_groq_api_key(),
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
