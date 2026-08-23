# European VAT Rates — JSON and packages

**Accurate European VAT rates, automatically updated from official sources. JSON + packages for JavaScript, Python, PHP, Go and Ruby.** Covers 45 European jurisdictions: every EU member state plus 18 non-EU jurisdictions.

[![Validate data](https://github.com/vatnode/eu-vat-rates-data/actions/workflows/test.yml/badge.svg)](https://github.com/vatnode/eu-vat-rates-data/actions/workflows/test.yml)
[![Update status](https://github.com/vatnode/eu-vat-rates-data/actions/workflows/update.yml/badge.svg)](https://github.com/vatnode/eu-vat-rates-data/actions/workflows/update.yml)
[![Last data update](https://img.shields.io/github/last-commit/vatnode/eu-vat-rates-data?path=data%2Feu-vat-rates-data.json&label=last%20data%20update)](https://github.com/vatnode/eu-vat-rates-data/commits/main/data/eu-vat-rates-data.json)
[![npm downloads](https://img.shields.io/npm/dw/eu-vat-rates-data)](https://www.npmjs.com/package/eu-vat-rates-data)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

EU rates come from the European Commission Taxes in Europe Database (TEDB). The source is checked daily; normalized, validated data is published automatically. See the [methodology](https://vatnode.dev/data), [rate history](data/eu-vat-rates-history.json), and [VAT Rates website](https://vatnode.dev/vat-rates).

## Quick start

### Direct JSON

```text
https://cdn.jsdelivr.net/gh/vatnode/eu-vat-rates-data@main/data/eu-vat-rates-data.json
```

```js
const response = await fetch(
  'https://cdn.jsdelivr.net/gh/vatnode/eu-vat-rates-data@main/data/eu-vat-rates-data.json'
)
const { rates } = await response.json()

console.log(rates.DE.standard) // 19
console.log(rates.FI.reduced)  // [10, 13.5]
```

jsDelivr is the recommended cached CDN endpoint. [Raw GitHub](https://raw.githubusercontent.com/vatnode/eu-vat-rates-data/main/data/eu-vat-rates-data.json) serves the file directly from the latest commit and is useful when GitHub origin semantics are preferred over CDN caching.

For reproducible builds, replace `@main` with a commit SHA. Package users should pin a package version or lockfile.

### JavaScript / TypeScript

```bash
npm install eu-vat-rates-data
```

```ts
import { getRate, getStandardRate, validateFormat } from 'eu-vat-rates-data'

getStandardRate('DE')            // 19
getRate('FI')?.reduced            // [10, 13.5]
validateFormat('DE123456789')     // true: format only, not VIES status
```

### Python

```bash
pip install eu-vat-rates-data
```

```python
from eu_vat_rates_data import get_rate, get_standard_rate, validate_format

get_standard_rate("DE")          # 19.0
get_rate("FI")["reduced"]       # [10.0, 13.5]
validate_format("DE123456789")   # True: format only, not VIES status
```

### PHP

```bash
composer require vatnode/eu-vat-rates-data
```

```php
use vatnode\EuVatRates\EuVatRates;

EuVatRates::getStandardRate('DE');          // 19.0
EuVatRates::getRate('FI')['reduced'];       // [10.0, 13.5]
EuVatRates::validateFormat('DE123456789');  // true: format only
```

### Go

```bash
go get github.com/vatnode/eu-vat-rates-data-go
```

```go
package main

import (
  "fmt"
  euvatrates "github.com/vatnode/eu-vat-rates-data-go"
)

func main() {
  standard, _ := euvatrates.GetStandardRate("DE")
  fi, _ := euvatrates.GetRate("FI")
  fmt.Println(standard, fi.Reduced)
  fmt.Println(euvatrates.ValidateFormat("DE123456789")) // format only
}
```

### Ruby

```bash
gem install eu_vat_rates_data
```

```ruby
require "eu_vat_rates_data"

EuVatRatesData.get_standard_rate("DE")       # 19.0
EuVatRatesData.get_rate("FI")["reduced"]   # [10.0, 13.5]
EuVatRatesData.valid_format?("DE123456789") # true: format only
```

Using this dataset in production or an open-source project? **A GitHub star helps other developers discover it.**

## Package ecosystem

| Ecosystem | Package | Install | Repository / registry |
|---|---|---|---|
| Direct JSON | `eu-vat-rates-data.json` | No install | [CDN](https://cdn.jsdelivr.net/gh/vatnode/eu-vat-rates-data@main/data/eu-vat-rates-data.json) · [repository](https://github.com/vatnode/eu-vat-rates-data) |
| JavaScript / TypeScript | `eu-vat-rates-data` | `npm install eu-vat-rates-data` | [repository](https://github.com/vatnode/eu-vat-rates-data-js) · [npm](https://www.npmjs.com/package/eu-vat-rates-data) |
| Python | `eu-vat-rates-data` | `pip install eu-vat-rates-data` | [repository](https://github.com/vatnode/eu-vat-rates-data-python) · [PyPI](https://pypi.org/project/eu-vat-rates-data/) |
| PHP | `vatnode/eu-vat-rates-data` | `composer require vatnode/eu-vat-rates-data` | [repository](https://github.com/vatnode/eu-vat-rates-data-php) · [Packagist](https://packagist.org/packages/vatnode/eu-vat-rates-data) |
| Go | `github.com/vatnode/eu-vat-rates-data-go` | `go get github.com/vatnode/eu-vat-rates-data-go` | [repository](https://github.com/vatnode/eu-vat-rates-data-go) · [pkg.go.dev](https://pkg.go.dev/github.com/vatnode/eu-vat-rates-data-go) |
| Ruby | `eu_vat_rates_data` | `gem install eu_vat_rates_data` | [repository](https://github.com/vatnode/eu-vat-rates-data-ruby) · [RubyGems](https://rubygems.org/gems/eu_vat_rates_data) |

All packages bundle a snapshot for offline use. The canonical repository for source data, schema, provenance, and history is this repository.

## Usage and distribution

The dataset is available in six distribution formats: direct JSON plus five language ecosystems. Public package and CDN request statistics are recorded weekly in [`stats/downloads.csv`](stats/downloads.csv). CDN requests are HTTP requests, **not unique users**.

### CDN usage

jsDelivr publishes usage statistics for the GitHub CDN endpoint. This repository records weekly and monthly request totals automatically so developers do not need to use the stats API directly. Use `@main` for automatically refreshed data or a commit SHA for reproducible builds.

## Data contract

The machine-readable contract is [`schema/eu-vat-rates-data.schema.json`](schema/eu-vat-rates-data.schema.json).

```ts
interface VatRate {
  country: string
  currency: string                 // ISO 4217
  eu_member: boolean
  vat_name: string
  vat_abbr: string
  standard: number                 // percentage points, e.g. 25.5
  reduced: number[]                // sorted ascending; [] when none
  super_reduced: number | null
  parking: number | null
  format: string                   // human-readable VAT ID format
  pattern: string                  // regex format check
}
```

Top-level `version` is an ISO date, `source` names the primary source, and `rates` is keyed by country code. Codes use ISO 3166-1 alpha-2 where available; Greece is stored as `GR` although VAT IDs use the EU prefix `EL`. `XI` identifies Northern Ireland for VAT purposes and `XK` is the user-assigned code used for Kosovo.

Fields documented by the current schema are stable. The registry packages currently use date-based versions for data releases; an ordinary rate update does not change the schema. Removing a field or changing its meaning is breaking and must not ship as an ordinary date release: it requires a documented migration and a coordinated opt-in compatibility boundary across packages. Adding an optional field is non-breaking; package types are updated with the data release.

## What changed and when?

- [Current-data commit history](https://github.com/vatnode/eu-vat-rates-data/commits/main/data/eu-vat-rates-data.json) shows every published snapshot.
- [`data/eu-vat-rates-history.json`](data/eu-vat-rates-history.json) contains EU-27 standard-rate periods back to 1967, including effective dates and source identifiers.
- [GitHub Releases](https://github.com/vatnode/eu-vat-rates-data/releases) summarize meaningful rate changes. Daily checks with no rate change do not create releases.
- [`CHANGELOG.md`](CHANGELOG.md) records schema, pipeline, and correction changes rather than duplicating generated rate history.

The history dataset covers standard rates only. Reduced, super-reduced, and parking rate history is not currently published.

## Data provenance

- **EU-27:** European Commission TEDB is the primary current-data source and is checked daily at 07:00 UTC.
- **Non-EU jurisdictions:** maintained manually from national sources, with official sources preferred and required for new corrections. Per-entry source URLs are not yet embedded in the current dataset; treat that as a provenance limitation.
- **Normalization:** TEDB's `EL` code is normalized to `GR`; numeric rates, rate types, currencies, membership, and VAT-number format metadata use one stable shape.
- **Validation:** CI checks the JSON structure, country counts and codes, rate ranges, regex syntax, sorted reduced rates, and history continuity before publication.
- **Publication:** data is committed automatically after a successful source check. Language packages publish only when actual rate values change.

No dataset can decide which VAT treatment applies to a transaction. Product or service category, customer status, location, place-of-supply rules, exemptions, and effective dates may change the result. The format helpers check only the shape of a VAT number; they do not confirm registration through VIES. This dataset is for software integration and is not tax or legal advice.

Full methodology and limitations: [vatnode.dev/data](https://vatnode.dev/data).

## Coverage

**EU-27:** `AT` `BE` `BG` `CY` `CZ` `DE` `DK` `EE` `ES` `FI` `FR` `GR` `HR` `HU` `IE` `IT` `LT` `LU` `LV` `MT` `NL` `PL` `PT` `RO` `SE` `SI` `SK`

**Non-EU and special VAT jurisdictions:** `AD` `AL` `BA` `CH` `GB` `GE` `IS` `LI` `MC` `MD` `ME` `MK` `NO` `RS` `TR` `UA` `XI` `XK`

## Factual feature comparison

| Capability | VATNode dataset | Hand-maintained constants | Runtime tax API |
|---|---:|---:|---:|
| Automatic official-source checks | Yes, daily for EU-27 | Depends on maintainer | Provider-dependent |
| Direct JSON | Yes | Sometimes | Usually no |
| Offline use | Yes | Yes | No |
| Standard + reduced rate types | Yes | Implementation-dependent | Provider-dependent |
| Standard-rate history | Yes, EU-27 | Rarely | Provider-dependent |
| TypeScript types | Yes, npm package | Implementation-dependent | SDK-dependent |
| Five language packages | Yes | Usually separate projects | SDK-dependent |

This compares distribution approaches, not named competitors; capabilities of individual projects and services vary.

## Contributing and support

Found an incorrect rate or missing jurisdiction? Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and open the matching issue template with the country, rate type, effective date, claimed value, and official source URL. Do not edit generated JSON directly.

For vulnerability reports and the support boundary, see [`SECURITY.md`](SECURITY.md).

## License

[MIT](LICENSE)
