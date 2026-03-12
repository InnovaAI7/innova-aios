"""
DataOS — Trello Collector

Tracks InnovaAI's client pipeline by stage.
Captures card counts per list and total cards per stage group daily.

Board: Client Tracking (usFYGkVi)
Tables created: trello_pipeline, trello_cards
"""

import os
import json
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_BASE = "https://api.trello.com/1"

# Pipeline stage order for display
PIPELINE_LISTS = [
    "Business Opportunities",
    "Discovery",
    "Inital SOW",
    "Deep Audit / SOW",
    "Agreement",
    "Build + Feedback",
    "Final Build",
    "Testing",
    "Training",
    "Launch",
    "Marketing / Testimonials",
    "Complete",
    "Project Cancelled / On Pause",
]


def trello_get(path, key, token, params=""):
    url = f"{API_BASE}{path}?key={key}&token={token}{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "DataOS/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def collect():
    key = os.getenv("TRELLO_API_KEY", "").strip()
    token = os.getenv("TRELLO_TOKEN", "").strip()
    board_id = os.getenv("TRELLO_BOARD_ID", "").strip()

    if not key or not token or not board_id:
        return {
            "source": "trello",
            "status": "skipped",
            "reason": "Missing TRELLO_API_KEY, TRELLO_TOKEN, or TRELLO_BOARD_ID"
        }

    try:
        # Fetch all lists
        lists = trello_get(f"/boards/{board_id}/lists", key, token, "&fields=name,pos")

        # Fetch all open cards
        cards = trello_get(f"/boards/{board_id}/cards", key, token, "&filter=open&fields=idList,name,due,dateLastActivity")

        # Map list id -> name
        list_map = {l["id"]: l["name"] for l in lists}

        # Count cards per list
        card_counts = {}
        card_details = []
        for card in cards:
            list_name = list_map.get(card["idList"], "Unknown")
            card_counts[list_name] = card_counts.get(list_name, 0) + 1
            card_details.append({
                "list_name": list_name,
                "card_name": card.get("name", ""),
                "due": card.get("due"),
                "last_activity": card.get("dateLastActivity"),
            })

        return {
            "source": "trello",
            "status": "success",
            "data": {
                "card_counts": card_counts,
                "card_details": card_details,
                "lists": [l["name"] for l in lists],
            }
        }
    except Exception as e:
        return {"source": "trello", "status": "error", "reason": str(e)}


def write(conn, result, date):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trello_pipeline (
            date TEXT NOT NULL,
            list_name TEXT NOT NULL,
            list_order INTEGER DEFAULT 0,
            card_count INTEGER DEFAULT 0,
            collected_at TEXT,
            PRIMARY KEY (date, list_name)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trello_cards (
            date TEXT NOT NULL,
            list_name TEXT NOT NULL,
            card_name TEXT,
            due TEXT,
            last_activity TEXT,
            collected_at TEXT
        )
    """)

    if result.get("status") != "success":
        conn.commit()
        return 0

    data = result["data"]
    card_counts = data["card_counts"]
    card_details = data["card_details"]
    collected_at = datetime.now(timezone.utc).isoformat()
    records = 0

    # Write pipeline stage counts
    for order, list_name in enumerate(PIPELINE_LISTS):
        count = card_counts.get(list_name, 0)
        conn.execute(
            "INSERT OR REPLACE INTO trello_pipeline "
            "(date, list_name, list_order, card_count, collected_at) VALUES (?, ?, ?, ?, ?)",
            (date, list_name, order, count, collected_at)
        )
        records += 1

    # Write individual card snapshot
    conn.execute("DELETE FROM trello_cards WHERE date = ?", (date,))
    for card in card_details:
        if card["list_name"] in PIPELINE_LISTS:
            conn.execute(
                "INSERT INTO trello_cards (date, list_name, card_name, due, last_activity, collected_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (date, card["list_name"], card["card_name"], card["due"], card["last_activity"], collected_at)
            )

    conn.commit()
    return records


if __name__ == "__main__":
    result = collect()
    if result["status"] == "success":
        print("Trello pipeline snapshot:")
        for stage in PIPELINE_LISTS:
            count = result["data"]["card_counts"].get(stage, 0)
            if count > 0:
                print(f"  {stage}: {count} card(s)")
    else:
        print(f"Status: {result['status']} — {result.get('reason', '')}")
