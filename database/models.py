import sqlite3
from pathlib import Path

def init_db(db_path: Path):
    """Initializes the SQLite database with required tables if they don't exist."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Table 1: scholarships
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scholarships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        provider TEXT NOT NULL,
        amount TEXT,
        eligibility_academic TEXT,
        eligibility_income TEXT,
        eligibility_other TEXT,
        deadline TEXT,
        official_source_url TEXT UNIQUE NOT NULL,
        application_url TEXT,
        source_type TEXT,
        status TEXT,
        confidence_score REAL,
        last_verified TEXT,
        raw_text_snapshot TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table 2: change_history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS change_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scholarship_id INTEGER,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        change_detected_date TEXT,
        source_url TEXT,
        evidence TEXT,
        FOREIGN KEY (scholarship_id) REFERENCES scholarships (id) ON DELETE CASCADE
    );
    """)

    # Table 3: verification_evidence
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verification_evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scholarship_id INTEGER,
        field_name TEXT,
        extracted_value TEXT,
        source_quote TEXT,
        is_verified_substring INTEGER,
        FOREIGN KEY (scholarship_id) REFERENCES scholarships (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
