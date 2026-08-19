#!/usr/bin/env python3
"""
Update EU VAT rates from European Commission TEDB SOAP web service.

Usage:
    python3 scripts/update.py [--dry-run]

Options:
    --dry-run   Show diff without writing to file

Dependencies:
    pip install requests
"""

import json
import sys
import datetime
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    sys.exit("Error: 'requests' not installed. Run: pip install requests")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# EU member states use ISO 3166-1 alpha-2 codes (EL for Greece per EU convention)
EU_MEMBER_STATES = [
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL",
    "ES", "FI", "FR", "HR", "HU", "IE", "IT", "LT", "LU",
    "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
]

# EU uses "EL" for Greece; we normalise to ISO 3166-1 alpha-2 in the output
TEDB_TO_ISO: dict[str, str] = {"EL": "GR"}

COUNTRY_NAMES: dict[str, str] = {
    "AT": "Austria",      "BE": "Belgium",       "BG": "Bulgaria",
    "CY": "Cyprus",       "CZ": "Czech Republic", "DE": "Germany",
    "DK": "Denmark",      "EE": "Estonia",        "GR": "Greece",
    "ES": "Spain",        "FI": "Finland",        "FR": "France",
    "HR": "Croatia",      "HU": "Hungary",        "IE": "Ireland",
    "IT": "Italy",        "LT": "Lithuania",      "LU": "Luxembourg",
    "LV": "Latvia",       "MT": "Malta",          "NL": "Netherlands",
    "PL": "Poland",       "PT": "Portugal",       "RO": "Romania",
    "SE": "Sweden",       "SI": "Slovenia",       "SK": "Slovakia",
}

# EU-27 countries that do not use EUR as their currency
CURRENCY: dict[str, str] = {
    "CZ": "CZK", "DK": "DKK", "HU": "HUF",
    "PL": "PLN", "RO": "RON", "SE": "SEK",
}

# Local name of the VAT tax for each EU-27 member state.
# Multi-language countries: most widely used official language chosen.
# BE → Dutch (largest language group), CH → German (largest), LU → French (legislation language).
# Local abbreviation of the VAT tax name for each country.
VAT_ABBR: dict[str, str] = {
    "AD": "IGI",   "AL": "TVSH",  "AT": "USt",   "BA": "PDV",   "BE": "BTW",
    "BG": "ДДС",   "CH": "MWST",  "CY": "ΦΠΑ",   "CZ": "DPH",   "DE": "MwSt",
    "DK": "moms",  "EE": "km",    "ES": "IVA",   "FI": "ALV",   "FR": "TVA",
    "GB": "VAT",   "GE": "დღგ",   "GR": "ΦΠΑ",   "HR": "PDV",   "HU": "ÁFA",
    "IE": "VAT",   "IS": "VSK",   "IT": "IVA",   "LI": "MWST",  "LT": "PVM",
    "LU": "TVA",   "LV": "PVN",   "MC": "TVA",   "MD": "TVA",   "ME": "PDV",
    "MK": "ДДВ",   "MT": "VAT",   "NL": "btw",   "NO": "MVA",   "PL": "VAT",
    "PT": "IVA",   "RO": "TVA",   "RS": "PDV",   "SE": "moms",  "SI": "DDV",
    "SK": "DPH",   "TR": "KDV",   "UA": "ПДВ",   "XI": "VAT",   "XK": "TVSH",
}

VAT_NAMES: dict[str, str] = {
    "AT": "Umsatzsteuer",
    "BE": "Belasting over de toegevoegde waarde",
    "BG": "Данък върху добавената стойност",
    "CY": "Φόρος Προστιθέμενης Αξίας",
    "CZ": "Daň z přidané hodnoty",
    "DE": "Mehrwertsteuer",
    "DK": "Moms",
    "EE": "Käibemaks",
    "ES": "Impuesto sobre el Valor Añadido",
    "FI": "Arvonlisävero",
    "FR": "Taxe sur la valeur ajoutée",
    "GR": "Φόρος Προστιθέμενης Αξίας",
    "HR": "Porez na dodanu vrijednost",
    "HU": "Általános forgalmi adó",
    "IE": "Value Added Tax",
    "IT": "Imposta sul valore aggiunto",
    "LT": "Pridėtinės vertės mokestis",
    "LU": "Taxe sur la valeur ajoutée",
    "LV": "Pievienotās vērtības nodoklis",
    "MT": "Taxxa tal-Valur Miżjud",
    "NL": "Belasting over de toegevoegde waarde",
    "PL": "Podatek od towarów i usług",
    "PT": "Imposto sobre o Valor Acrescentado",
    "RO": "Taxa pe valoarea adăugată",
    "SE": "Mervärdesskatt",
    "SI": "Davek na dodano vrednost",
    "SK": "Daň z pridanej hodnoty",
}

