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

    def test_standard_rate_history(self):
        data = json.loads((ROOT / "data/eu-vat-rates-history.json").read_text(encoding="utf-8"))
        self.assertEqual([], validate_history(data))


if __name__ == "__main__":
    unittest.main()
