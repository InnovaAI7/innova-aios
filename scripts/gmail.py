"""Gmail CLI — used by the Telegram bot to manage Cameron's email.

Usage:
    python scripts/gmail.py search "query string" [--max N]
    python scripts/gmail.py read <message_id>
    python scripts/gmail.py send --to "a@b.com" --subject "Subject" --body "Body text"
    python scripts/gmail.py reply <message_id> --body "Reply text"
    python scripts/gmail.py labels
    python scripts/gmail.py label <message_id> --add "LabelName" [--remove "INBOX"]
    python scripts/gmail.py archive <message_id>
    python scripts/gmail.py trash <message_id>

All email operations use cameron@innovaaiintegration.com.
"""

import argparse
import base64
import json
import sys
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = ROOT / "credentials" / "google_token.json"


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
    return build("gmail", "v1", credentials=_get_creds())


# ── Search ────────────────────────────────────────────────────────────────────

def cmd_search(args):
    """Search emails using Gmail query syntax."""
    service = _service()
    results = service.users().messages().list(
        userId="me", q=args.query, maxResults=args.max
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        print(json.dumps({"results": [], "count": 0}))
        return

    output = []
    for msg_meta in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_meta["id"], format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        output.append({
            "id": msg["id"],
            "threadId": msg["threadId"],
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
            "labels": msg.get("labelIds", []),
        })

    print(json.dumps({"results": output, "count": len(output)}, indent=2))


# ── Read ──────────────────────────────────────────────────────────────────────

def _extract_body(payload) -> str:
    """Recursively extract plain text body from email payload."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        text = _extract_body(part)
        if text:
            return text
    return ""


def cmd_read(args):
    """Read a full email by message ID."""
    service = _service()
    msg = service.users().messages().get(userId="me", id=args.message_id, format="full").execute()

    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    body = _extract_body(msg["payload"])

    print(json.dumps({
        "id": msg["id"],
        "threadId": msg["threadId"],
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
        "labels": msg.get("labelIds", []),
        "body": body,
    }, indent=2))


# ── Send ──────────────────────────────────────────────────────────────────────

def _create_message(to: str, subject: str, body: str, thread_id: str = None,
                    in_reply_to: str = None, references: str = None) -> dict:
    """Create a Gmail API message payload."""
    mime = MIMEText(body)
    mime["to"] = to
    mime["subject"] = subject
    if in_reply_to:
        mime["In-Reply-To"] = in_reply_to
        mime["References"] = references or in_reply_to

    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    msg = {"raw": raw}
    if thread_id:
        msg["threadId"] = thread_id
    return msg


def cmd_send(args):
    """Send a new email."""
    service = _service()
    message = _create_message(to=args.to, subject=args.subject, body=args.body)
    sent = service.users().messages().send(userId="me", body=message).execute()
    print(json.dumps({"status": "sent", "id": sent["id"], "threadId": sent["threadId"]}))


# ── Reply ─────────────────────────────────────────────────────────────────────

def cmd_reply(args):
    """Reply to an existing email thread."""
    service = _service()

    # Get original message for threading headers
    original = service.users().messages().get(userId="me", id=args.message_id, format="metadata",
                                               metadataHeaders=["From", "Subject", "Message-ID"]).execute()
    headers = {h["name"]: h["value"] for h in original["payload"]["headers"]}

    # Reply goes to the original sender
    reply_to = headers.get("From", "")
    subject = headers.get("Subject", "")
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    message_id = headers.get("Message-ID", "")

    message = _create_message(
        to=reply_to, subject=subject, body=args.body,
        thread_id=original["threadId"],
        in_reply_to=message_id, references=message_id,
    )
    sent = service.users().messages().send(userId="me", body=message).execute()
    print(json.dumps({"status": "replied", "id": sent["id"], "threadId": sent["threadId"]}))


# ── Labels / Folders ──────────────────────────────────────────────────────────

def cmd_labels(args):
    """List all Gmail labels."""
    service = _service()
    results = service.users().labels().list(userId="me").execute()
    labels = [{"id": l["id"], "name": l["name"], "type": l.get("type", "")}
              for l in results.get("labels", [])]
    print(json.dumps({"labels": labels}, indent=2))


def _resolve_label_id(service, label_name: str) -> str:
    """Resolve a label name to its ID, creating it if it doesn't exist."""
    results = service.users().labels().list(userId="me").execute()
    for label in results.get("labels", []):
        if label["name"].lower() == label_name.lower():
            return label["id"]

    # Label doesn't exist — create it
    new_label = service.users().labels().create(userId="me", body={
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }).execute()
    return new_label["id"]


def cmd_label(args):
    """Add or remove labels on a message (moves it to folders)."""
    service = _service()

    add_ids = []
    remove_ids = []

    if args.add:
        add_ids.append(_resolve_label_id(service, args.add))
    if args.remove:
        remove_ids.append(_resolve_label_id(service, args.remove))

    body = {}
    if add_ids:
        body["addLabelIds"] = add_ids
    if remove_ids:
        body["removeLabelIds"] = remove_ids

    service.users().messages().modify(userId="me", id=args.message_id, body=body).execute()
    print(json.dumps({"status": "labels_updated", "id": args.message_id,
                       "added": args.add or "", "removed": args.remove or ""}))


def cmd_archive(args):
    """Archive a message (remove from INBOX)."""
    service = _service()
    service.users().messages().modify(
        userId="me", id=args.message_id, body={"removeLabelIds": ["INBOX"]}
    ).execute()
    print(json.dumps({"status": "archived", "id": args.message_id}))


def cmd_trash(args):
    """Move a message to trash."""
    service = _service()
    service.users().messages().trash(userId="me", id=args.message_id).execute()
    print(json.dumps({"status": "trashed", "id": args.message_id}))


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gmail CLI for Baymax")
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    p_search = sub.add_parser("search")
    p_search.add_argument("query", help="Gmail search query")
    p_search.add_argument("--max", type=int, default=10, help="Max results")

    # read
    p_read = sub.add_parser("read")
    p_read.add_argument("message_id", help="Message ID to read")

    # send
    p_send = sub.add_parser("send")
    p_send.add_argument("--to", required=True, help="Recipient email")
    p_send.add_argument("--subject", required=True, help="Email subject")
    p_send.add_argument("--body", required=True, help="Email body text")

    # reply
    p_reply = sub.add_parser("reply")
    p_reply.add_argument("message_id", help="Message ID to reply to")
    p_reply.add_argument("--body", required=True, help="Reply body text")

    # labels
    sub.add_parser("labels")

    # label (modify)
    p_label = sub.add_parser("label")
    p_label.add_argument("message_id", help="Message ID")
    p_label.add_argument("--add", help="Label name to add")
    p_label.add_argument("--remove", help="Label name to remove")

    # archive
    p_archive = sub.add_parser("archive")
    p_archive.add_argument("message_id", help="Message ID to archive")

    # trash
    p_trash = sub.add_parser("trash")
    p_trash.add_argument("message_id", help="Message ID to trash")

    args = parser.parse_args()

    commands = {
        "search": cmd_search,
        "read": cmd_read,
        "send": cmd_send,
        "reply": cmd_reply,
        "labels": cmd_labels,
        "label": cmd_label,
        "archive": cmd_archive,
        "trash": cmd_trash,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
