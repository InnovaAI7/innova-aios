"""
IntelOS — Database setup and helper functions.

Creates and manages the SQLite database for meeting transcripts,
Slack messages, team registry, and collection logs.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

# Points to the existing DataOS database so all data stays in one place
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = WORKSPACE_ROOT / "data" / "data.db"


SCHEMA_SQL = """
-- Meeting transcripts from any recorder (Fireflies, Fathom, custom)
CREATE TABLE IF NOT EXISTS meetings (
    meeting_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT,
    date TEXT NOT NULL,
    start_time TEXT,
    duration_minutes INTEGER,
    participants TEXT,
    transcript_text TEXT,
    summary TEXT,
    action_items_raw TEXT,
    stream TEXT,
    call_type TEXT,
    classified_at TEXT,
    external_url TEXT,
    collected_at TEXT NOT NULL
);

-- Team member registry (for meeting classification)
CREATE TABLE IF NOT EXISTS staff_registry (
    email TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    team TEXT NOT NULL,
    department TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    added_at TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    """Get a database connection. Creates the file and tables if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> sqlite3.Connection:
    """Initialize the database with all IntelOS tables."""
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_meetings(conn: sqlite3.Connection, meetings: list) -> int:
    """Write meeting records to database. Returns count written."""
    records = 0
    now = _now_iso()
    for m in meetings:
        mid = m.get("meeting_id")
        if not mid:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO meetings "
            "(meeting_id, source, title, date, start_time, duration_minutes, "
            "participants, transcript_text, summary, action_items_raw, "
            "stream, call_type, classified_at, external_url, collected_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)",
            (mid, m.get("source", "unknown"), m.get("title"),
             m.get("date"), m.get("start_time"), m.get("duration_minutes"),
             m.get("participants"), m.get("transcript_text"),
             m.get("summary"), m.get("action_items_raw"),
             m.get("external_url"), now)
        )
        records += 1
    conn.commit()
    return records


def search_meetings(conn: sqlite3.Connection, query: str, days: int = 30) -> list:
    """Search meeting transcripts and titles for a keyword/phrase."""
    rows = conn.execute(
        "SELECT meeting_id, title, date, duration_minutes, participants, "
        "summary, transcript_text FROM meetings "
        "WHERE date >= date('now', ?) "
        "AND (title LIKE ? OR transcript_text LIKE ? OR summary LIKE ?) "
        "ORDER BY date DESC",
        (f"-{days} days", f"%{query}%", f"%{query}%", f"%{query}%")
    ).fetchall()
    return [dict(r) for r in rows]


def get_meeting_stats(conn: sqlite3.Connection) -> dict:
    """Get a quick summary of what's in the database."""
    try:
        meetings = conn.execute("SELECT COUNT(*) FROM meetings").fetchone()[0]
        latest = conn.execute("SELECT date FROM meetings ORDER BY date DESC LIMIT 1").fetchone()
        return {
            "total_meetings": meetings,
            "latest_meeting_date": latest[0] if latest else None,
        }
    except Exception:
        return {"total_meetings": 0, "latest_meeting_date": None}


if __name__ == "__main__":
    conn = init_db()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row["name"] for row in cursor.fetchall()]
    print(f"Database: {DB_PATH}")
    print(f"Tables: {', '.join(tables)}")
    stats = get_meeting_stats(conn)
    print(f"Meetings: {stats['total_meetings']} | Latest: {stats['latest_meeting_date'] or 'none yet'}")
    conn.close()
