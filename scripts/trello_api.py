#!/usr/bin/env python3
"""
Baymax Trello API — Client Pipeline Manager

Commands:
    pipeline                        — Full pipeline overview
    client <card_id>                — Detailed card info
    search <keyword>                — Search cards by name
    move <card_id> <list_name>      — Move card to a stage
    comment <card_id> <text>        — Add comment to a card
    due <card_id> <YYYY-MM-DD>      — Set/update due date
    stale <days>                    — Cards with no activity in N days
    labels <card_id>                — Show labels on a card
    add-label <card_id> <label>     — Add a label to a card
"""

import sys
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_BASE = "https://api.trello.com/1"
KEY = os.getenv("TRELLO_API_KEY", "").strip()
TOKEN = os.getenv("TRELLO_TOKEN", "").strip()
BOARD_ID = os.getenv("TRELLO_BOARD_ID", "").strip()

PIPELINE_ORDER = [
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


def api_get(path, params=""):
    url = f"{API_BASE}{path}?key={KEY}&token={TOKEN}{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Baymax/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def api_post(path, data=None):
    url = f"{API_BASE}{path}?key={KEY}&token={TOKEN}"
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"User-Agent": "Baymax/1.0", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def api_put(path, data=None):
    url = f"{API_BASE}{path}?key={KEY}&token={TOKEN}"
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(url, data=body, method="PUT",
                                 headers={"User-Agent": "Baymax/1.0", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get_lists():
    lists = api_get(f"/boards/{BOARD_ID}/lists", "&fields=name,pos")
    return {l["id"]: l["name"] for l in lists}, lists


def get_cards():
    return api_get(f"/boards/{BOARD_ID}/cards",
                   "&filter=open&fields=idList,name,due,dateLastActivity,labels,desc,shortUrl")


def days_ago(date_str):
    if not date_str:
        return None
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - dt
    return delta.days


def format_date(date_str):
    if not date_str:
        return "not set"
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    d = days_ago(date_str)
    formatted = dt.strftime("%Y-%m-%d")
    if d is not None and d < 0:
        return f"{formatted} (in {abs(d)} days)"
    elif d == 0:
        return f"{formatted} (today)"
    else:
        return f"{formatted} ({d} days ago)"


# --- COMMANDS ---

def cmd_pipeline():
    list_map, lists = get_lists()
    cards = get_cards()

    # Group cards by list
    by_list = {}
    for card in cards:
        list_name = list_map.get(card["idList"], "Unknown")
        by_list.setdefault(list_name, []).append(card)

    now = datetime.now(timezone.utc)
    active_count = 0
    overdue = []
    output = []

    for stage in PIPELINE_ORDER:
        stage_cards = by_list.get(stage, [])
        if not stage_cards:
            continue

        if stage not in ("Complete", "Project Cancelled / On Pause"):
            active_count += len(stage_cards)

        output.append(f"\n{stage} — {len(stage_cards)} client(s)")
        for c in stage_cards:
            activity = days_ago(c.get("dateLastActivity"))
            activity_str = f"active {activity}d ago" if activity is not None else "no activity"
            due_str = ""
            if c.get("due"):
                due_days = days_ago(c["due"])
                if due_days is not None and due_days > 0:
                    due_str = f" | OVERDUE by {due_days}d"
                    overdue.append(f"{c['name']} ({stage})")
                elif due_days is not None:
                    due_str = f" | due {format_date(c['due'])}"
            output.append(f"  - {c['name']} ({activity_str}{due_str}) [id:{c['shortUrl'].split('/')[-1]}]")

    # Summary
    bottleneck = max(
        [(s, len(by_list.get(s, []))) for s in PIPELINE_ORDER
         if s not in ("Complete", "Project Cancelled / On Pause")],
        key=lambda x: x[1], default=("None", 0)
    )

    print(f"PIPELINE OVERVIEW — {now.strftime('%Y-%m-%d')}")
    print("\n".join(output))
    print(f"\nSUMMARY")
    print(f"Active clients: {active_count}")
    print(f"Bottleneck: {bottleneck[0]} ({bottleneck[1]} clients)")
    if overdue:
        print(f"Overdue: {', '.join(overdue)}")
    else:
        print("Overdue: None")


def cmd_search(keyword):
    list_map, _ = get_lists()
    cards = get_cards()
    keyword_lower = keyword.lower()
    matches = [c for c in cards if keyword_lower in c["name"].lower()]

    if not matches:
        print(f"No cards found matching '{keyword}'")
        return

    print(f"Found {len(matches)} match(es) for '{keyword}':\n")
    for c in matches:
        stage = list_map.get(c["idList"], "Unknown")
        card_id = c["shortUrl"].split("/")[-1]
        print(f"  {c['name']}")
        print(f"    Stage: {stage}")
        print(f"    Last activity: {format_date(c.get('dateLastActivity'))}")
        print(f"    Due: {format_date(c.get('due'))}")
        print(f"    Card ID: {card_id}")
        print(f"    URL: {c['shortUrl']}")
        print()


def cmd_client(card_id):
    # card_id could be the short ID or full ID
    # Try to get card directly
    try:
        card = api_get(f"/cards/{card_id}", "&fields=name,idList,due,dateLastActivity,labels,desc,shortUrl")
    except Exception:
        # Try searching by short link
        list_map, _ = get_lists()
        cards = get_cards()
        match = [c for c in cards if c["shortUrl"].endswith(f"/{card_id}")]
        if not match:
            print(f"Card '{card_id}' not found.")
            return
        card = match[0]

    list_map, _ = get_lists()
    stage = list_map.get(card["idList"], "Unknown")

    print(f"CLIENT: {card['name']}")
    print(f"Stage: {stage}")
    print(f"Last activity: {format_date(card.get('dateLastActivity'))}")
    print(f"Due: {format_date(card.get('due'))}")
    if card.get("labels"):
        print(f"Labels: {', '.join(l['name'] or l['color'] for l in card['labels'])}")
    if card.get("desc"):
        print(f"Description: {card['desc'][:500]}")
    print(f"URL: {card.get('shortUrl', 'N/A')}")

    # Get recent comments
    try:
        actions = api_get(f"/cards/{card['id']}/actions", "&filter=commentCard&limit=3")
        if actions:
            print(f"\nRecent comments:")
            for a in actions:
                date = format_date(a.get("date"))
                text = a.get("data", {}).get("text", "")[:200]
                member = a.get("memberCreator", {}).get("fullName", "Unknown")
                print(f"  [{date}] {member}: {text}")
    except Exception:
        pass

    # Get checklists
    try:
        checklists = api_get(f"/cards/{card['id']}/checklists")
        if checklists:
            print(f"\nChecklists:")
            for cl in checklists:
                items = cl.get("checkItems", [])
                done = sum(1 for i in items if i["state"] == "complete")
                print(f"  {cl['name']}: {done}/{len(items)} complete")
    except Exception:
        pass


def cmd_move(card_id, list_name):
    list_map, lists = get_lists()

    # Find target list
    target = None
    list_name_lower = list_name.lower()
    for l in lists:
        if l["name"].lower() == list_name_lower:
            target = l
            break
    # Fuzzy match
    if not target:
        for l in lists:
            if list_name_lower in l["name"].lower():
                target = l
                break

    if not target:
        print(f"Stage '{list_name}' not found. Valid stages:")
        for s in PIPELINE_ORDER:
            print(f"  - {s}")
        return

    try:
        api_put(f"/cards/{card_id}", {"idList": target["id"]})
        print(f"Moved card to: {target['name']}")
    except Exception as e:
        print(f"Error moving card: {e}")


def cmd_comment(card_id, text):
    try:
        api_post(f"/cards/{card_id}/actions/comments", {"text": text})
        print(f"Comment added to card.")
    except Exception as e:
        print(f"Error adding comment: {e}")


def cmd_due(card_id, date_str):
    try:
        api_put(f"/cards/{card_id}", {"due": date_str})
        print(f"Due date set to: {date_str}")
    except Exception as e:
        print(f"Error setting due date: {e}")


def cmd_stale(days_threshold):
    list_map, _ = get_lists()
    cards = get_cards()
    threshold = int(days_threshold)
    now = datetime.now(timezone.utc)
    stale = []

    for c in cards:
        stage = list_map.get(c["idList"], "Unknown")
        if stage in ("Complete", "Project Cancelled / On Pause"):
            continue
        d = days_ago(c.get("dateLastActivity"))
        if d is not None and d >= threshold:
            stale.append((c, stage, d))

    stale.sort(key=lambda x: x[2], reverse=True)

    if not stale:
        print(f"No stale cards (all active within {threshold} days).")
        return

    print(f"STALE CARDS — No activity in {threshold}+ days:\n")
    for c, stage, d in stale:
        card_id = c["shortUrl"].split("/")[-1]
        due_str = ""
        if c.get("due"):
            due_d = days_ago(c["due"])
            if due_d is not None and due_d > 0:
                due_str = f" | OVERDUE by {due_d}d"
        print(f"  {c['name']}")
        print(f"    Stage: {stage} | Last activity: {d} days ago{due_str}")
        print(f"    Card ID: {card_id}")
        print()


def cmd_labels(card_id):
    try:
        card = api_get(f"/cards/{card_id}", "&fields=labels,name")
        print(f"Labels on {card['name']}:")
        if card.get("labels"):
            for l in card["labels"]:
                print(f"  - {l.get('name') or l['color']} ({l['color']})")
        else:
            print("  No labels")
    except Exception as e:
        print(f"Error: {e}")


def cmd_add_label(card_id, label_name):
    try:
        # Get board labels
        labels = api_get(f"/boards/{BOARD_ID}/labels")
        target = None
        for l in labels:
            if l.get("name", "").lower() == label_name.lower():
                target = l
                break
        if not target:
            # Try color match
            for l in labels:
                if l.get("color", "").lower() == label_name.lower():
                    target = l
                    break
        if not target:
            print(f"Label '{label_name}' not found. Available labels:")
            for l in labels:
                print(f"  - {l.get('name') or '(unnamed)'} ({l['color']})")
            return

        api_post(f"/cards/{card_id}/idLabels", {"value": target["id"]})
        print(f"Label '{target.get('name') or target['color']}' added.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if not KEY or not TOKEN or not BOARD_ID:
        print("ERROR: Missing TRELLO_API_KEY, TRELLO_TOKEN, or TRELLO_BOARD_ID in .env")
        sys.exit(1)

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "pipeline":
        cmd_pipeline()
    elif cmd == "search" and len(sys.argv) >= 3:
        cmd_search(sys.argv[2])
    elif cmd == "client" and len(sys.argv) >= 3:
        cmd_client(sys.argv[2])
    elif cmd == "move" and len(sys.argv) >= 4:
        cmd_move(sys.argv[2], sys.argv[3])
    elif cmd == "comment" and len(sys.argv) >= 4:
        cmd_comment(sys.argv[2], sys.argv[3])
    elif cmd == "due" and len(sys.argv) >= 4:
        cmd_due(sys.argv[2], sys.argv[3])
    elif cmd == "stale":
        cmd_stale(sys.argv[2] if len(sys.argv) >= 3 else "14")
    elif cmd == "labels" and len(sys.argv) >= 3:
        cmd_labels(sys.argv[2])
    elif cmd == "add-label" and len(sys.argv) >= 4:
        cmd_add_label(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
