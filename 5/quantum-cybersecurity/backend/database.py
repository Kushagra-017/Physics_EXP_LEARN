"""SQLite persistence for the educational simulation history."""
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = os.environ.get("DATABASE_PATH", "/tmp/quantum-cybersecurity.sqlite3" if os.environ.get("VERCEL") else str(ROOT / "simulations.sqlite3"))


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))


def save_simulation(number, factors, algorithm, details):
    init_db()
    with connect() as conn:
        cursor = conn.execute("INSERT INTO simulations (input_number, factors, algorithm, details) VALUES (?, ?, ?, ?)",
                              (number, json.dumps(factors), algorithm, json.dumps(details)))
        return cursor.lastrowid


def get_history(limit=20):
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM simulations ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{**dict(row), "factors": json.loads(row["factors"]), "details": json.loads(row["details"])} for row in rows]
