#!/usr/bin/env python3
"""Extract standard-rate history from the EC TAXUD booklet.

Source document: "VAT rates applied in the Member States of the European
Union", DG TAXUD, last edition 06/2021 (publication discontinued in favour of
TEDB). Section VIII, "The evolution of VAT rates applicable in the Member
States", lists every dated rate change from 1967 onwards.

    https://taxation-customs.ec.europa.eu/system/files/2021-06/vat_rates_en.pdf

This is a one-off transcription tool, kept for reproducibility. Its output is
reviewed by hand and committed as data/history-pre-tedb.json, which is then
frozen — the daily pipeline never regenerates it. TEDB, which only answers for
dates from 2016-01-01, supplies everything after that.

Usage:
    python3 scripts/parse_booklet_history.py vat_rates_en.pdf > out.json

Requires `pdftotext` (poppler-utils) on PATH.
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

COUNTRY_TO_CODE = {
    "Belgium": "BE", "Bulgaria": "BG", "Czech Republic": "CZ", "Denmark": "DK",
    "Germany": "DE", "Estonia": "EE", "Ireland": "IE", "Greece": "GR",
    "Spain": "ES", "France": "FR", "Croatia": "HR", "Italy": "IT",
    "Cyprus": "CY", "Latvia": "LV", "Lithuania": "LT", "Luxembourg": "LU",
    "Hungary": "HU", "Malta": "MT", "Netherlands": "NL", "Austria": "AT",
    "Poland": "PL", "Portugal": "PT", "Romania": "RO", "Slovenia": "SI",
    "Slovak Republic": "SK", "Finland": "FI", "Sweden": "SE",
}

SECTION_HEADING = re.compile(
    r"The evolution of (the )?VAT rates applicable in the Member States",
    re.IGNORECASE,
)
FOOTNOTE = re.compile(r"^\(\d+\)$")
DATE_DMY = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")
DATE_YEAR = re.compile(r"^(\d{4})$")
DATE_YEAR_RANGE = re.compile(r"^(\d{4})-(\d{4})?$")


def pdf_to_lines(pdf_path: Path) -> list[str]:
    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
        try:
            subprocess.run(
                ["pdftotext", "-layout", str(pdf_path), tmp.name],
                check=True,
                capture_output=True,
            )
        except FileNotFoundError:
            sys.exit("Error: `pdftotext` not found. Install poppler-utils.")
        except subprocess.CalledProcessError as exc:
            sys.exit(f"pdftotext failed: {exc.stderr.decode(errors='replace')}")
        return Path(tmp.name).read_text(encoding="utf-8").splitlines()


def section_eight(lines: list[str]) -> list[str]:
    """Slice out section VIII, skipping its table-of-contents entry."""
    starts = [i for i, ln in enumerate(lines) if SECTION_HEADING.search(ln)]
    if not starts:
        sys.exit("Could not locate section VIII in the document")
    start = starts[-1]

    # The per-country reduced-rate annexes that follow open with an all-caps
    # country name on its own line.
    upper_names = {name.upper() for name in COUNTRY_TO_CODE}
    for i in range(start + 1, len(lines)):
        if lines[i].strip() in upper_names:
            return lines[start:i]
    return lines[start:]


def group_fields(tokens: list[str]) -> list[str]:
    """Join tokens around a standalone '|' so '1 | 6 | 12' stays one column."""
    fields: list[str] = []
    expect_join = False
    for tok in tokens:
        if tok == "|":
            expect_join = True
            continue
        if expect_join and fields:
            fields[-1] += " | " + tok
            expect_join = False
        else:
            fields.append(tok)
    return fields


def parse_date(tok: str) -> tuple[str, str] | None:
    m = DATE_DMY.match(tok)
    if m:
        day, month, year = m.groups()
        return f"{year}-{month}-{day}", "day"
    for pattern in (DATE_YEAR, DATE_YEAR_RANGE):
        m = pattern.match(tok)
        if m:
            return f"{m.group(1)}-01-01", "year"
    return None


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip().splitlines()[-3].strip())

    lines = section_eight(pdf_to_lines(Path(sys.argv[1])))

    rows: dict[str, list[dict]] = {}
    warnings: list[str] = []
    current: str | None = None

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        if stripped in COUNTRY_TO_CODE:
            current = COUNTRY_TO_CODE[stripped]
            rows.setdefault(current, [])
            continue

        # Footnote markers ("01-09-2020 (1)") would shift the columns.
        tokens = [t for t in stripped.split() if not FOOTNOTE.match(t)]
        if not tokens:
            continue

        parsed = parse_date(tokens[0])
        if parsed is None:
            continue
        if current is None:
            warnings.append(f"row outside any country block: {stripped!r}")
            continue

        iso, precision = parsed
        fields = group_fields(tokens[1:])
        if len(fields) < 2:
            warnings.append(f"{current} {iso}: too few columns: {stripped!r}")
            continue

        entry: dict = {"from": iso, "date_precision": precision}
        raw_standard = fields[1]
        try:
            entry["standard"] = float(raw_standard)
        except ValueError:
            # A few member states ran two standard rates side by side
            # (Ireland 1983-1985). Record both rather than picking one.
            try:
                entry["standard"] = None
                entry["standard_values"] = [
                    float(v.strip()) for v in raw_standard.split("|")
                ]
                entry["ambiguous"] = True
            except ValueError:
                warnings.append(
                    f"{current} {iso}: unparsable standard rate "
                    f"{raw_standard!r} in row {stripped!r}"
                )
                continue

        rows[current].append(entry)

    # Keep only rows where the standard rate actually moves — the booklet also
    # lists dates on which just the reduced rates changed.
    periods: dict[str, list[dict]] = {}
    for code, entries in rows.items():
        entries.sort(key=lambda e: e["from"])
        kept: list[dict] = []
        for entry in entries:
            if kept and (
                kept[-1].get("standard") == entry.get("standard")
                and kept[-1].get("standard_values") == entry.get("standard_values")
            ):
                continue
            kept.append(entry)
        periods[code] = kept

    missing = sorted(set(COUNTRY_TO_CODE.values()) - {c for c, v in periods.items() if v})
    for code in missing:
        warnings.append(f"{code}: no rows extracted")

    print(
        json.dumps(
            {
                "source": "ec-taxud-booklet-2021-06",
                "source_url": (
                    "https://taxation-customs.ec.europa.eu/system/files/"
                    "2021-06/vat_rates_en.pdf"
                ),
                "rate_type": "standard",
                "periods": periods,
                "warnings": warnings,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    total = sum(len(v) for v in periods.values())
    print(
        f"{len(periods)} member states, {total} change points, "
        f"{len(warnings)} warnings",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
