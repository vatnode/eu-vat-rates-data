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

For **live VIES validation** — confirming a VAT ID is real, pulling the registered company name and address, and getting the VIES consultation number as your reference for the check — there's **[vatnode](https://vatnode.dev)**:

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

[**Get a free API key →**](https://vatnode.dev/login?ref=rates-readme-data)

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

## Need to validate VAT numbers?

This repository provides **VAT rates** only. If you also need to **validate EU VAT numbers** against the official VIES database, check out [vatnode.dev](https://vatnode.dev) — a simple REST API with a free tier.

---

## Changelog

### 2026-04-25
- **fix:** Corrected Sweden (SE) VAT number regex — was `^SE\d{12}$`, now correctly requires the mandatory `01` suffix: `^SE\d{10}01$`.

---

## License

MIT

If you find this useful, a ⭐ on GitHub is appreciated.
