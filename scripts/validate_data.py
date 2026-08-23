#!/usr/bin/env python3
"""Validate the published current and standard-rate history datasets."""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRENT = ROOT / "data" / "eu-vat-rates-data.json"
HISTORY = ROOT / "data" / "eu-vat-rates-history.json"

EU_CODES = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR",
    "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL",
    "PT", "RO", "SE", "SI", "SK",
}
REQUIRED_RATE_FIELDS = {
    "country", "currency", "eu_member", "vat_name", "vat_abbr", "standard",
    "reduced", "super_reduced", "parking", "format", "pattern",
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def iso_date(value: object, path: str, errors: list[str]) -> None:
    try:
        dt.date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{path}: expected ISO date, got {value!r}")


def validate_current(data: dict) -> list[str]:
    errors: list[str] = []
    if set(data) != {"version", "source", "publisher", "rates"}:
        errors.append("current root: unexpected or missing fields")
    iso_date(data.get("version"), "version", errors)
    rates = data.get("rates")
    if not isinstance(rates, dict):
        return errors + ["rates: expected object"]
    if len(rates) != 45:
        errors.append(f"rates: expected 45 jurisdictions, got {len(rates)}")
    actual_eu: set[str] = set()
    for code, rate in rates.items():
        prefix = f"rates.{code}"
        if not re.fullmatch(r"[A-Z]{2}", code):
            errors.append(f"{prefix}: key must be a two-letter uppercase code")
        if not isinstance(rate, dict) or set(rate) != REQUIRED_RATE_FIELDS:
            errors.append(f"{prefix}: unexpected or missing fields")
            continue
        for field in ("country", "currency", "vat_name", "vat_abbr", "format", "pattern"):
            if not isinstance(rate[field], str) or not rate[field]:
                errors.append(f"{prefix}.{field}: expected non-empty string")
        if not re.fullmatch(r"[A-Z]{3}", rate["currency"]):
            errors.append(f"{prefix}.currency: expected ISO 4217-style code")
        if not isinstance(rate["eu_member"], bool):
            errors.append(f"{prefix}.eu_member: expected boolean")
        elif rate["eu_member"]:
            actual_eu.add(code)
        for field in ("standard", "super_reduced", "parking"):
            value = rate[field]
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 100):
                errors.append(f"{prefix}.{field}: expected rate from 0 to 100 or null")
        reduced = rate["reduced"]
        if not isinstance(reduced, list) or reduced != sorted(set(reduced)):
            errors.append(f"{prefix}.reduced: expected sorted unique list")
        elif any(isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 100 for value in reduced):
            errors.append(f"{prefix}.reduced: rate outside 0 to 100")
        try:
            re.compile(rate["pattern"])
        except (re.error, TypeError) as exc:
            errors.append(f"{prefix}.pattern: invalid regex ({exc})")
    if actual_eu != EU_CODES:
        errors.append(f"eu_member flags do not match EU-27: {sorted(actual_eu ^ EU_CODES)}")
    return errors


def validate_history(data: dict) -> list[str]:
    errors: list[str] = []
    history = data.get("history")
    sources = data.get("sources")
    if not isinstance(history, dict) or set(history) != EU_CODES:
        return ["history: expected exactly the EU-27 country codes"]
    if not isinstance(sources, dict):
        return ["sources: expected object"]
    for code, entry in history.items():
        periods = entry.get("periods") if isinstance(entry, dict) else None
        if not isinstance(periods, list) or not periods:
            errors.append(f"history.{code}.periods: expected non-empty list")
            continue
        previous_to: dt.date | None = None
        for index, period in enumerate(periods):
            prefix = f"history.{code}.periods[{index}]"
            iso_date(period.get("from"), f"{prefix}.from", errors)
            start = dt.date.fromisoformat(period["from"])
            end_raw = period.get("to")
            end = dt.date.fromisoformat(end_raw) if end_raw is not None else None
            if previous_to is not None and start != previous_to + dt.timedelta(days=1):
                errors.append(f"{prefix}: gap or overlap after {previous_to}")
            if end is not None and end < start:
                errors.append(f"{prefix}: end precedes start")
            if period.get("source") not in sources:
                errors.append(f"{prefix}.source: unknown source")
            previous_to = end
            if end is None and index != len(periods) - 1:
                errors.append(f"{prefix}: open period must be last")
    return errors


def main() -> int:
    errors = validate_current(load_json(CURRENT)) + validate_history(load_json(HISTORY))
    if errors:
        print("Dataset validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Validated current dataset (45 jurisdictions) and EU-27 standard-rate history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
