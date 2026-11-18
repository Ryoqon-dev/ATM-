import unittest

from atm_app.domain.constants import MAX_BALANCE
from atm_app.domain import VirtualAccount
from atm_app.shared.errors import AccountAccessError, BusinessError

A = "100100000001"


class VirtualAccountTests(unittest.TestCase):
    def account(self, balance=500_000):
        return VirtualAccount(A, "0123", balance)

    def test_credit_and_debit(self):
        account = self.account()
        account.credit(30_000)
        account.debit(20_000)
        self.assertEqual(account.balance, 510_000)

    def test_invalid_mutations_are_atomic(self):
        account = self.account()
        for amount in (0, -1, True, 1.5, "1", MAX_BALANCE + 1):
            for action in (account.credit, account.debit):
                with self.subTest(amount=amount, action=action.__name__), self.assertRaises(BusinessError):
                    action(amount)
                self.assertEqual(account.balance, 500_000)
        with self.assertRaises(BusinessError):
            account.debit(500_001)
        self.assertEqual(account.balance, 500_000)

    def test_failed_count_always_matches_block_state(self):
        account = self.account()
        for count in range(1, 8):
            self.assertEqual(account.increment_failed_count(), min(count, 5))
            self.assertEqual(account.blocked, account.failed_count == 5)
        account.block()
        self.assertEqual(account.failed_count, 5)
        with self.assertRaises(AccountAccessError):
            account.reset_failed_count()

    def test_blocked_domain_rejects_balance_changes(self):
        account = self.account()
        account.block()
        for action in (account.credit, account.debit):
            with self.assertRaises(AccountAccessError):
                action(10_000)
        self.assertEqual(account.balance, 500_000)

    def test_pin_not_in_repr_and_account_number_is_readonly(self):
        account = self.account()
        self.assertTrue(account.matches_pin("0123"))
        self.assertFalse(account.matches_pin("123"))
        self.assertNotIn("0123", repr(account))
        with self.assertRaises(AttributeError):
            account.account_number = "100100000002"

    def test_invalid_initial_state(self):
        for kwargs in (dict(balance=True), dict(balance=-1), dict(balance=MAX_BALANCE + 1),
                       dict(failed_count=5, blocked=False), dict(failed_count=0, blocked=True),
                       dict(failed_count=True), dict(blocked=1)):
            arguments = dict(account_number=A, password="0123", balance=500_000)
            arguments.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                VirtualAccount(**arguments)
