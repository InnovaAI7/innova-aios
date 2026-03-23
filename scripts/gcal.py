"""Google Calendar CLI — used by the Telegram bot to manage Cameron's calendar.

Usage:
    python scripts/gcal.py list [--date YYYY-MM-DD] [--days N]
    python scripts/gcal.py get <event_id>
    python scripts/gcal.py create --title TITLE --start DATETIME --end DATETIME [--color COLOR_ID] [--attendees a@b.com,c@d.com] [--description DESC] [--location LOC]
    python scripts/gcal.py update <event_id> [--title TITLE] [--start DATETIME] [--end DATETIME] [--color COLOR_ID] [--attendees a@b.com,c@d.com] [--description DESC] [--location LOC]
    python scripts/gcal.py delete <event_id>
    python scripts/gcal.py free --start DATETIME --end DATETIME

Datetimes should be ISO 8601 format: 2026-03-27T09:00:00
All times are treated as Europe/London.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = ROOT / "credentials" / "google_token.json"
TIMEZONE = "Europe/London"
CALENDAR_ID = "primary"


def _get_creds() -> Credentials:
    token_data = json.loads(TOKEN_PATH.read_text())
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
    return creds


def _service():
    return build("calendar", "v3", credentials=_get_creds())


def cmd_list(args):
    service = _service()
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    time_min = f"{date}T00:00:00"
    time_max_dt = datetime.fromisoformat(f"{date}T00:00:00") + timedelta(days=args.days)
    time_max = time_max_dt.strftime("%Y-%m-%dT00:00:00")

    result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=f"{time_min}+00:00",
        timeMax=f"{time_max}+00:00",
        singleEvents=True,
        orderBy="startTime",
        timeZone=TIMEZONE,
    ).execute()

    events = result.get("items", [])
    print(json.dumps(events, indent=2))


def cmd_get(args):
    service = _service()
    event = service.events().get(
        calendarId=CALENDAR_ID,
        eventId=args.event_id,
    ).execute()
    print(json.dumps(event, indent=2))


def cmd_create(args):
    service = _service()
    body = {
        "summary": args.title,
        "start": {"dateTime": args.start, "timeZone": TIMEZONE},
        "end": {"dateTime": args.end, "timeZone": TIMEZONE},
    }
    if args.color:
        body["colorId"] = args.color
    if args.attendees:
        body["attendees"] = [{"email": e.strip()} for e in args.attendees.split(",")]
    if args.description:
        body["description"] = args.description
    if args.location:
        body["location"] = args.location

    event = service.events().insert(
        calendarId=CALENDAR_ID,
        body=body,
        conferenceDataVersion=0,
    ).execute()
    print(json.dumps({"status": "created", "id": event["id"], "link": event.get("htmlLink", "")}, indent=2))


def cmd_update(args):
    service = _service()
    event = service.events().get(calendarId=CALENDAR_ID, eventId=args.event_id).execute()

    if args.title:
        event["summary"] = args.title
    if args.start:
        event["start"] = {"dateTime": args.start, "timeZone": TIMEZONE}
    if args.end:
        event["end"] = {"dateTime": args.end, "timeZone": TIMEZONE}
    if args.color:
        event["colorId"] = args.color
    if args.attendees:
        event["attendees"] = [{"email": e.strip()} for e in args.attendees.split(",")]
    if args.description:
        event["description"] = args.description
    if args.location:
        event["location"] = args.location

    updated = service.events().update(
        calendarId=CALENDAR_ID,
        eventId=args.event_id,
        body=event,
    ).execute()
    print(json.dumps({"status": "updated", "id": updated["id"], "summary": updated.get("summary", "")}, indent=2))


def cmd_delete(args):
    service = _service()
    service.events().delete(calendarId=CALENDAR_ID, eventId=args.event_id).execute()
    print(json.dumps({"status": "deleted", "id": args.event_id}))


def cmd_free(args):
    service = _service()
    body = {
        "timeMin": f"{args.start}",
        "timeMax": f"{args.end}",
        "timeZone": TIMEZONE,
        "items": [{"id": CALENDAR_ID}],
    }
    result = service.freebusy().query(body=body).execute()
    busy = result["calendars"][CALENDAR_ID]["busy"]
    print(json.dumps({"busy": busy, "timeMin": args.start, "timeMax": args.end}, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Google Calendar CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list")
    p_list.add_argument("--date", help="Start date (YYYY-MM-DD), defaults to today")
    p_list.add_argument("--days", type=int, default=1, help="Number of days to fetch")

    # get
    p_get = sub.add_parser("get")
    p_get.add_argument("event_id")

    # create
    p_create = sub.add_parser("create")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--start", required=True, help="ISO datetime e.g. 2026-03-27T09:00:00")
    p_create.add_argument("--end", required=True, help="ISO datetime e.g. 2026-03-27T17:00:00")
    p_create.add_argument("--color", help="Google Calendar colorId")
    p_create.add_argument("--attendees", help="Comma-separated emails")
    p_create.add_argument("--description", help="Event description")
    p_create.add_argument("--location", help="Event location")

    # update
    p_update = sub.add_parser("update")
    p_update.add_argument("event_id")
    p_update.add_argument("--title")
    p_update.add_argument("--start", help="New start datetime")
    p_update.add_argument("--end", help="New end datetime")
    p_update.add_argument("--color", help="New colorId")
    p_update.add_argument("--attendees", help="New attendees (comma-separated emails)")
    p_update.add_argument("--description")
    p_update.add_argument("--location")

    # delete
    p_delete = sub.add_parser("delete")
    p_delete.add_argument("event_id")

    # free
    p_free = sub.add_parser("free")
    p_free.add_argument("--start", required=True)
    p_free.add_argument("--end", required=True)

    args = parser.parse_args()
    cmd_map = {
        "list": cmd_list,
        "get": cmd_get,
        "create": cmd_create,
        "update": cmd_update,
        "delete": cmd_delete,
        "free": cmd_free,
    }
    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
