#!/usr/bin/env python3
"""Create factual GitHub release notes from two current-data snapshots."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

RATE_FIELDS = ("standard", "reduced", "super_reduced", "parking")
METADATA_FIELDS = ("country", "currency", "eu_member", "vat_name", "vat_abbr", "format", "pattern")


def display(value: object) -> str:
    if value is None:
        return "not applicable"
    if isinstance(value, list):
        return ", ".join(f"{item:g}%" for item in value) or "none"
    return f"{value:g}%" if isinstance(value, (int, float)) else str(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    old = json.loads(args.old.read_text(encoding="utf-8"))
    new = json.loads(args.new.read_text(encoding="utf-8"))
    old_rates, new_rates = old.get("rates", {}), new.get("rates", {})
    codes = sorted(code for code in set(old_rates) | set(new_rates) if old_rates.get(code) != new_rates.get(code))
    if not codes:
        raise SystemExit("No rate changes found")

    lines = [
        f"Published: **{new['version']}**",
        "",
        "## Affected jurisdictions",
        "",
    ]
    for code in codes:
        before, after = old_rates.get(code), new_rates.get(code)
        name = (after or before).get("country", code)
        lines.append(f"### {name} (`{code}`)")
        lines.append("")
        if before is None:
            lines.append("- Jurisdiction added to the dataset.")
        elif after is None:
            lines.append("- Jurisdiction removed from the dataset.")
        else:
            for field in RATE_FIELDS:
                if before.get(field) != after.get(field):
                    lines.append(f"- `{field}`: {display(before.get(field))} → {display(after.get(field))}")
            for field in METADATA_FIELDS:
                if before.get(field) != after.get(field):
                    lines.append(f"- `{field}` metadata: `{before.get(field)}` → `{after.get(field)}`")
        lines.append("")
    lines.extend([
        "## Source and effective date",
        "",
        f"- Primary source: {new.get('source', 'official source')}",
        f"- Detected and published: {new['version']}",
        "- The current snapshot does not encode effective dates for every rate type. Check the official source and the standard-rate history before applying a rate to a past transaction.",
        "",
        "## Packages and audit trail",
        "",
        "Language packages synchronize after the canonical dataset update: [npm](https://www.npmjs.com/package/eu-vat-rates-data), [PyPI](https://pypi.org/project/eu-vat-rates-data/), [Packagist](https://packagist.org/packages/vatnode/eu-vat-rates-data), [Go](https://pkg.go.dev/github.com/vatnode/eu-vat-rates-data-go), and [RubyGems](https://rubygems.org/gems/eu_vat_rates_data).",
        "",
        "See the [commit history](https://github.com/vatnode/eu-vat-rates-data/commits/main/data/eu-vat-rates-data.json) and [standard-rate history](https://github.com/vatnode/eu-vat-rates-data/blob/main/data/eu-vat-rates-history.json).",
    ])
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    title = f"VAT rates update — {', '.join(codes)}"
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"title={title}\n")
            handle.write(f"tag=data-{new['version']}\n")
    print(title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
