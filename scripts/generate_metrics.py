"""
DataOS — Key Metrics Generator

Reads the database and generates key-metrics.md for InnovaAI Integration.
Loaded by /prime so Claude always has fresh business data.

Usage:
    python scripts/generate_metrics.py
"""

import sqlite3
from datetime import datetime
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE_ROOT / "data" / "data.db"
OUTPUT_PATH = WORKSPACE_ROOT / "context" / "key-metrics.md"


def fmt_currency(value, symbol="£"):
    if value is None:
        return "No data"
    return f"{symbol}{value:,.0f}"


def fmt_number(value, suffix=""):
    if value is None:
        return "No data"
    return f"{value:,}{suffix}"


def query_one(conn, sql):
    try:
        row = conn.execute(sql).fetchone()
        return dict(row) if row else None
    except Exception:
        return None


def query_all(conn, sql):
    try:
        return [dict(r) for r in conn.execute(sql).fetchall()]
    except Exception:
        return []


def table_exists(conn, name):
    r = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return r is not None


# ============================================================
# SECTION GENERATORS
# ============================================================

def section_fx_rates(conn):
    if not table_exists(conn, "fx_rates"):
        return []
    lines = ["## Exchange Rates (USD base)", "| Currency | Rate | As Of |", "|----------|------|-------|"]
    rows = query_all(conn, """
        SELECT date, currency, rate FROM fx_rates
        WHERE date = (SELECT MAX(date) FROM fx_rates)
        ORDER BY currency
    """)
    for r in rows:
        lines.append(f"| {r['currency']} | {r['rate']:.4f} | {r['date']} |")
    lines.append("")
    return lines


def section_trello(conn):
    if not table_exists(conn, "trello_pipeline"):
        return []
    lines = ["## Client Pipeline (Trello)", "| Stage | Count | As Of |", "|-------|-------|-------|"]
    rows = query_all(conn, """
        SELECT list_name, card_count, date FROM trello_pipeline
        WHERE date = (SELECT MAX(date) FROM trello_pipeline)
        ORDER BY list_order ASC
    """)
    for r in rows:
        lines.append(f"| {r['list_name']} | {r['card_count']} | {r['date']} |")

    # Total active
    total = query_one(conn, """
        SELECT SUM(card_count) as total FROM trello_pipeline
        WHERE date = (SELECT MAX(date) FROM trello_pipeline)
    """)
    if total and total['total']:
        lines.append(f"| **Total Active** | **{total['total']}** | — |")
    lines.append("")
    return lines


def section_calendly(conn):
    if not table_exists(conn, "calendly_bookings"):
        return []
    lines = ["## Calls & Bookings (Calendly)", "| Metric | Value | Period |", "|--------|-------|--------|"]

    # Last 30 days bookings
    last30 = query_one(conn, """
        SELECT COUNT(*) as total FROM calendly_bookings
        WHERE event_date >= date('now', '-30 days')
        AND status != 'canceled'
    """)
    if last30:
        lines.append(f"| Calls booked (last 30 days) | {last30['total']} | Rolling 30d |")

    # This month
    this_month = query_one(conn, """
        SELECT COUNT(*) as total FROM calendly_bookings
        WHERE strftime('%Y-%m', event_date) = strftime('%Y-%m', 'now')
        AND status != 'canceled'
    """)
    if this_month:
        lines.append(f"| Calls booked (this month) | {this_month['total']} | MTD |")

    # Last 7 days
    last7 = query_one(conn, """
        SELECT COUNT(*) as total FROM calendly_bookings
        WHERE event_date >= date('now', '-7 days')
        AND status != 'canceled'
    """)
    if last7:
        lines.append(f"| Calls booked (last 7 days) | {last7['total']} | Last 7d |")

    lines.append("")
    return lines


# ============================================================
# SECTIONS REGISTRY
# ============================================================

SECTIONS = [
    section_trello,
    section_calendly,
    section_fx_rates,
]


def generate(conn):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "# Key Metrics — InnovaAI Integration",
        "",
        f"> Auto-generated from database. Last updated: {today}",
        f"> Source: `data/data.db` | Regenerate: `python scripts/generate_metrics.py`",
        "",
    ]

    for section_fn in SECTIONS:
        try:
            section_lines = section_fn(conn)
            if section_lines:
                lines.extend(section_lines)
        except Exception as e:
            lines.append(f"<!-- Error in {section_fn.__name__}: {e} -->")
            lines.append("")

    lines.append("## Data Freshness")
    lines.append("| Source | Latest Record | Status |")
    lines.append("|--------|---------------|--------|")

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name != 'collection_log' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()

    for t in tables:
        name = t["name"]
        try:
            row = conn.execute(f"SELECT MAX(date) as d FROM {name}").fetchone()
            if row and row["d"]:
                lines.append(f"| {name} | {row['d']} | Connected |")
            else:
                lines.append(f"| {name} | — | Empty |")
        except Exception:
            lines.append(f"| {name} | — | No date column |")

    lines.append("")
    return "\n".join(lines)


def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    content = generate(conn)
    conn.close()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content)
    print(f"Key metrics written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
