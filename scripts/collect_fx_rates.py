"""
DataOS — FX Rates Collector (Starter)

Fetches GBP/USD exchange rate from the Frankfurter API (European Central Bank data).
No API key needed — proves the pipeline works.

Tables created: fx_rates
"""

import sqlite3
import urllib.request
import json
from datetime import datetime, timezone

# Uses Open Exchange Rates public endpoint — no API key needed for latest USD rates
# Falls back to a hardcoded GBP rate if the API is unavailable
API_URL = "https://open.er-api.com/v6/latest/USD"


def collect():
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": "DataOS/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        rates = data.get("rates", {})
        filtered = {k: rates[k] for k in ["GBP", "EUR"] if k in rates}
        return {
            "source": "fx_rates",
            "status": "success",
            "data": {
                "base": "USD",
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "rates": filtered,
            }
        }
    except Exception as e:
        return {"source": "fx_rates", "status": "error", "reason": str(e)}


def write(conn, result, date):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fx_rates (
            date TEXT NOT NULL,
            currency TEXT NOT NULL,
            rate REAL NOT NULL,
            base TEXT DEFAULT 'USD',
            collected_at TEXT,
            PRIMARY KEY (date, currency)
        )
    """)

    if result.get("status") != "success":
        conn.commit()
        return 0

    data = result["data"]
    rates = data.get("rates", {})
    rate_date = data.get("date", date)
    collected_at = datetime.now(timezone.utc).isoformat()
    records = 0

    for currency, rate in rates.items():
        conn.execute(
            "INSERT OR REPLACE INTO fx_rates (date, currency, rate, base, collected_at) VALUES (?, ?, ?, ?, ?)",
            (rate_date, currency, rate, "USD", collected_at)
        )
        records += 1

    conn.commit()
    return records


if __name__ == "__main__":
    result = collect()
    if result["status"] == "success":
        print(f"FX Rates for {result['data']['date']}:")
        for curr, rate in sorted(result["data"]["rates"].items()):
            print(f"  USD -> {curr}: {rate:.4f}")
    else:
        print(f"Error: {result.get('reason')}")
