"""Tests drive our own Tk widgets and event loop, without external UI automation."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
import unittest
from unittest.mock import patch

from atm_app.infrastructure.bootstrap import DEFAULT_SEED, load_seed
from atm_app.shared.errors import Code
from atm_app.application import AccountManager
from atm_app.application.screen_data import ScreenData
from atm_app.presentation.transaction_screen import TransactionScreen
from atm_app.presentation.widgets import choose_receipt

A, B, TARGET = "100100000001", "100100000002", "999999999999"


class GuiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            probe = tk.Tk()
            probe.withdraw()
            probe.update_idletasks()
            probe.destroy()
        except tk.TclError as exc:
            raise unittest.SkipTest(f"Tk display unavailable: {exc}")

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.manager = AccountManager(load_seed())
        self.app = TransactionScreen(self.root, self.manager, processing_delay_ms=0)
        self.root.update_idletasks()

    def tearDown(self):
        try:
            if self.root.winfo_exists():
                self.root.update_idletasks()
                self.root.destroy()
        except tk.TclError:
            pass

    def login(self, number=A, pin="0123"):
        self.app.login_screen.account_var.set(number)
        self.app.login_screen.pin_var.set(pin)
        self.app.login_screen.login_button.invoke()

    def transact(self, kind, amount, target=TARGET):
        self.app.select_menu(kind)
        screen = self.app.screens[kind]
        screen.amount_var.set(amount)
        if kind == "transfer":
            screen.target_var.set(target)
        screen.confirm_button.invoke()
        self.root.update()
        return screen

    def assert_clean(self):
        self.assertEqual(asdict(self.app.screen_data), asdict(ScreenData()))
        self.assertEqual(self.app.current_view, "login")
        self.assertEqual(self.app.login_screen.account_var.get(), "")
        self.assertEqual(self.app.login_screen.pin_var.get(), "")
        self.assertEqual(self.app.menu_screen.balance_var.get(), "")
        for screen in self.app._financial_screens():
            for variable in (screen.amount_var, screen.target_var, screen.balance_var,
                             screen.result_balance_var, screen.result_detail_var, screen.receipt_var):
                self.assertEqual(variable.get(), "")

    def test_TC_L01_login_displays_balance(self):
        self.login()
        self.assertEqual(self.app.current_view, "menu")
        self.assertEqual(self.app.screen_data.account_number, A)
        self.assertEqual(self.app.menu_screen.balance_var.get(), "500,000원")
        self.assertEqual(self.app.login_screen.pin_var.get(), "")

    def test_TC_L04_fifth_failure_returns_clean_login(self):
        for count in range(1, 6):
            self.login(pin="9999")
            self.assertEqual(self.manager.accounts[0].failed_count, count)
            self.assertEqual(self.app.current_view, "login")
        self.assertTrue(self.manager.accounts[0].blocked)
        self.assert_clean()
        self.assertEqual(self.app.last_error_code, Code.ACCOUNT_BLOCKED)
        self.assertIn("차단", self.app.login_screen.warning_var.get())

    def test_TC_W04_full_withdrawal_and_receipt_choice(self):
        self.login()
        screen = self.transact("withdrawal", "500000")
        self.assertTrue(screen.result_success)
        self.assertEqual(screen.result_balance_var.get(), "0원")
        self.assertEqual(self.manager.get_balance(A), 0)
        self.assertIn("명세표", screen.receipt_var.get())
        self.assertTrue(screen.continue_button.instate(("disabled",)))
        choose_receipt(screen, True)
        self.assertIn("실제 인쇄", screen.receipt_var.get())
        self.assertTrue(screen.continue_button.instate(("!disabled",)))

    def test_TC_S01_logout_cleans_hidden_widgets_and_session(self):
        self.login()
        for screen in self.app._financial_screens():
            screen.amount_var.set("20000")
            screen.target_var.set(TARGET)
            screen.result_balance_var.set("500000")
            screen.result_detail_var.set("previous data")
        self.app.screen_data.set_transaction_input("transfer", "20000", TARGET)
        self.app.end_session()
        self.assert_clean()
        self.assertEqual(self.manager.get_balance(A), 500_000)

    def test_TC_S02_logout_then_login_keeps_balance(self):
        self.login()
        self.transact("deposit", "1")
        self.app.end_session()
        self.login()
        self.assertEqual(self.app.menu_screen.balance_var.get(), "500,001원")

    def test_TC_S03_new_process_restores_seed(self):
        root = Path(__file__).resolve().parents[1]
        seed_before = DEFAULT_SEED.read_bytes()
        child_env = dict(os.environ, PYTHONPATH=str(root / "src"))
        mutate = "from atm_app.infrastructure.bootstrap import load_seed; from atm_app.application import AccountManager; m=AccountManager(load_seed()); m.deposit('100100000001',1); m.accounts[0].block(); assert m.accounts[0].balance==500001"
        subprocess.run([sys.executable, "-c", mutate], cwd=root, env=child_env, check=True, capture_output=True)
        inspect = "import json; from atm_app.infrastructure.bootstrap import load_seed; a=load_seed()[0]; print(json.dumps([a.balance,a.failed_count,a.blocked]))"
        result = subprocess.run([sys.executable, "-c", inspect], cwd=root, env=child_env, check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [500_000, 0, False])
        self.assertEqual(DEFAULT_SEED.read_bytes(), seed_before)

    def test_TC_S04_cancel_keeps_balance_and_clears_input(self):
        self.login()
        self.app.select_menu("transfer")
        screen = self.app.transfer_screen
        screen.amount_var.set("20000")
        screen.target_var.set(TARGET)
        screen.cancel_button.invoke()
        self.assertEqual(self.app.current_view, "menu")
        self.assertEqual(screen.amount_var.get(), "")
        self.assertEqual(screen.target_var.get(), "")
        self.assertEqual(self.manager.get_balance(A), 500_000)

    def test_TC_Q01_unauthenticated_controller_requests(self):
        for callback in (lambda: self.app.request_deposit("1"), lambda: self.app.request_withdrawal("10000"), lambda: self.app.request_transfer(TARGET, "1")):
            callback()
            self.assertEqual(self.app.current_view, "login")
            self.assertEqual(self.app.last_error_code, Code.NOT_AUTHENTICATED)
        self.assertEqual(self.manager.get_balance(A), 500_000)

    def test_TC_Q03_double_click_updates_once(self):
        self.login()
        self.app.select_menu("deposit")
        screen = self.app.deposit_screen
        screen.amount_var.set("10000")
        with patch.object(self.manager, "deposit", wraps=self.manager.deposit) as deposit:
            screen.confirm_button.invoke()
            self.assertTrue(self.app.processing)
            self.assertTrue(screen.confirm_button.instate(("disabled",)))
            screen.confirm_button.invoke()
            self.app.request_deposit("10000")
            self.root.update()
            self.assertEqual(deposit.call_count, 1)
            screen.confirm_button.invoke()  # hidden old form cannot replay after success
            self.root.update()
            self.assertEqual(deposit.call_count, 1)
        self.assertEqual(self.manager.get_balance(A), 510_000)
        self.assertEqual(screen.stage, "result")

    def test_TC_Q05_pin_masked_and_never_retained(self):
        self.assertEqual(self.app.login_screen.pin_entry.cget("show"), "●")
        self.login(pin="9999")
        self.assertEqual(self.app.login_screen.pin_var.get(), "")
        self.login()
        self.assertNotIn("password", asdict(self.app.screen_data))
        self.assertNotIn("pin", asdict(self.app.screen_data))
        self.app.end_session()
        self.assert_clean()

    def test_TC_Q07_unexpected_service_error_is_safe(self):
        self.login()
        with patch.object(self.manager, "deposit", side_effect=RuntimeError("0123-test-private")):
            with self.assertLogs("atm_app.presentation.transaction_screen", level="ERROR") as captured:
                self.transact("deposit", "10000")
        self.assertEqual(self.app.last_error_code, Code.UNEXPECTED_ERROR)
        self.assertEqual(self.manager.get_balance(A), 500_000)
        self.assertNotIn("0123", " ".join(captured.output))
        self.assert_clean()

    def test_TC_Q08_display_copy_cannot_approve_withdrawal(self):
        self.login()
        self.app.select_menu("withdrawal")
        self.app.screen_data.shown_balance = 9_999_999_999
        self.app.request_withdrawal("510000")
        self.root.update()
        self.assertFalse(self.app.withdrawal_screen.result_success)
        self.assertEqual(self.app.last_error_code, Code.INSUFFICIENT_FUNDS)
        self.assertEqual(self.manager.get_balance(A), 500_000)
        self.assertEqual(self.app.withdrawal_screen.result_balance_var.get(), "500,000원")

    def test_sequential_demo_matches_document(self):
        self.login()
        self.transact("deposit", "30000")
        self.transact("withdrawal", "20000")
        choose_receipt(self.app.withdrawal_screen, False)
        self.transact("transfer", "10000")
        self.assertEqual(self.manager.get_balance(A), 500_000)
        self.assertEqual(self.manager.get_balance(B), 2_000_000)
        self.app.end_session()
        self.assert_clean()

    def test_invalid_gui_values_cancel_without_mutation(self):
        self.login()
        for kind, value, code in (("deposit", "0", Code.INVALID_AMOUNT),
                                  ("deposit", "1000001", Code.LIMIT_EXCEEDED),
                                  ("withdrawal", "15000", Code.INVALID_UNIT),
                                  ("withdrawal", "1010000", Code.LIMIT_EXCEEDED),
                                  ("transfer", "500001", Code.INSUFFICIENT_FUNDS)):
            with self.subTest(kind=kind, value=value):
                screen = self.transact(kind, value)
                self.assertFalse(screen.result_success)
                self.assertEqual(self.app.last_error_code, code)
                self.assertEqual(self.manager.get_balance(A), 500_000)

    def test_logout_waits_for_accepted_transaction(self):
        self.login()
        self.app.select_menu("deposit")
        self.app.request_deposit("1")
        self.app.end_session()
        self.assertTrue(self.app.processing)
        self.root.update()
        self.assertEqual(self.manager.get_balance(A), 500_001)
        self.assert_clean()

    def test_stale_queued_request_is_rejected(self):
        self.login()
        self.app.select_menu("deposit")
        self.app.request_deposit("1")
        self.app._generation += 1
        self.root.update()
        self.assertEqual(self.manager.get_balance(A), 500_000)
        self.assert_clean()

    def test_close_waits_for_transaction_and_cleans_data(self):
        self.login()
        self.app.select_menu("deposit")
        self.app.request_deposit("1")
        self.app.close()
        self.root.update()
        self.assertEqual(self.manager.get_balance(A), 500_001)
        self.assertEqual(asdict(self.app.screen_data), asdict(ScreenData()))

    def test_menu_and_keyboard_shortcuts(self):
        self.login()
        self.app.select_menu("unknown")
        self.assertEqual(self.app.current_view, "menu")
        self.app.select_menu("deposit")
        self.app._on_escape()
        self.assertEqual(self.app.current_view, "menu")
        self.app._on_escape()
        self.assert_clean()

    def test_minimum_window_controls_fit(self):
        self.root.geometry("940x740")
        self.root.deiconify()
        self.root.update()
        for entry in (self.app.login_screen.account_entry, self.app.login_screen.pin_entry):
            self.assertTrue(entry.winfo_ismapped())
            self.assertGreater(entry.winfo_height(), 25)
        self.login()
        for kind in ("menu", "deposit", "withdrawal", "transfer"):
            self.app.select_menu(kind)
            self.root.update_idletasks()
            screen = self.app.screens[kind]
            buttons = list(screen.buttons.values()) + [screen.end_button] if kind == "menu" else [screen.confirm_button, screen.cancel_button]
            if kind != "menu":
                buttons.append(screen.amount_entry)
                if kind == "transfer":
                    buttons.append(screen.target_entry)
            for button in buttons:
                with self.subTest(screen=kind, widget=str(button)):
                    self.assertTrue(button.winfo_ismapped())
                    self.assertGreater(button.winfo_width(), 30)
                    self.assertGreater(button.winfo_height(), 20)
                    self.assertLessEqual(button.winfo_rooty() + button.winfo_height(), screen.winfo_rooty() + screen.winfo_height())

    def test_transfer_target_is_checked_before_amount(self):
        self.login()
        self.app.select_menu("transfer")
        self.app.request_transfer(A, "invalid")
        self.assertEqual(self.app.last_error_code, Code.INVALID_TARGET)
        self.assertEqual(self.manager.get_balance(A), 500_000)

    def test_receipt_result_controls_fit_minimum_window(self):
        self.root.geometry("940x740")
        self.root.deiconify()
        self.login()
        screen = self.transact("withdrawal", "10000")
        self.root.update_idletasks()
        for widget in (screen.receipt_frame, screen.receipt_actions, screen.result_actions):
            self.assertTrue(widget.winfo_ismapped())
            self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(), screen.winfo_rooty() + screen.winfo_height())

    def test_blocked_account_during_queued_request_cannot_mutate(self):
        self.login()
        self.app.select_menu("deposit")
        self.app.request_deposit("1")
        self.manager.accounts[0].block()
        self.root.update()
        self.assertEqual(self.manager.accounts[0].balance, 500_000)
        self.assert_clean()
