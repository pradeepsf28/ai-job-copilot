import sqlite3
from datetime import datetime

DB_NAME = "jobs.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            salary TEXT,
            description TEXT,
            apply_url TEXT UNIQUE,
            source TEXT,
            match_score INTEGER,
            match_label TEXT,
            status TEXT DEFAULT 'Bookmarked',
            date_found TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_job(job):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO saved_jobs
        (title, company, location, salary, description, apply_url, source, match_score, match_label, status, date_found)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("salary", ""),
        job.get("description", ""),
        job.get("apply_url", ""),
        job.get("source", ""),
        job.get("match_score", 0),
        job.get("match_label", ""),
        job.get("status", "Bookmarked"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def get_saved_jobs():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT title, company, location, match_score, match_label, status, apply_url, date_found FROM saved_jobs ORDER BY date_found DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def job_exists(apply_url):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM saved_jobs WHERE apply_url = ?", (apply_url,))
    result = c.fetchone()
    conn.close()
    return result is not None
