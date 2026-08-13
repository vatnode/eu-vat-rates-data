# Changelog

Rate changes themselves are not listed here — they land automatically whenever the
European Commission TEDB publishes them, and every change is visible in the commit
history of [`data/eu-vat-rates-data.json`](https://github.com/vatnode/eu-vat-rates-data/commits/main/data/eu-vat-rates-data.json).
This file records changes to the data format, the update pipeline, and corrections
to hand-maintained fields.

## 2026-08-13

- **added:** `data/eu-vat-rates-history.json` — standard rate history for the EU-27 back to 1967, with the effective date of every change. Built from section VIII of the archived TAXUD booklet up to the end of 2016, and TEDB from 2017-01-01. See the README section "Standard rate history".
- **added:** `data/history-corrections.json` — hand-entered changes the Commission's sources omit or get wrong, each citing a national source. Two entries: Germany's cut to 16% for 1 July – 31 December 2020, which appears in neither TEDB nor the booklet; and Estonia's pre-2009 rates (7% from 10.01.1991, 10% from 01.01.1992, 18% from 20.06.1992 per the Estonian Ministry of Finance), replacing the booklet's year-only and incorrect 10%-from-1991 / 18%-from-1993 account.
- **changed:** every published period now carries an exact `from` date. The booklet's year-only entries were the only exception and have been researched against national sources.
- **added:** `scripts/parse_booklet_history.py` (one-off transcription of the booklet), `scripts/backfill_tedb_history.py` (one-off TEDB backfill), `scripts/build_history.py` (merge and cross-check), `scripts/update_history.py` (daily append). The daily workflow now runs the last of these; `data/history-pre-tedb.json` and `data/history-corrections.json` are frozen and never rewritten by CI.

## 2026-04-25

- **fix:** Corrected Sweden (SE) VAT number regex — was `^SE\d{12}$`, now correctly requires the mandatory `01` suffix: `^SE\d{10}01$`.
