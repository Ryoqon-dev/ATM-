from dataclasses import asdict
import unittest

from atm_app.application.screen_data import ScreenData


class ScreenDataTests(unittest.TestCase):
    def test_store_read_and_clear_all_fields(self):
        data = ScreenData()
        data.set_account_number("100100000001")
        data.set_shown_balance(500_000)
        data.set_transaction_input("transfer", "20000", "999999999999")
        self.assertEqual(data.get_account_number(), "100100000001")
        self.assertEqual(data.amount_text, "20000")
        data.clear()
        data.clear()
        self.assertEqual(asdict(data), asdict(ScreenData()))

    def test_cannot_add_pin_to_session(self):
        data = ScreenData()
        with self.assertRaises(AttributeError):
            data.password = "0123"