# Human-readable format description for each country's VAT number.
VAT_FORMATS: dict[str, str] = {
    "AD": "1 letter + 6 digits + 1 letter",
    "AL": "1 letter + 8 digits + 1 letter",
    "AT": "ATU + 8 digits",
    "BA": "12 digits",
    "BE": "BE + 0/1 + 9 digits",
    "BG": "BG + 9–10 digits",
    "CH": "CHE-NNN.NNN.NNN (+ MWST/TVA/IVA)",
    "CY": "CY + 8 digits + 1 letter",
    "CZ": "CZ + 8–10 digits",
    "DE": "DE + 9 digits",
    "DK": "DK + 8 digits",
    "EE": "EE + 9 digits",
    "ES": "ES + letter/digit + 7 digits + letter/digit",
    "FI": "FI + 8 digits",
    "FR": "FR + 2 alphanumeric + 9 digits",
    "GB": "GB + 9 digits, 12 digits, or GD/HA + 3 digits",
    "GE": "9 digits",
    "GR": "EL + 9 digits",
    "HR": "HR + 11 digits",
    "HU": "HU + 8 digits",
    "IE": "IE + 7 digits + 1–2 letters",
    "IS": "5–6 digits",
    "IT": "IT + 11 digits",
    "LI": "5 digits",
    "LT": "LT + 9 or 12 digits",
    "LU": "LU + 8 digits",
    "LV": "LV + 11 digits",
    "MC": "FR + 2 alphanumeric + 9 digits",
    "MD": "7 digits",
    "ME": "8 digits",
    "MK": "MK + 13 digits",
    "MT": "MT + 8 digits",
    "NL": "NL + 9 digits + B + 2 digits",
    "NO": "9 digits + MVA",
    "PL": "PL + 10 digits",
    "PT": "PT + 9 digits",
    "RO": "RO + 2–10 digits",
    "RS": "9 digits",
    "SE": "SE + 10 digits + 01",
    "SI": "SI + 8 digits",
    "SK": "SK + 10 digits",
    "TR": "10 digits",
    "UA": "9 digits",
    "XI": "XI + 9 digits, 12 digits, or GD/HA + 3 digits",
    "XK": "9 digits",
}

# Regex pattern string (without slashes) for VAT number validation.
# None for countries without a standardised format.
VAT_PATTERNS: dict[str, Optional[str]] = {
    "AD": r"^[A-Z]\d{6}[A-Z]$",
    "AL": r"^[A-Z]\d{8}[A-Z]$",
    "AT": r"^ATU\d{8}$",
    "BA": r"^\d{12}$",
    "BE": r"^BE[01]\d{9}$",
    "BG": r"^BG\d{9,10}$",
    "CH": r"^CHE-?\d{3}\.?\d{3}\.?\d{3}[ ]?(MWST|TVA|IVA)?$",
    "CY": r"^CY\d{8}[A-Z]$",
    "CZ": r"^CZ\d{8,10}$",
    "DE": r"^DE\d{9}$",
    "DK": r"^DK\d{8}$",
    "EE": r"^EE\d{9}$",
    "ES": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$",
    "FI": r"^FI\d{8}$",
    "FR": r"^FR[A-HJ-NP-Z0-9]{2}\d{9}$",
    "GB": r"^GB(\d{9}|\d{12}|GD\d{3}|HA\d{3})$",
    "GE": r"^\d{9}$",
    "GR": r"^EL\d{9}$",
    "HR": r"^HR\d{11}$",
    "HU": r"^HU\d{8}$",
    "IE": r"^IE\d{7}[A-W][A-IW]?$|^IE\d[A-Z+*]\d{5}[A-W]$",
    "IS": r"^\d{5,6}$",
    "IT": r"^IT\d{11}$",
    "LI": r"^\d{5}$",
    "LT": r"^LT(\d{9}|\d{12})$",
    "LU": r"^LU\d{8}$",
    "LV": r"^LV\d{11}$",
    "MC": r"^FR[A-HJ-NP-Z0-9]{2}\d{9}$",
    "MD": r"^\d{7}$",
    "ME": r"^\d{8}$",
    "MK": r"^MK\d{13}$",
    "MT": r"^MT\d{8}$",
    "NL": r"^NL\d{9}B\d{2}$",
    "NO": r"^\d{9}MVA$",
    "PL": r"^PL\d{10}$",
    "PT": r"^PT\d{9}$",
    "RO": r"^RO\d{2,10}$",
    "RS": r"^\d{9}$",
    "SE": r"^SE\d{10}01$",
    "SI": r"^SI\d{8}$",
    "SK": r"^SK\d{10}$",
    "TR": r"^\d{10}$",
    "UA": r"^\d{9}$",
    "XI": r"^XI(\d{9}|\d{12}|(GD|HA)\d{3})$",
    "XK": r"^\d{9}$",
}

