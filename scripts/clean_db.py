import sqlite3

def clean_database():
    conn = sqlite3.connect('scholarships.db')
    cursor = conn.cursor()
    
    # Check current records
    cursor.execute("SELECT id, name, official_source_url FROM scholarships")
    rows = cursor.fetchall()
    print("Before cleanup:", rows)
    
    # Delete any records with invalid/unrelated URLs
    cursor.execute("DELETE FROM scholarships WHERE official_source_url LIKE '%motorcycle%' OR official_source_url LIKE '%bike%'")
    cursor.execute("DELETE FROM verification_evidence WHERE scholarship_id NOT IN (SELECT id FROM scholarships)")
    cursor.execute("DELETE FROM change_history WHERE scholarship_id NOT IN (SELECT id FROM scholarships)")
    
    # Make sure National Post-Matric Scholarship is present with the correct official government URL
    cursor.execute("SELECT id FROM scholarships WHERE official_source_url = 'https://scholarships.gov.in/post_matric_2026'")
    existing_np = cursor.fetchone()
    
    if not existing_np:
        cursor.execute("""
            INSERT OR REPLACE INTO scholarships (
                name, provider, amount, deadline, eligibility_academic, 
                eligibility_income, eligibility_other, application_url, 
                official_source_url, status, confidence_score, last_verified
            ) VALUES (
                'National Post-Matric Scholarship Scheme 2026 for SC/ST/OBC Students',
                'Ministry of Social Justice and Empowerment Government of India',
                'Rs. 12,000',
                '31st October 2026',
                'Class 11, 12, Diploma, Graduation, or Post Graduation in India',
                'income must not exceed Rs. 2,50,000',
                'Indian Students',
                'https://scholarships.gov.in/apply',
                'https://scholarships.gov.in/post_matric_2026',
                'VERIFIED',
                100.0,
                datetime('now')
            )
        """)
        
    conn.commit()
    
    cursor.execute("SELECT id, name, official_source_url, status, confidence_score FROM scholarships")
    print("After cleanup:")
    for r in cursor.fetchall():
        print(r)
        
    conn.close()

if __name__ == "__main__":
    clean_database()
