"""
IntelOS — Meeting classifier.

Classifies meetings by department/stream based on participant emails
matched against the staff registry. If no registry is populated,
everything goes into a single 'general' stream.

Usage:
    python scripts/classify.py                  # Classify all unclassified meetings
    python scripts/classify.py --reclassify     # Re-classify everything
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Import from sibling module
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_connection


# ─── Google Calendar Color → Stream Mapping ───────────────────────────────────
# Cameron's calendar color system. colorId is the Google Calendar API integer string.
# Color name is the human-readable label from the Google Calendar UI.
#
#   colorId | Color Name  | Meaning (Cameron's system)
#   --------|-------------|---------------------------
#     10    | Tomato/Red  | Admin
#      8    | Blueberry   | Software
#      9    | Basil       | Meetings (client/external)
#      5    | Banana      | LinkedIn / Marketing
#     11    | Graphite    | Centryn
#      3    | Grape       | Personal
#
CALENDAR_COLOR_STREAM = {
    # By colorId (string, as returned by Google Calendar API)
    "10": "admin",
    "8":  "software",
    "9":  "meetings",
    "5":  "marketing",
    "11": "centryn",
    "3":  "personal",
    # By color name (fallback if name is stored instead of ID)
    "tomato":    "admin",
    "red":       "admin",
    "blueberry": "software",
    "basil":     "meetings",
    "banana":    "marketing",
    "graphite":  "centryn",
    "grape":     "personal",
}

STREAM_LABELS = {
    "admin":     "Admin",
    "software":  "Software",
    "meetings":  "Meetings",
    "marketing": "LinkedIn/Marketing",
    "centryn":   "Centryn",
    "personal":  "Personal",
    "general":   "General",
}


def classify_by_calendar_color(color_id: str = None, color_name: str = None) -> str:
    """Return the stream name for a Google Calendar color.

    Pass either the colorId integer string (e.g. "10") or the color name
    (e.g. "tomato"). Returns "general" if no match found.
    """
    if color_id and str(color_id) in CALENDAR_COLOR_STREAM:
        return CALENDAR_COLOR_STREAM[str(color_id)]
    if color_name and color_name.lower() in CALENDAR_COLOR_STREAM:
        return CALENDAR_COLOR_STREAM[color_name.lower()]
    return "general"


def classify_meeting(conn, meeting: dict, department_streams: dict) -> dict:
    """Classify a single meeting by stream based on participants.

    Args:
        conn: Database connection
        meeting: Dict with participants, title, meeting_id
        department_streams: Mapping of department names to stream labels
            e.g. {"sales": "sales", "engineering": "engineering", "leadership": "internal"}
            If empty, all meetings go to "general".

    Returns:
        {"stream": str, "call_type": str, "reason": str}
    """
    participants_json = meeting.get("participants", "")
    title = (meeting.get("title") or "").strip()

    # Parse participants
    try:
        participants = json.loads(participants_json) if participants_json else []
    except (json.JSONDecodeError, TypeError):
        participants = []

    # Look up each participant in staff registry
    staff_found = []
    external_found = []

    for p in participants:
        email = None
        name = None
        if isinstance(p, dict):
            email = p.get("email", "")
            name = p.get("name", "")
        elif isinstance(p, str):
            if "@" in p:
                email = p
            else:
                name = p

        if email:
            row = conn.execute(
                "SELECT * FROM staff_registry WHERE LOWER(email) = LOWER(?)",
                (email.strip(),)
            ).fetchone()
            if row:
                staff_found.append(dict(row))
            else:
                external_found.append({"email": email, "name": name or email})
        elif name:
            row = conn.execute(
                "SELECT * FROM staff_registry WHERE LOWER(name) = LOWER(?)",
                (name.strip(),)
            ).fetchone()
            if row:
                staff_found.append(dict(row))
            else:
                external_found.append({"name": name})

    # If no department streams configured, everything is "general"
    if not department_streams:
        call_type = "meeting"
        if len(staff_found) >= 2 and len(external_found) == 0:
            call_type = "team_meeting"
        elif len(staff_found) >= 1 and len(external_found) >= 1:
            call_type = "one_on_one"
        return {"stream": "general", "call_type": call_type, "reason": "no_departments_configured"}

    # Determine call type
    staff_count = len(staff_found)
    external_count = len(external_found)

    if staff_count >= 2 and external_count == 0:
        call_type = "team_meeting"
    elif staff_count >= 1 and external_count >= 1:
        call_type = "one_on_one"
    elif staff_count == 0 and external_count >= 2:
        call_type = "external"
    else:
        call_type = "meeting"

    # Determine stream from staff department
    if staff_found:
        dept = staff_found[0].get("department", "general")
        stream = department_streams.get(dept, dept)
        staff_names = [s["name"] for s in staff_found]
        reason = f"department:{dept} staff:{', '.join(staff_names)}"
    elif title:
        stream = _classify_by_title(title, department_streams)
        reason = f"title_heuristic:{title[:60]}"
    else:
        stream = "general"
        reason = "no_participants_no_title"

    return {"stream": stream, "call_type": call_type, "reason": reason}


def _classify_by_title(title: str, department_streams: dict) -> str:
    """Fallback: try to classify by title keywords."""
    title_lower = title.lower()

    # Check if any department name appears in the title
    for dept in department_streams:
        if dept.lower() in title_lower:
            return department_streams[dept]

    # Common keywords
    for keyword in ["sales", "demo", "discovery", "qualification"]:
        if keyword in title_lower:
            return department_streams.get("sales", "sales")

    for keyword in ["standup", "sync", "team", "internal", "weekly"]:
        if keyword in title_lower:
            return "team_meeting"

    return "general"


def get_department_streams(conn) -> dict:
    """Build department→stream mapping from the staff registry.

    Returns a dict like {"sales": "sales", "engineering": "engineering"}
    built from distinct departments in the registry.
    """
    rows = conn.execute(
        "SELECT DISTINCT department FROM staff_registry WHERE is_active = 1"
    ).fetchall()
    if not rows:
        return {}
    # By default, each department maps to itself as a stream
    return {row["department"]: row["department"] for row in rows}


def classify_all(conn, reclassify: bool = False) -> int:
    """Classify all (or only unclassified) meetings. Returns count."""
    department_streams = get_department_streams(conn)

    if reclassify:
        cursor = conn.execute("SELECT meeting_id, title, participants FROM meetings")
    else:
        cursor = conn.execute(
            "SELECT meeting_id, title, participants FROM meetings WHERE stream IS NULL"
        )

    meetings = [dict(row) for row in cursor.fetchall()]
    if not meetings:
        print("No meetings to classify.")
        return 0

    now = datetime.now(timezone.utc).isoformat()
    count = 0

    for meeting in meetings:
        result = classify_meeting(conn, meeting, department_streams)
        conn.execute(
            "UPDATE meetings SET stream = ?, call_type = ?, classified_at = ? "
            "WHERE meeting_id = ?",
            (result["stream"], result["call_type"], now, meeting["meeting_id"])
        )
        count += 1

    conn.commit()
    streams_summary = {}
    for m in meetings:
        r = classify_meeting(conn, m, department_streams)
        streams_summary[r["stream"]] = streams_summary.get(r["stream"], 0) + 1

    print(f"Classified {count} meetings:")
    for stream, ct in sorted(streams_summary.items()):
        print(f"  {stream}: {ct}")

    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify meetings by department/stream")
    parser.add_argument("--reclassify", action="store_true",
                        help="Re-classify all meetings (not just unclassified)")
    args = parser.parse_args()

    conn = get_connection()
    classify_all(conn, reclassify=args.reclassify)
    conn.close()
