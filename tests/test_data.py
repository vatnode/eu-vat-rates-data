import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_data import validate_current, validate_history  # noqa: E402


class DatasetTests(unittest.TestCase):
    def test_current_dataset(self):
        data = json.loads((ROOT / "data/eu-vat-rates-data.json").read_text(encoding="utf-8"))
        self.assertEqual([], validate_current(data))

    def test_identifiers_come_from_the_curated_file(self):
        data = json.loads((ROOT / "data/eu-vat-rates-data.json").read_text(encoding="utf-8"))
        curated = json.loads((ROOT / "scripts/identifiers.json").read_text(encoding="utf-8"))
        self.assertEqual(set(curated), set(data["rates"]))
        for code, rate in data["rates"].items():
            self.assertEqual(curated[code], rate["identifiers"], code)

    def test_standard_rate_history(self):
        data = json.loads((ROOT / "data/eu-vat-rates-history.json").read_text(encoding="utf-8"))
        self.assertEqual([], validate_history(data))


if __name__ == "__main__":
    unittest.main()
