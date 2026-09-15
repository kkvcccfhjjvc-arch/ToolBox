import sqlite3
from config import DB_PATH, DATA_DIR
import os

os.makedirs(DATA_DIR, exist_ok=True)

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_banned INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tool_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tool TEXT,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()

def register_user(user):
    conn = connect()

    conn.execute("""
        INSERT INTO users(user_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_seen=CURRENT_TIMESTAMP
    """, (
        user.id,
        user.username,
        user.first_name
    ))

    conn.commit()
    conn.close()

def log_tool(user_id, tool):
    conn = connect()
    conn.execute(
        "INSERT INTO tool_usage(user_id, tool) VALUES (?, ?)",
        (user_id, tool)
    )
    conn.commit()
    conn.close()

def stats():
    conn = connect()

    users = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    usages = conn.execute(
        "SELECT COUNT(*) FROM tool_usage"
    ).fetchone()[0]

    conn.close()

    return users, usages
