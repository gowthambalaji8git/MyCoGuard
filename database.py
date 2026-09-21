"""SQLite persistence layer: users + saved analysis reports."""
import os
import sqlite3
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "instance", "mycoguard.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            security_question TEXT NOT NULL,
            security_answer_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            mushroom_name TEXT NOT NULL,
            scientific_name TEXT,
            category TEXT NOT NULL,
            category_label TEXT NOT NULL,
            confidence REAL NOT NULL,
            image_path TEXT NOT NULL,
            pdf_path TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


# ---------- users ----------

def create_user(username, email, password_hash, security_question, security_answer_hash):
    conn = get_db()
    conn.execute(
        "INSERT INTO users (username, email, password_hash, security_question, "
        "security_answer_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (username, email, password_hash, security_question, security_answer_hash,
         datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_user_by_username(username):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row


def get_user_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def update_password(user_id, new_password_hash):
    conn = get_db()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
    conn.commit()
    conn.close()


# ---------- reports ----------

def save_report(user_id, mushroom_name, scientific_name, category, category_label,
                 confidence, image_path, pdf_path):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO reports (user_id, mushroom_name, scientific_name, category, "
        "category_label, confidence, image_path, pdf_path, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, mushroom_name, scientific_name, category, category_label,
         confidence, image_path, pdf_path, datetime.utcnow().isoformat()),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def get_report(report_id, user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM reports WHERE id = ? AND user_id = ?", (report_id, user_id)
    ).fetchone()
    conn.close()
    return row


def list_reports(user_id, limit=50):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return rows
