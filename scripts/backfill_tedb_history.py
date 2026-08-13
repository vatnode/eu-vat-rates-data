#!/usr/bin/env python3
"""Backfill standard-rate history from EC TEDB (coverage starts 2016-01-01).

TEDB answers `situationOn` queries for past dates, but the `situationOn` it
echoes back is the start of its own record period, not the date the rate
changed. Change points are therefore found by scanning month by month and
binary-searching the days around each observed change.

One-off script: its output is committed as data/history-tedb.json and refreshed
by scripts/update_history.py from then on.

Usage:
    python3 scripts/backfill_tedb_history.py [--from 2016-01-01] [--out PATH]

Dependencies:
    pip install requests
"""

import argparse
import datetime as dt
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Error: 'requests' not installed. Run: pip install requests")

TEDB_URL = "https://ec.europa.eu/taxation_customs/tedb/ws/VatRetrievalService"
NS_MSG = "urn:ec.europa.eu:taxud:tedb:services:v1:IVatRetrievalService"
NS_TYPES = NS_MSG + ":types"
SOAP_ACTION = (
    "urn:ec.europa.eu:taxud:tedb:services:v1:VatRetrievalService/RetrieveVatRates"
)

# TEDB returns nothing before this date (verified: 2015-01-01 is empty).
TEDB_EPOCH = dt.date(2016, 1, 1)

MEMBER_STATES = [
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR",
    "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO",
    "SE", "SI", "SK",
]

TEDB_TO_ISO = {"EL": "GR"}

REQUEST_PAUSE_SECONDS = 0.5


def build_body(situation_on: dt.date) -> bytes:
    states = "\n".join(
        f"        <types:isoCode>{s}</types:isoCode>" for s in MEMBER_STATES
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:v1="{NS_MSG}"
    xmlns:types="{NS_TYPES}">
  <soapenv:Body>
    <v1:retrieveVatRatesReqMsg>
      <types:memberStates>
{states}
      </types:memberStates>
      <types:situationOn>{situation_on.isoformat()}</types:situationOn>
    </v1:retrieveVatRatesReqMsg>
  </soapenv:Body>
</soapenv:Envelope>"""
    return xml.encode("utf-8")


def parse_standard_rates(xml_bytes: bytes) -> dict[str, float]:
    """Standard rate per member state.

    TEDB can return more than one STANDARD/DEFAULT entry for a country: Spain
    carries a second one for the Canary Islands (IGIC, 7%), told apart only by
    a free-text comment. Take the highest, which is the mainland rate — the
    same rule scripts/update.py applies to the current-rates dataset.
    """
    root = ET.fromstring(xml_bytes)
    candidates: dict[str, set[float]] = {}

    for el in root.iter():
        if (el.tag.split("}")[-1] if "}" in el.tag else el.tag) != "vatRateResults":
            continue

        code = outer_type = rate_type = None
        value = None
        for child in el:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "memberState":
                raw = (child.text or "").strip()
                code = TEDB_TO_ISO.get(raw, raw)
            elif tag == "type":
                outer_type = (child.text or "").strip()
            elif tag == "rate":
                for gc in child:
                    gtag = gc.tag.split("}")[-1] if "}" in gc.tag else gc.tag
                    if gtag == "type":
                        rate_type = (gc.text or "").strip()
                    elif gtag == "value":
                        try:
                            value = float((gc.text or "").strip())
                        except ValueError:
                            value = None

        if code and outer_type == "STANDARD" and rate_type == "DEFAULT" and value:
            candidates.setdefault(code, set()).add(value)

    return {code: max(values) for code, values in candidates.items()}


_cache: dict[dt.date, dict[str, float]] = {}


def fetch(situation_on: dt.date) -> dict[str, float]:
    if situation_on in _cache:
        return _cache[situation_on]

    for attempt in range(3):
        try:
            resp = requests.post(
                TEDB_URL,
                data=build_body(situation_on),
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": SOAP_ACTION,
                },
                timeout=60,
            )
            resp.raise_for_status()
            rates = parse_standard_rates(resp.content)
            _cache[situation_on] = rates
            time.sleep(REQUEST_PAUSE_SECONDS)
            return rates
        except Exception as exc:  # noqa: BLE001 - retry on any transport failure
            if attempt == 2:
                sys.exit(f"TEDB request failed for {situation_on}: {exc}")
            time.sleep(2 ** attempt)

    return {}


def month_starts(start: dt.date, end: dt.date) -> list[dt.date]:
    out, cur = [], start.replace(day=1)
    while cur <= end:
        out.append(cur)
        cur = (cur.replace(day=28) + dt.timedelta(days=7)).replace(day=1)
    return out


def find_change_date(code: str, lo: dt.date, hi: dt.date, new_value: float) -> dt.date:
    """Smallest date in (lo, hi] where `code` already shows `new_value`."""
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if fetch(mid).get(code) == new_value:
            hi = mid
        else:
            lo = mid + dt.timedelta(days=1)
    return hi


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default=TEDB_EPOCH.isoformat())
    ap.add_argument("--out", default="data/history-tedb.json")
    args = ap.parse_args()

    start = dt.date.fromisoformat(args.start)
    if start < TEDB_EPOCH:
        sys.exit(f"TEDB has no data before {TEDB_EPOCH.isoformat()}")
    today = dt.date.today()

    months = month_starts(start, today)
    print(f"Scanning {len(months)} months for {len(MEMBER_STATES)} member states…",
          file=sys.stderr)

    periods: dict[str, list[dict]] = {}
    previous: dict[str, float] = {}
    prev_date: dt.date | None = None

    for i, probe in enumerate(months, 1):
        rates = fetch(probe)
        print(f"  [{i}/{len(months)}] {probe} → {len(rates)} states",
              file=sys.stderr)

        for code, value in sorted(rates.items()):
            if code not in previous:
                periods.setdefault(code, []).append(
                    {"from": probe.isoformat(), "standard": value,
                     "date_precision": "day" if probe == start else "month"}
                )
            elif previous[code] != value:
                exact = find_change_date(code, prev_date, probe, value)
                periods[code].append(
                    {"from": exact.isoformat(), "standard": value,
                     "date_precision": "day"}
                )
                print(f"      change: {code} {previous[code]} → {value} "
                      f"on {exact}", file=sys.stderr)
            previous[code] = value

        prev_date = probe

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "source": "European Commission TEDB",
                "coverage_from": start.isoformat(),
                "generated_on": today.isoformat(),
                "periods": periods,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    total = sum(len(v) for v in periods.values())
    print(f"Wrote {out_path} — {len(periods)} states, {total} periods",
          file=sys.stderr)


if __name__ == "__main__":
    main()
