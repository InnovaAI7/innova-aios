"""
IntelOS — Master Collection Script

Runs all IntelOS collectors (meetings, etc.) and writes to the database.
Called hourly by cron.

Usage:
    python scripts/intel/collect_all.py
    python scripts/intel/collect_all.py --days 30   # backfill
"""

import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Ensure imports work regardless of where script is called from
INTEL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(INTEL_DIR))

from db import init_db, write_meetings, get_meeting_stats


def main():
    parser = argparse.ArgumentParser(description="Run IntelOS collectors")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    args = parser.parse_args()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] IntelOS collection started (last {args.days} days)")

    conn = init_db()
    total = 0

    # --- Fireflies ---
    try:
        from collect_fireflies import collect as collect_fireflies
        meetings = collect_fireflies(days=args.days)
        if meetings:
            count = write_meetings(conn, meetings)
            print(f"  Fireflies: {count} meetings written")
            total += count
        else:
            print(f"  Fireflies: 0 meetings (skipped or no new meetings)")
    except Exception as e:
        print(f"  Fireflies: ERROR — {e}")

    conn.close()

    stats_conn = init_db()
    stats = get_meeting_stats(stats_conn)
    stats_conn.close()

    print(f"[{timestamp}] Done — {total} new records written")
    print(f"  Total meetings in database: {stats['total_meetings']}")
    print(f"  Latest meeting: {stats['latest_meeting_date'] or 'none yet'}")


if __name__ == "__main__":
    main()