# Non-EU European countries — rates maintained manually.
# Sources: official tax authority websites, Tax Foundation, PWC Tax Summaries (2026).
NON_EU_COUNTRIES: dict[str, dict] = {
    "AD": {"country": "Andorra",              "currency": "EUR", "vat_name": "Impost General Indirecte",                "standard": 4.5,  "reduced": [1.0, 2.5],  "super_reduced": None, "parking": None},
    "AL": {"country": "Albania",              "currency": "ALL", "vat_name": "Tatimi mbi vlerën e shtuar",               "standard": 20.0, "reduced": [6.0, 10.0], "super_reduced": None, "parking": None},
    "BA": {"country": "Bosnia and Herzegovina","currency": "BAM","vat_name": "Porez na dodanu vrijednost",               "standard": 17.0, "reduced": [],           "super_reduced": None, "parking": None},
    "CH": {"country": "Switzerland",          "currency": "CHF", "vat_name": "Mehrwertsteuer",                           "standard": 8.1,  "reduced": [2.6, 3.8],  "super_reduced": None, "parking": None},
    "GB": {"country": "United Kingdom",       "currency": "GBP", "vat_name": "Value Added Tax",                          "standard": 20.0, "reduced": [5.0],       "super_reduced": None, "parking": None},
    "GE": {"country": "Georgia",              "currency": "GEL", "vat_name": "დამატებული ღირებულების გადასახადი",        "standard": 18.0, "reduced": [],           "super_reduced": None, "parking": None},
    "IS": {"country": "Iceland",              "currency": "ISK", "vat_name": "Virðisaukaskattur",                        "standard": 24.0, "reduced": [11.0],      "super_reduced": None, "parking": None},
    "LI": {"country": "Liechtenstein",        "currency": "CHF", "vat_name": "Mehrwertsteuer",                           "standard": 8.1,  "reduced": [2.6, 3.8],  "super_reduced": None, "parking": None},
    "MC": {"country": "Monaco",               "currency": "EUR", "vat_name": "Taxe sur la valeur ajoutée",               "standard": 20.0, "reduced": [5.5, 10.0], "super_reduced": 2.1,  "parking": None},
    "MD": {"country": "Moldova",              "currency": "MDL", "vat_name": "Taxa pe valoarea adăugată",                "standard": 20.0, "reduced": [8.0],       "super_reduced": None, "parking": None},
    "ME": {"country": "Montenegro",           "currency": "EUR", "vat_name": "Porez na dodatu vrijednost",               "standard": 21.0, "reduced": [7.0, 15.0], "super_reduced": None, "parking": None},
    "MK": {"country": "North Macedonia",      "currency": "MKD", "vat_name": "Данок на додадена вредност",               "standard": 18.0, "reduced": [5.0, 10.0], "super_reduced": None, "parking": None},
    "NO": {"country": "Norway",               "currency": "NOK", "vat_name": "Merverdiavgift",                           "standard": 25.0, "reduced": [12.0, 15.0],"super_reduced": None, "parking": None},
    "RS": {"country": "Serbia",               "currency": "RSD", "vat_name": "Porez na dodatu vrednost",                 "standard": 20.0, "reduced": [10.0],      "super_reduced": None, "parking": None},
    "TR": {"country": "Turkey",               "currency": "TRY", "vat_name": "Katma Değer Vergisi",                      "standard": 20.0, "reduced": [1.0, 10.0], "super_reduced": None, "parking": None},
    "UA": {"country": "Ukraine",              "currency": "UAH", "vat_name": "Податок на додану вартість",               "standard": 20.0, "reduced": [7.0, 14.0], "super_reduced": None, "parking": None},
    "XI": {"country": "Northern Ireland",     "currency": "GBP", "vat_name": "Value Added Tax",                          "standard": 20.0, "reduced": [5.0],       "super_reduced": None, "parking": None},
    "XK": {"country": "Kosovo",               "currency": "EUR", "vat_name": "Tatimi mbi Vlerën e Shtuar",               "standard": 18.0, "reduced": [8.0],       "super_reduced": None, "parking": None},
}

DATA_FILE = Path(__file__).parent.parent / "data" / "eu-vat-rates-data.json"

