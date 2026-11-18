import unittest

from atm_app.infrastructure.bootstrap import load_seed
from atm_app.domain.constants import MAX_BALANCE
from atm_app.domain import VirtualAccount
from atm_app.shared.errors import AccountAccessError, Code
from atm_app.application import AccountManager

A, B, TARGET = "100100000001", "100100000002", "999999999999"


class AccountManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = AccountManager(load_seed())
        self.account = self.manager.accounts[0]

    def test_TC_L02_format_errors_do_not_increment(self):
        for pin in ("", "123", "12345", "12a3", "１２３４"):
            self.assertEqual(self.manager.authenticate(A, pin), Code.INVALID_FORMAT)
        self.assertEqual(self.account.failed_count, 0)

    def test_TC_L03_four_failures_still_active(self):
        for count in range(1, 5):
            self.assertEqual(self.manager.authenticate(A, "9999"), Code.INVALID_CREDENTIALS)
            self.assertEqual(self.account.failed_count, count)
            self.assertFalse(self.account.blocked)

    def test_TC_L05_correct_pin_cannot_unblock(self):
        self.account.block()
        self.assertEqual(self.manager.authenticate(A, "0123"), Code.ACCOUNT_BLOCKED)
        self.assertEqual(self.account.failed_count, 5)

    def test_TC_L06_success_resets_count(self):
        self.manager.authenticate(A, "9999")
        self.manager.authenticate(A, "9999")
        self.assertEqual(self.manager.authenticate(A, "0123"), Code.SUCCESS)
        self.assertEqual(self.account.failed_count, 0)

    def test_TC_L07_unknown_account_does_not_change_other_accounts(self):
        self.assertEqual(self.manager.authenticate("888888888888", "0123"), Code.INVALID_CREDENTIALS)
        self.assertTrue(all(account.failed_count == 0 for account in self.manager.accounts))

    def test_TC_L08_failures_are_per_account(self):
        for _ in range(4):
            self.manager.authenticate(A, "9999")
        self.assertEqual(self.manager.authenticate(B, "5678"), Code.SUCCESS)
        self.assertEqual(self.account.failed_count, 4)
        self.assertEqual(self.manager.accounts[1].failed_count, 0)

    def test_TC_D02_maximum_deposit(self):
        self.assertTrue(self.manager.deposit(A, 1_000_000))
        self.assertEqual(self.account.balance, 1_500_000)

    def test_TC_D03_deposit_limit_rejection(self):
        self.assertFalse(self.manager.deposit(A, 1_000_001))
        self.assertEqual(self.account.balance, 500_000)

    def test_TC_D04_minimum_deposit(self):
        self.assertTrue(self.manager.deposit(A, 1))
        self.assertEqual(self.account.balance, 500_001)

    def test_TC_D05_balance_ceiling(self):
        account = VirtualAccount(A, "0123", MAX_BALANCE)
        manager = AccountManager([account])
        self.assertFalse(manager.deposit(A, 1))
        self.assertEqual(account.balance, MAX_BALANCE)

    def test_TC_W01_withdrawal_unit(self):
        self.assertFalse(self.manager.withdraw(A, 15_000))
        self.assertEqual(self.account.balance, 500_000)

    def test_TC_W02_withdrawal_limit_inclusive(self):
        self.assertTrue(self.manager.withdraw(B, 1_000_000))
        self.assertEqual(self.manager.get_balance(B), 1_000_000)

    def test_TC_W03_withdrawal_over_limit(self):
        self.assertFalse(self.manager.withdraw(B, 1_010_000))
        self.assertEqual(self.manager.get_balance(B), 2_000_000)

    def test_TC_W05_insufficient_balance(self):
        self.assertFalse(self.manager.withdraw(A, 510_000))
        self.assertEqual(self.account.balance, 500_000)

    def test_TC_W06_invalid_withdrawal_values(self):
        for amount in (0, -10_000, "10000", 10_000.0, True, None):
            self.assertFalse(self.manager.withdraw(A, amount))
        self.assertEqual(self.account.balance, 500_000)

    def test_TC_T01_transfer_is_debit_only(self):
        self.assertTrue(self.manager.transfer(A, TARGET, 20_000))
        self.assertEqual(self.account.balance, 480_000)
        self.assertEqual(len(self.manager.accounts), 3)

    def test_TC_T02_insufficient_transfer_balance(self):
        self.assertFalse(self.manager.transfer(A, TARGET, 500_001))
        self.assertEqual(self.account.balance, 500_000)

    def test_TC_T03_reject_invalid_target(self):
        for target in (A, "12345678901", "1234567890123", "문자", "", None, []):
            self.assertFalse(self.manager.transfer(A, target, 20_000))
        self.assertEqual(self.account.balance, 500_000)

    def test_TC_T04_reject_invalid_transfer_amount(self):
        for amount in (0, -1, "10000", 1.5, True, None):
            self.assertFalse(self.manager.transfer(A, TARGET, amount))
        self.assertEqual(self.account.balance, 500_000)

    def test_TC_T05_transfer_has_no_million_won_cap(self):
        self.assertTrue(self.manager.transfer(B, TARGET, 1_500_000))
        self.assertEqual(self.manager.get_balance(B), 500_000)

    def test_TC_T06_local_recipient_is_unchanged(self):
        self.assertTrue(self.manager.transfer(A, B, 20_000))
        self.assertEqual(self.account.balance, 480_000)
        self.assertEqual(self.manager.get_balance(B), 2_000_000)

    def test_TC_Q02_blocked_service_requests(self):
        self.account.block()
        self.assertFalse(self.manager.deposit(A, 1))
        self.assertFalse(self.manager.withdraw(A, 10_000))
        self.assertFalse(self.manager.transfer(A, TARGET, 1))
        self.assertEqual(self.account.balance, 500_000)

    def test_TC_Q04_service_rechecks_rules(self):
        for amount in (-1, True, 1_000_001):
            self.assertFalse(self.manager.deposit(A, amount))
        self.assertEqual(self.account.balance, 500_000)

    def test_unknown_lookup_is_error_not_zero(self):
        with self.assertRaises(AccountAccessError):
            self.manager.get_balance(TARGET)
        self.assertFalse(self.manager.deposit(TARGET, 1))
        self.assertFalse(self.manager.withdraw(TARGET, 10_000))
        self.assertFalse(self.manager.transfer(TARGET, A, 1))

    def test_duplicate_account_collection_is_rejected(self):
        with self.assertRaises(ValueError):
            AccountManager([self.account, self.account])
