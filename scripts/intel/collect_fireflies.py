"""
IntelOS — Fireflies Collector

Pulls meeting transcripts from Fireflies.ai into the database.

Status: PENDING SETUP
To activate: add FIREFLIES_API_KEY to your .env file.
Get your key at: https://app.fireflies.ai/integrations → API & Webhooks

Tables used: meetings
"""

import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

FIREFLIES_API_URL = "https://api.fireflies.ai/graphql"


def collect(days: int = 7) -> list:
    """Collect meetings from the last N days. Returns list of meeting dicts."""
    api_key = os.getenv("FIREFLIES_API_KEY", "").strip()

    if not api_key:
        print("SKIPPED: FIREFLIES_API_KEY not set in .env")
        print("Get your key at: https://app.fireflies.ai/integrations")
        return []

    try:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

        query = """
        {
          transcripts(limit: 50) {
            id
            title
            date
            duration
            participants
            summary { overview action_items }
            sentences { text speaker_name }
            fireflies_users { email name }
          }
        }
        """

        payload = json.dumps({"query": query}).encode()
        req = urllib.request.Request(
            FIREFLIES_API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "DataOS/1.0"
            }
        )

        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())

        if "errors" in data:
            print(f"Fireflies API error: {data['errors'][0].get('message', 'unknown')}")
            return []

        transcripts = data.get("data", {}).get("transcripts", []) or []
        meetings = []

        for t in transcripts:
            date_str = t.get("date", "")
            if date_str:
                try:
                    # Fireflies returns epoch ms
                    ts = int(date_str) / 1000
                    date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    date_str = str(date_str)[:10]

            if date_str < since:
                continue

            # Build transcript text from sentences
            sentences = t.get("sentences") or []
            transcript_lines = []
            for s in sentences:
                speaker = s.get("speaker_name", "Unknown")
                text = s.get("text", "")
                if text:
                    transcript_lines.append(f"{speaker}: {text}")
            transcript_text = "\n".join(transcript_lines)

            # Participants
            participants = json.dumps(t.get("participants") or [])

            # Summary
            summary_obj = t.get("summary") or {}
            summary = summary_obj.get("overview", "")
            action_items = json.dumps(summary_obj.get("action_items") or [])

            meetings.append({
                "meeting_id": t["id"],
                "source": "fireflies",
                "title": t.get("title", "Untitled Meeting"),
                "date": date_str,
                "duration_minutes": t.get("duration"),
                "participants": participants,
                "transcript_text": transcript_text,
                "summary": summary,
                "action_items_raw": action_items,
                "external_url": f"https://app.fireflies.ai/view/{t['id']}",
            })

        print(f"Fireflies: collected {len(meetings)} meetings from last {days} days")
        return meetings

    except Exception as e:
        print(f"Fireflies collection error: {e}")
        return []


if __name__ == "__main__":
    meetings = collect(days=30)
    for m in meetings:
        print(f"  {m['date']} — {m['title']} ({m['duration_minutes']} min)")
