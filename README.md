# eu-vat-rates-data

[![Last updated](https://img.shields.io/github/last-commit/vatnode/eu-vat-rates-data?path=data%2Feu-vat-rates-data.json&label=last%20updated)](https://github.com/vatnode/eu-vat-rates-data/commits/main/data/eu-vat-rates-data.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Canonical data source — VAT rates for **45 European countries**, including all EU-27 member states plus Norway, Switzerland, the United Kingdom, and more. Sourced from the European Commission TEDB (EU rates) and supplemented with non-EU European countries. Checked daily, committed automatically when rates change.

This repository contains **only the data and the update script**. Language-specific packages are published separately:

| Language | Package | Install |
|---|---|---|
| JavaScript / TypeScript | [npm](https://www.npmjs.com/package/eu-vat-rates-data) | `npm install eu-vat-rates-data` |
| Python | [PyPI](https://pypi.org/project/eu-vat-rates-data/) | `pip install eu-vat-rates-data` |
| PHP | [Packagist](https://packagist.org/packages/vatnode/eu-vat-rates-data) | `composer require vatnode/eu-vat-rates-data` |
| Go | [pkg.go.dev](https://pkg.go.dev/github.com/vatnode/eu-vat-rates-data-go) | `go get github.com/vatnode/eu-vat-rates-data-go` |
| Ruby | [RubyGems](https://rubygems.org/gems/eu_vat_rates_data) | `gem install eu_vat_rates_data` |

---

## Need live VIES validation?

This dataset gives you VAT **rates** for free, offline. The language packages also include offline **format checks** against country-specific regex patterns. None of this calls VIES — format checks only verify the shape of a VAT number, not whether it actually exists.

For **live VIES validation** — confirming a VAT ID is real, pulling the registered company name and address, and getting the VIES consultation number as your reference for the check — there's **[vatnode](https://vatnode.dev?ref=rates-readme-data)**:

- Live VIES validation, with national-database fallback when VIES is down
- Registered company name, address, registration date
- VIES consultation number for compliance and audit trails
- Webhooks for VAT status changes
- Official [MCP server](https://www.npmjs.com/package/vatnode-mcp) so AI agents (Claude, Cursor, ChatGPT) can validate VAT IDs directly
- Free tier — no credit card needed

```bash
curl https://api.vatnode.dev/v1/vat/IE6388047V \
  -H "Authorization: Bearer YOUR_API_KEY"
```

[**See what the API adds →**](https://vatnode.dev/vat-rates?ref=rates-readme-data#beyond-rates) · [Get a free API key](https://vatnode.dev/login?ref=rates-readme-data)

---

## Direct JSON access

No package needed — use the JSON directly via CDN:

```
# jsDelivr CDN (cached):
https://cdn.jsdelivr.net/gh/vatnode/eu-vat-rates-data@main/data/eu-vat-rates-data.json

# Raw GitHub (always latest commit):
https://raw.githubusercontent.com/vatnode/eu-vat-rates-data/main/data/eu-vat-rates-data.json
```

```js
const res = await fetch(
  'https://cdn.jsdelivr.net/gh/vatnode/eu-vat-rates-data@main/data/eu-vat-rates-data.json'
)
const { rates } = await res.json()
console.log(rates.DE.standard) // 19
```

---

## Data structure

```ts
interface VatRate {
  country:       string        // "Finland"
  currency:      string        // "EUR" (or "DKK", "GBP", …)
  eu_member:     boolean       // true for EU-27, false for non-EU
  vat_name:      string        // "Arvonlisävero" — official name in primary local language
  vat_abbr:      string        // "ALV" — short abbreviation used locally
  standard:      number        // 25.5
  reduced:       number[]      // [10, 13.5] — sorted ascending
  super_reduced: number | null // null when not applicable
  parking:       number | null // null when not applicable
  format:        string        // "FI + 8 digits" — human-readable VAT number format
  pattern:       string        // "^FI\\d{8}$" — regex for format validation, always present
}
```

### Example JSON entry

```json
{
  "version": "2026-03-31",
  "source": "European Commission TEDB",
  "publisher": { "name": "vatnode.dev", "url": "https://vatnode.dev" },
  "rates": {
    "FI": {
      "country": "Finland",
      "currency": "EUR",
      "eu_member": true,
      "vat_name": "Arvonlisävero",
      "vat_abbr": "ALV",
      "standard": 25.5,
      "reduced": [10, 13.5],
      "super_reduced": null,
      "parking": null,
      "format": "FI + 8 digits",
      "pattern": "^FI\\d{8}$"
    }
  }
}
```

---

## Standard rate history

`data/eu-vat-rates-history.json` is a second dataset: every change to the **standard** VAT rate in each of the EU-27, back to 1967, with the date each rate took effect. Useful when you need the rate that applied on a past date — recalculating an old invoice, an audit, a backdated correction.

```
https://cdn.jsdelivr.net/gh/vatnode/eu-vat-rates-data@main/data/eu-vat-rates-history.json
https://raw.githubusercontent.com/vatnode/eu-vat-rates-data/main/data/eu-vat-rates-history.json
```

```json
{
  "rate_type": "standard",
  "publisher": { "name": "vatnode.dev", "url": "https://vatnode.dev" },
  "history": {
    "DE": {
      "country": "Germany",
      "periods": [
        { "from": "2007-01-01", "to": "2020-06-30", "standard": 19.0, "source": "ec-taxud-booklet-2021-06" },
        { "from": "2020-07-01", "to": "2020-12-31", "standard": 16.0, "source": "de-zweites-corona-steuerhilfegesetz-2020" },
        { "from": "2021-01-01", "to": null, "standard": 19.0, "source": "de-zweites-corona-steuerhilfegesetz-2020" }
      ]
    }
  }
}
```

Every period carries a `source`, resolvable through the file's `sources` block:

- **`ec-taxud-booklet-2021-06`** — section VIII, "The evolution of VAT rates applicable in the Member States", of the Commission's booklet _VAT rates applied in the Member States of the European Union_ (final edition 06/2021, discontinued in favour of TEDB). Transcribed once by `scripts/parse_booklet_history.py` into the frozen `data/history-pre-tedb.json`, which CI never rewrites. Supplies everything up to the end of 2016.
- **`tedb`** — the Taxes in Europe Database, queried date by date. Takes over from **2017-01-01**. TEDB does answer for 2016, but its record for that year is flattened: it reports Greece at 24% for all of 2016, when the rise from 23% only took effect on 1 June. The booklet dates that change correctly, so the handover sits at 2017, where the two sources agree on every member state.
- **National legislation** — a small set of hand-entered corrections in `data/history-corrections.json`, each naming the law it comes from. Applied last, also frozen against CI.

Where the two Commission sources overlap (2017 to mid-2021) they are compared, and any disagreement is reported by `scripts/build_history.py` rather than quietly resolved. They currently agree everywhere.

The corrections file exists because the Commission's own record has gaps and errors. Two are known:

- **Germany's cut from 19% to 16% for 1 July – 31 December 2020** appears in neither TEDB nor the booklet, though Ireland's temporary cut over almost the same window appears in both.
- **Estonia's rates before 2009** are wrong in the booklet, which dates them by year and gives 10% from 1991 and 18% from 1993. The Estonian Ministry of Finance records 7% from 10 January 1991, 10% from 1 January 1992, and 18% from 20 June 1992 — the day of the kroon currency reform, set by decree no. 035 of the Currency Reform Committee. Those replace the booklet's account.

Absence from this dataset is evidence about the Commission's record, not about national law — if you find another gap, open an issue with the legislation and it goes in the corrections file.

Two fields need care:

- `date_precision` says whether `from` is an exact date. Every period currently published is `"day"`. The field exists because the booklet dates a few early changes by year alone; those cases have been researched against national sources and replaced, and any that reappear would be marked `"year"` with `from` set to `YYYY-01-01` as a placeholder, not a claim about the day.
- `standard` is `null` where a member state ran two standard rates at once — Ireland did, from 1983 to 1985. Both values are in `standard_values`, and `ambiguous` is set.

Reduced, super-reduced and parking rates are **not** in the history file; only their current values are published, in `eu-vat-rates-data.json`.

Which rate applies to a given supply also depends on the place-of-supply and time-of-supply rules in force at the time. This dataset does not model those.

---

## Update frequency

How the daily check works, and what changed when: [vatnode.dev/data](https://vatnode.dev/data?ref=rates-readme-data).

- Checked against the EC TEDB SOAP API: **daily at 07:00 UTC**, committed on any change
- Committed on every run (version date always updated)
- Full audit trail: `git log -- data/eu-vat-rates-data.json`

To run locally:

```bash
git clone https://github.com/vatnode/eu-vat-rates-data.git
pip install requests
python3 scripts/update.py
```

---

## Keeping rates current

The JSON in this repository is updated automatically — use it directly via CDN if you need always-current data without any setup:

```
https://cdn.jsdelivr.net/gh/vatnode/eu-vat-rates-data@main/data/eu-vat-rates-data.json
https://raw.githubusercontent.com/vatnode/eu-vat-rates-data/main/data/eu-vat-rates-data.json
```

Language-specific packages bundle a snapshot of this data at publish time. A new package version is released automatically whenever rates change, but installed packages do not update themselves. If you use a package and need rates to stay current, set up [Renovate](https://renovatebot.com) or [Dependabot](https://docs.github.com/en/code-security/dependabot) — they will open a PR automatically when a new version is published.

---

## Covered countries

**EU-27** (checked daily against EC TEDB, updated on any change):

`AT` `BE` `BG` `CY` `CZ` `DE` `DK` `EE` `ES` `FI` `FR` `GR` `HR` `HU` `IE` `IT` `LT` `LU` `LV` `MT` `NL` `PL` `PT` `RO` `SE` `SI` `SK`

**Non-EU Europe** (manually maintained):

`AD` `AL` `BA` `CH` `GB` `GE` `IS` `LI` `MC` `MD` `ME` `MK` `NO` `RS` `TR` `UA` `XK`

45 countries total.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT

If you find this useful, a ⭐ on GitHub is appreciated.
