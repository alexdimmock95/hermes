# src/learning/storage.py

'''
word_events
----------------------------------------
id         INTEGER (PK)
user_id    INTEGER
word       TEXT
source     TEXT
timestamp  TEXT (ISO8601)
'''

import sqlite3
from pathlib import Path

DB_PATH = Path("data/learning_events.db")


def get_connection():
    """
    Create (or reuse) a SQLite connection.
    """
    # Ensure parent directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(str(DB_PATH))
    return conn

def initialise_db():
    """
    Create tables if they don't exist.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS word_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            source TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def store_word_event(event: dict):
    """
    Persist a word event to SQLite.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO word_events (user_id, word, source, timestamp)
        VALUES (?, ?, ?, ?)
    """, (
        event["user_id"],
        event["word"],
        event["source"],
        event["timestamp"]
    ))

    conn.commit()
    conn.close()