# EC TEDB SOAP service (HTTP per WSDL, redirects to HTTPS)
TEDB_ENDPOINT = "https://ec.europa.eu/taxation_customs/tedb/ws/"
TEDB_NS_MSG   = "urn:ec.europa.eu:taxud:tedb:services:v1:IVatRetrievalService"
TEDB_NS_TYPES = "urn:ec.europa.eu:taxud:tedb:services:v1:IVatRetrievalService:types"
TEDB_SOAP_ACTION = "urn:ec.europa.eu:taxud:tedb:services:v1:VatRetrievalService/RetrieveVatRates"

# rateValueTypeEnum values to skip — these are not real positive VAT rates
SKIP_RATE_TYPES = {"EXEMPTED", "OUT_OF_SCOPE", "NOT_APPLICABLE"}


# ---------------------------------------------------------------------------
# SOAP helpers
# ---------------------------------------------------------------------------

def _build_soap_body(member_states: list[str], situation_on: str) -> bytes:
    states_xml = "\n".join(
        f"        <types:isoCode>{s}</types:isoCode>" for s in member_states
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:v1="{TEDB_NS_MSG}"
    xmlns:types="{TEDB_NS_TYPES}">
  <soapenv:Body>
    <v1:retrieveVatRatesReqMsg>
      <types:memberStates>
{states_xml}
      </types:memberStates>
      <types:situationOn>{situation_on}</types:situationOn>
    </v1:retrieveVatRatesReqMsg>
  </soapenv:Body>
</soapenv:Envelope>"""
    return xml.encode("utf-8")


def _parse_soap_response(xml_bytes: bytes) -> Optional[dict[str, dict]]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        print(f"  XML parse error: {exc}", file=sys.stderr)
        return None

    # Accumulate unique (rate_value_type, rate_value) per country
    # Structure: country_code → { "standard": float, "reduced": set, "super_reduced": set, "parking": set }
    raw: dict[str, dict] = {}

    for el in root.iter():
        local_tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if local_tag != "vatRateResults":
            continue

        country_code: Optional[str] = None
        outer_type:   Optional[str] = None  # STANDARD | REDUCED
        rv_type:      Optional[str] = None  # DEFAULT | REDUCED_RATE | SUPER_REDUCED_RATE | PARKING_RATE | …
        rv_value:     Optional[float] = None

        for child in el:
            ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if ctag == "memberState":
                raw_code = (child.text or "").strip()
                country_code = TEDB_TO_ISO.get(raw_code, raw_code)
            elif ctag == "type":
                outer_type = (child.text or "").strip()
            elif ctag == "rate":
                for gc in child:
                    gctag = gc.tag.split("}")[-1] if "}" in gc.tag else gc.tag
                    if gctag == "type":
                        rv_type = (gc.text or "").strip()
                    elif gctag == "value":
                        try:
                            rv_value = float((gc.text or "").strip())
                        except ValueError:
                            pass

        if not country_code or not outer_type or rv_type is None:
            continue
        if rv_type in SKIP_RATE_TYPES:
            continue
        if rv_value is None or rv_value < 0:
            continue

        entry = raw.setdefault(country_code, {
            "standard":     set(),
            "reduced":      set(),
            "super_reduced": set(),
            "parking":      set(),
        })

        if outer_type == "STANDARD" and rv_type == "DEFAULT":
            entry["standard"].add(rv_value)
        elif outer_type == "REDUCED":
            if rv_type == "REDUCED_RATE":
                entry["reduced"].add(rv_value)
            elif rv_type == "SUPER_REDUCED_RATE":
                entry["super_reduced"].add(rv_value)
            elif rv_type == "PARKING_RATE":
                entry["parking"].add(rv_value)

    if not raw:
        return None

    # Convert sets → canonical scalars / lists
    result: dict[str, dict] = {}
    for code, entry in raw.items():
        std_set = entry["standard"]
        result[code] = {
            # Standard rate: should be a single value per country
            "standard": max(std_set) if std_set else None,
            # Reduced rates: list, sorted ascending
            "reduced": sorted(entry["reduced"]),
            # Super-reduced: smallest value (some countries use multiple for special territories)
            "super_reduced": min(entry["super_reduced"]) if entry["super_reduced"] else None,
            # Parking: smallest value
            "parking": min(entry["parking"]) if entry["parking"] else None,
        }

    return result


def fetch_from_tedb() -> Optional[dict[str, dict]]:
    """Fetch current VAT rates via EC TEDB SOAP web service (official EU source)."""
    today = datetime.date.today().isoformat()
    body = _build_soap_body(EU_MEMBER_STATES, today)
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction":   TEDB_SOAP_ACTION,
    }
    print("  Requesting EC TEDB SOAP service…")
    try:
        resp = requests.post(TEDB_ENDPOINT, data=body, headers=headers, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  TEDB SOAP failed: {exc}", file=sys.stderr)
        return None

    result = _parse_soap_response(resp.content)
    if result:
        print(f"  Got rates for {len(result)} EU member states from TEDB.")
    else:
        print("  TEDB response parsed but yielded no rates.", file=sys.stderr)
    return result


# ---------------------------------------------------------------------------
# Build final dataset
# ---------------------------------------------------------------------------

def build_dataset(eu_rates: dict[str, dict]) -> dict:
    today = datetime.date.today().isoformat()
    rates_out: dict[str, dict] = {}

    # EU-27: rates from TEDB
    for code_tedb in EU_MEMBER_STATES:
        code = TEDB_TO_ISO.get(code_tedb, code_tedb)
        entry = eu_rates.get(code)
        if not entry:
            print(f"  Warning: no data for {code} — skipped.", file=sys.stderr)
            continue
        rates_out[code] = {
            "country":      COUNTRY_NAMES.get(code, code),
            "currency":     CURRENCY.get(code, "EUR"),
            "eu_member":    True,
            "vat_name":     VAT_NAMES.get(code, ""),
            "vat_abbr":     VAT_ABBR.get(code, ""),
            "standard":     entry.get("standard"),
            "reduced":      entry.get("reduced", []),
            "super_reduced": entry.get("super_reduced"),
            "parking":      entry.get("parking"),
            "format":       VAT_FORMATS.get(code, ""),
            "pattern":      VAT_PATTERNS.get(code),
        }

    # Non-EU European countries: hardcoded, updated manually
    for code, entry in NON_EU_COUNTRIES.items():
        rates_out[code] = {
            "country":      entry["country"],
            "currency":     entry["currency"],
            "eu_member":    False,
            "vat_name":     entry["vat_name"],
            "vat_abbr":     VAT_ABBR.get(code, ""),
            "standard":     entry["standard"],
            "reduced":      entry["reduced"],
            "super_reduced": entry["super_reduced"],
            "parking":      entry["parking"],
            "format":       VAT_FORMATS.get(code, ""),
            "pattern":      VAT_PATTERNS.get(code),
        }

    return {
        "version": today,
        "source":  "European Commission TEDB",
        "publisher": {"name": "vatnode.dev", "url": "https://vatnode.dev"},
        "rates":   dict(sorted(rates_out.items())),
    }


# ---------------------------------------------------------------------------
# Diff helpers
# ---------------------------------------------------------------------------

def _diff(old: object, new: object, path: str, lines: list[str]) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(old) | set(new)):
            _diff(old.get(key), new.get(key), f"{path}.{key}", lines)
    else:
        if old != new:
            lines.append(f"  ~ {path}: {old!r} → {new!r}")


def compute_diff(old_dataset: dict, new_dataset: dict) -> list[str]:
    lines: list[str] = []
    _diff(
        old_dataset.get("rates", {}),
        new_dataset.get("rates", {}),
        "rates",
        lines,
    )
    return lines


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _set_github_output(key: str, value: str) -> None:
    """Write a key=value pair to $GITHUB_OUTPUT if running in GitHub Actions."""
    import os
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"{key}={value}\n")


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    print("eu-vat-rates updater")
    print("=" * 40)

    eu_rates = fetch_from_tedb()
    if eu_rates is None:
        print(
            "\nError: EC TEDB SOAP service is unavailable. "
            "Check connectivity and retry.",
            file=sys.stderr,
        )
        _set_github_output("rates_changed", "false")
        return 1

    new_dataset = build_dataset(eu_rates)

    # Load existing data for comparison
    old_dataset: dict = {}
    if DATA_FILE.exists():
        try:
            old_dataset = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  Warning: could not read existing file: {exc}", file=sys.stderr)

    # Check if actual VAT rates changed (ignoring version date)
    rate_diff = compute_diff(old_dataset, new_dataset)
    rates_changed = bool(rate_diff)

    if rate_diff:
        print(f"\nRate changes ({len(rate_diff)} fields):")
        for line in rate_diff:
            print(line)
    else:
        print(f"\nNo rate changes. Updating version date: "
              f"{old_dataset.get('version', 'n/a')} → {new_dataset['version']}")

    _set_github_output("rates_changed", "true" if rates_changed else "false")

    if dry_run:
        print("\n[dry-run] File not updated.")
        return 0

    # Always write the file — version date is always today
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(new_dataset, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated: {DATA_FILE}  (version: {new_dataset['version']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
