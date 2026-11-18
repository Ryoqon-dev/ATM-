import unittest

from atm_app.shared.errors import BusinessError, Code
from atm_app.domain.validation import parse_amount, validate_account_number, validate_pin


class ValidationTests(unittest.TestCase):
    def test_TC_D01_invalid_amount_strings(self):
        for text in ("", "0", "-1", "+1", "1.5", " ", " 1", "1 ", "1,000", "문자", "12345678901", "１２３４", "١٢٣", None, True, 1):
            with self.subTest(value=text), self.assertRaises(BusinessError) as error:
                parse_amount(text)
            self.assertEqual(error.exception.code, Code.INVALID_AMOUNT)

    def test_valid_amounts_and_leading_zeroes(self):
        for text, value in (("1", 1), ("0001", 1), ("1000000", 1_000_000), ("9999999999", 9_999_999_999)):
            self.assertEqual(parse_amount(text), value)

    def test_account_format_is_ascii_and_exact(self):
        self.assertTrue(validate_account_number("000000000001"))
        for value in ("", "10010000001", "1001000000001", "１００１０００００００１", "100100000001\n", 100100000001, [], None):
            self.assertFalse(validate_account_number(value))

    def test_pin_leading_zero_and_whitespace(self):
        self.assertTrue(validate_pin("0123"))
        for value in ("123", "12345", "１２３４", "0123\n", " 0123", 123, None):
            self.assertFalse(validate_pin(value))
