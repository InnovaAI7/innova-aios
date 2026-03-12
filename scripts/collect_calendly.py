"""
DataOS — Calendly Collector

Tracks calls booked via Calendly for InnovaAI Integration.
Collects scheduled events from the last 90 days daily.

Tables created: calendly_bookings
"""

import os
import json
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_BASE = "https://api.calendly.com"


def calendly_get(path, token, params=None):
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "User-Agent": "DataOS/1.0"
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def collect():
    token = os.getenv("CALENDLY_TOKEN", "").strip()
    user_uri = os.getenv("CALENDLY_USER_URI", "").strip()

    if not token:
        return {"source": "calendly", "status": "skipped", "reason": "Missing CALENDLY_TOKEN"}

    try:
        # Fetch events from the last 90 days
        min_time = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
        max_time = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "user": user_uri,
            "min_start_time": min_time,
            "max_start_time": max_time,
            "count": 100,
            "status": "active",
        }

        data = calendly_get("/scheduled_events", token, params)
        events = data.get("collection", [])

        # Also fetch canceled events
        params["status"] = "canceled"
        canceled_data = calendly_get("/scheduled_events", token, params)
        canceled_events = canceled_data.get("collection", [])

        all_events = []
        for event in events:
            all_events.append({
                "uuid": event.get("uri", "").split("/")[-1],
                "name": event.get("name", ""),
                "status": "active",
                "event_date": event.get("start_time", "")[:10] if event.get("start_time") else None,
                "start_time": event.get("start_time"),
                "end_time": event.get("end_time"),
                "created_at": event.get("created_at"),
            })
        for event in canceled_events:
            all_events.append({
                "uuid": event.get("uri", "").split("/")[-1],
                "name": event.get("name", ""),
                "status": "canceled",
                "event_date": event.get("start_time", "")[:10] if event.get("start_time") else None,
                "start_time": event.get("start_time"),
                "end_time": event.get("end_time"),
                "created_at": event.get("created_at"),
            })

        return {
            "source": "calendly",
            "status": "success",
            "data": {"events": all_events}
        }

    except Exception as e:
        return {"source": "calendly", "status": "error", "reason": str(e)}


def write(conn, result, date):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calendly_bookings (
            uuid TEXT PRIMARY KEY,
            event_name TEXT,
            status TEXT,
            event_date TEXT,
            start_time TEXT,
            end_time TEXT,
            created_at TEXT,
            collected_at TEXT
        )
    """)

    if result.get("status") != "success":
        conn.commit()
        return 0

    events = result["data"]["events"]
    collected_at = datetime.now(timezone.utc).isoformat()
    records = 0

    for event in events:
        conn.execute(
            "INSERT OR REPLACE INTO calendly_bookings "
            "(uuid, event_name, status, event_date, start_time, end_time, created_at, collected_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event["uuid"], event["name"], event["status"],
                event["event_date"], event["start_time"], event["end_time"],
                event["created_at"], collected_at
            )
        )
        records += 1

    conn.commit()
    return records


if __name__ == "__main__":
    result = collect()
    if result["status"] == "success":
        events = result["data"]["events"]
        active = [e for e in events if e["status"] == "active"]
        canceled = [e for e in events if e["status"] == "canceled"]
        print(f"Calendly: {len(active)} active events, {len(canceled)} canceled (last 90 days)")
        # Show recent
        recent = sorted(active, key=lambda x: x["start_time"] or "", reverse=True)[:5]
        for e in recent:
            print(f"  {e['event_date']} — {e['name']}")
    else:
        print(f"Status: {result['status']} — {result.get('reason', '')}")
