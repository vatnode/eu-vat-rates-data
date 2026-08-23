# Contributing to VATNode VAT Rates

Thank you for helping keep the dataset accurate and auditable.

## Report an incorrect or missing rate

Use the relevant GitHub issue template and include the jurisdiction, country code, rate type, published and claimed values, effective date, official source URL, and any product or territory limitation.

News articles, aggregator pages, and search-result snippets can help locate a change, but they are not accepted as the final authority when an official tax-authority, government, or European Commission source is available.

## Propose a jurisdiction

Open a “Missing jurisdiction or rate” issue. Explain why it belongs in European VAT coverage and provide its code, currency, current rates, local VAT name and abbreviation, VAT-number format, and official sources.

## Generated-data workflow

`data/eu-vat-rates-data.json`, `data/history-tedb.json`, and `data/eu-vat-rates-history.json` are generated. Do not edit them directly.

- Current EU rates are fetched by `scripts/update.py` from TEDB.
- Frozen historical input and cited corrections live in `data/history-pre-tedb.json` and `data/history-corrections.json`.
- `scripts/update_history.py` updates the generated history.
- The daily workflow commits generated files only after validation.

For a non-EU correction, update the maintained source values in `scripts/update.py`, include the official citation in the pull request, regenerate the dataset, and describe the effective date.

## Run validation

```bash
python3 scripts/validate_data.py
python3 -m unittest discover tests
```

To exercise the source updater without writing files, install `requests` and run `python3 scripts/update.py --dry-run` and `python3 scripts/update_history.py --dry-run`. The dry run requires network access; validation and tests run offline.

Keep pull requests focused. Schema changes must document compatibility impact and update the JSON Schema, README contract, tests, and package types where applicable.
