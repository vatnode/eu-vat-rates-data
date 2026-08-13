#!/usr/bin/env python3
"""Keep the standard-rate history current.

Runs daily alongside scripts/update.py. Queries TEDB for today's standard
rates and appends a new period for any member state whose rate has moved since
the last recorded one, then rebuilds data/eu-vat-rates-history.json.

Only ever appends. The frozen booklet extract (data/history-pre-tedb.json) is
never touched, and existing periods in data/history-tedb.json are never
rewritten — a rate change is a new fact, not a correction of an old one.

Usage:
    python3 scripts/update_history.py [--dry-run]

Dependencies:
    pip install requests
"""

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from backfill_tedb_history import fetch, find_change_date

REPO_ROOT = Path(__file__).resolve().parent.parent
TEDB_PATH = REPO_ROOT / "data" / "history-tedb.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not TEDB_PATH.exists():
        sys.exit(
            f"{TEDB_PATH.relative_to(REPO_ROOT)} is missing — run "
            "scripts/backfill_tedb_history.py first"
        )

    data = json.loads(TEDB_PATH.read_text(encoding="utf-8"))
    periods: dict[str, list[dict]] = data["periods"]

    today = dt.date.today()
    current = fetch(today)
    if not current:
        sys.exit("TEDB returned no rates — leaving history untouched")

    changes: list[str] = []
    for code, value in sorted(current.items()):
        history = periods.get(code)
        if not history:
            changes.append(f"{code}: first record, {value}%")
            periods[code] = [
                {"from": today.isoformat(), "standard": value,
                 "date_precision": "day"}
            ]
            continue

        last = max(history, key=lambda p: p["from"])
        if last.get("standard") == value:
            continue

        # Pin down the day the new rate took effect rather than stamping today.
        known_good = dt.date.fromisoformat(last["from"])
        effective = find_change_date(code, known_good, today, value)
        changes.append(
            f"{code}: {last.get('standard')}% → {value}% on {effective}"
        )
        history.append(
            {"from": effective.isoformat(), "standard": value,
             "date_precision": "day"}
        )
        history.sort(key=lambda p: p["from"])

    if not changes:
        print("No standard-rate changes.", file=sys.stderr)
    for line in changes:
        print(f"change: {line}", file=sys.stderr)

    if args.dry_run:
        print("Dry run — nothing written.", file=sys.stderr)
        return

    data["generated_on"] = today.isoformat()
    data["periods"] = periods
    TEDB_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "build_history.py")],
        check=True,
    )


if __name__ == "__main__":
    main()
