"""
DataOS — Database Framework

Local SQLite database for your business data warehouse.
Creates the database, manages connections, and provides query helpers.

Each collector creates its own tables when first run — no need to
define the schema upfront. The database grows as you add collectors.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Database lives in data/ directory at workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE_ROOT / "data" / "data.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collection_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collected_at TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            reason TEXT,
            records_written INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def get_connection():
    if not DB_PATH.exists():
        return init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def log_collection(conn, source, status, records=0, reason=None):
    conn.execute(
        "INSERT INTO collection_log (collected_at, source, status, reason, records_written) "
        "VALUES (?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), source, status, reason, records)
    )
    conn.commit()


def query_one(conn, sql, params=None):
    try:
        row = conn.execute(sql, params or ()).fetchone()
        return dict(row) if row else None
    except Exception:
        return None


def query_all(conn, sql, params=None):
    try:
        rows = conn.execute(sql, params or ()).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []


def table_exists(conn, table_name):
    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    return result is not None


def get_latest_date(conn, table_name, date_column="date"):
    try:
        row = conn.execute(
            f"SELECT MAX({date_column}) as d FROM {table_name}"
        ).fetchone()
        return row["d"] if row else None
    except Exception:
        return None


def get_table_list(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' AND name != 'collection_log' "
        "ORDER BY name"
    ).fetchall()
    return [row["name"] for row in rows]


if __name__ == "__main__":
    conn = init_db()
    print(f"Database initialized at: {DB_PATH}")
    print(f"Size: {DB_PATH.stat().st_size / 1024:.1f} KB")
    tables = get_table_list(conn)
    print(f"Tables: {tables if tables else '(none yet — run a collector to create tables)'}")
    conn.close()
