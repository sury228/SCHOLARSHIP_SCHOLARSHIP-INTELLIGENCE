import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from database.models import init_db

class DBManager:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        init_db(self.db_path)

    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def upsert_scholarship(self, scholarship_data: Dict) -> Tuple[int, List[Dict]]:
        """
        Inserts a new scholarship or updates an existing record.
        Detects changes in fields and records them in change_history.
        Returns tuple of (scholarship_id, list_of_detected_changes).
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now_str = datetime.utcnow().isoformat()
        url = scholarship_data.get("official_source_url")
        
        cursor.execute("SELECT * FROM scholarships WHERE official_source_url = ?", (url,))
        existing = cursor.fetchone()

        detected_changes = []

        if existing:
            scholarship_id = existing["id"]
            # Fields to monitor for historical changes
            tracked_fields = ["name", "provider", "amount", "deadline", "eligibility_income", "eligibility_academic", "application_url", "status"]
            
            for field in tracked_fields:
                old_val = existing[field]
                new_val = scholarship_data.get(field)
                
                # Check for meaningful change
                if new_val is not None and str(old_val).strip() != str(new_val).strip():
                    detected_changes.append({
                        "scholarship_id": scholarship_id,
                        "field_name": field,
                        "old_value": str(old_val),
                        "new_value": str(new_val),
                        "change_detected_date": now_str,
                        "source_url": url,
                        "evidence": scholarship_data.get("evidence_quotes", {}).get(field, "")
                    })
            
            # Update scholarship record
            cursor.execute("""
                UPDATE scholarships SET
                    name = ?,
                    provider = ?,
                    amount = ?,
                    eligibility_academic = ?,
                    eligibility_income = ?,
                    eligibility_other = ?,
                    deadline = ?,
                    application_url = ?,
                    source_type = ?,
                    status = ?,
                    confidence_score = ?,
                    last_verified = ?,
                    raw_text_snapshot = ?
                WHERE id = ?
            """, (
                scholarship_data.get("name"),
                scholarship_data.get("provider"),
                scholarship_data.get("amount"),
                scholarship_data.get("eligibility_academic"),
                scholarship_data.get("eligibility_income"),
                scholarship_data.get("eligibility_other"),
                scholarship_data.get("deadline"),
                scholarship_data.get("application_url"),
                scholarship_data.get("source_type"),
                scholarship_data.get("status"),
                scholarship_data.get("confidence_score", 0.0),
                now_str,
                scholarship_data.get("raw_text_snapshot", ""),
                scholarship_id
            ))
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO scholarships (
                    name, provider, amount, eligibility_academic, eligibility_income,
                    eligibility_other, deadline, official_source_url, application_url,
                    source_type, status, confidence_score, last_verified, raw_text_snapshot
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scholarship_data.get("name"),
                scholarship_data.get("provider"),
                scholarship_data.get("amount"),
                scholarship_data.get("eligibility_academic"),
                scholarship_data.get("eligibility_income"),
                scholarship_data.get("eligibility_other"),
                scholarship_data.get("deadline"),
                url,
                scholarship_data.get("application_url"),
                scholarship_data.get("source_type"),
                scholarship_data.get("status"),
                scholarship_data.get("confidence_score", 0.0),
                now_str,
                scholarship_data.get("raw_text_snapshot", "")
            ))
            scholarship_id = cursor.lastrowid

        # Record changes in change_history table
        for change in detected_changes:
            cursor.execute("""
                INSERT INTO change_history (
                    scholarship_id, field_name, old_value, new_value,
                    change_detected_date, source_url, evidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                change["scholarship_id"],
                change["field_name"],
                change["old_value"],
                change["new_value"],
                change["change_detected_date"],
                change["source_url"],
                change["evidence"]
            ))

        conn.commit()
        conn.close()
        return scholarship_id, detected_changes

    def add_verification_evidence(self, scholarship_id: int, evidence_records: List[Dict]):
        """Records quotes and substring verification status into database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Clear existing evidence for this scholarship before re-verifying
        cursor.execute("DELETE FROM verification_evidence WHERE scholarship_id = ?", (scholarship_id,))
        
        for rec in evidence_records:
            cursor.execute("""
                INSERT INTO verification_evidence (
                    scholarship_id, field_name, extracted_value, source_quote, is_verified_substring
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                scholarship_id,
                rec.get("field_name"),
                rec.get("extracted_value"),
                rec.get("source_quote"),
                1 if rec.get("is_verified_substring") else 0
            ))
            
        conn.commit()
        conn.close()

    def get_all_scholarships(self) -> List[Dict]:
        """Returns all scholarship records."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scholarships ORDER BY confidence_score DESC, id DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_scholarship_by_id(self, scholarship_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scholarships WHERE id = ?", (scholarship_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_change_history(self, scholarship_id: Optional[int] = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        if scholarship_id:
            cursor.execute("SELECT * FROM change_history WHERE scholarship_id = ? ORDER BY change_detected_date DESC", (scholarship_id,))
        else:
            cursor.execute("SELECT * FROM change_history ORDER BY change_detected_date DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_evidence_for_scholarship(self, scholarship_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM verification_evidence WHERE scholarship_id = ?", (scholarship_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
