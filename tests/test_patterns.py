import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PatternTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((ROOT / "data/eu-vat-rates-data.json").read_text(encoding="utf-8"))
        cls.rates = data["rates"]

    def assert_pattern(self, code, accepted, rejected):
        pattern = re.compile(self.rates[code]["pattern"])
        for vat_id in accepted:
            with self.subTest(vat_id=vat_id):
                self.assertIsNotNone(pattern.match(vat_id))
        for vat_id in rejected:
            with self.subTest(vat_id=vat_id):
                self.assertIsNone(pattern.match(vat_id))

    # The first and last characters of a Spanish VAT number may not both be digits.
    def test_es(self):
        self.assert_pattern(
            "ES",
            accepted=[
                "ESA15075062",  # legal entity, digit control
                "ESB12345674",  # legal entity, digit control
                "ESQ2818015F",  # public body, letter control
                "ES12345678Z",  # individual (DNI)
                "ESX1234567L",  # foreign national (NIE)
            ],
            rejected=[
                "ES123456789",
                "ES1234567A",
                "ESA1234567",
                "ESA123456789",
            ],
        )


if __name__ == "__main__":
    unittest.main()
