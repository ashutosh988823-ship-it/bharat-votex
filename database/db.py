"""
Bharat Votex — Database Module
SQLite-based voter and vote storage
"""

import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "bharat_votex.db")

CANDIDATES = [
    {"id": "party_a", "name": "Priya Sharma", "party": "National Progress Party", "symbol": "🌟"},
    {"id": "party_b", "name": "Rajesh Kumar",  "party": "United India Front",       "symbol": "🌿"},
    {"id": "party_c", "name": "Anita Patel",   "party": "People's Democratic Union","symbol": "🔆"},
    {"id": "nota",    "name": "NOTA",           "party": "None of the Above",        "symbol": "✖"},
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist and seed demo data."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            voter_id    TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            has_voted   INTEGER DEFAULT 0,
            voted_at    TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate   TEXT NOT NULL,
            vote_hash   TEXT NOT NULL,
            cast_at     TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id      TEXT PRIMARY KEY,
            name    TEXT NOT NULL,
            party   TEXT NOT NULL,
            symbol  TEXT NOT NULL,
            votes   INTEGER DEFAULT 0
        )
    """)

    # Seed candidates
    for cand in CANDIDATES:
        c.execute("""
            INSERT OR IGNORE INTO candidates (id, name, party, symbol, votes)
            VALUES (?, ?, ?, ?, 0)
        """, (cand["id"], cand["name"], cand["party"], cand["symbol"]))

    # Demo voters (you can register real ones via admin panel)
    demo_voters = [
        ("VTR001", "Arjun Mehta"),
        ("VTR002", "Sunita Rao"),
        ("VTR003", "Vikram Singh"),
    ]
    for vid, vname in demo_voters:
        c.execute("INSERT OR IGNORE INTO voters (voter_id, name) VALUES (?, ?)", (vid, vname))

    conn.commit()
    conn.close()
    print("[DB] Database initialized.")


def get_voter(voter_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM voters WHERE voter_id = ?", (voter_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_voters():
    conn = get_connection()
    rows = conn.execute("SELECT voter_id, name, has_voted, voted_at FROM voters").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_voter(voter_id: str, name: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO voters (voter_id, name) VALUES (?, ?)", (voter_id, name))
    conn.commit()
    conn.close()


def mark_voted(voter_id: str):
    conn = get_connection()
    conn.execute(
        "UPDATE voters SET has_voted = 1, voted_at = ? WHERE voter_id = ?",
        (datetime.now().isoformat(), voter_id)
    )
    conn.commit()
    conn.close()


def cast_vote(candidate_id: str):
    """Store encrypted vote hash and increment counter."""
    vote_hash = hashlib.sha256(
        f"{candidate_id}-{datetime.now().isoformat()}".encode()
    ).hexdigest()

    conn = get_connection()
    conn.execute("INSERT INTO votes (candidate, vote_hash) VALUES (?, ?)", (candidate_id, vote_hash))
    conn.execute("UPDATE candidates SET votes = votes + 1 WHERE id = ?", (candidate_id,))
    conn.commit()
    conn.close()


def get_results():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM candidates ORDER BY votes DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
