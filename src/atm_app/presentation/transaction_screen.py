import logging
import tkinter as tk
from tkinter import ttk

from ..shared.errors import AccountAccessError, BusinessError, Code, MESSAGES
from ..application import AccountManager
from ..domain.validation import check_deposit, check_transfer, check_withdrawal, parse_amount, validate_account_number
from .deposit_screen import DepositScreen
from .login_screen import LoginScreen
from .menu_screen import MenuScreen
from ..application.screen_data import ScreenData
from .transfer_screen import TransferScreen
from .withdrawal_screen import WithdrawalScreen
from .widgets import configure_theme, lock_form, reset_transaction

logger = logging.getLogger(__name__)


class TransactionScreen:
    """OP-01..07: GUI controller and authentication-session boundary.

    Account changes run on the Tk event loop. A processing guard and a per-form
    generation prevent double clicks and stale callbacks from replaying a request.
    """

    def __init__(self, root: tk.Tk, account_manager: AccountManager, *, processing_delay_ms: int = 180):
        self.root = root
        self.account_manager = account_manager
        self.screen_data = ScreenData()
        self.processing = False
        self.current_view = "login"
        self.last_error_code: Code | None = None
        self._generation = 0
        self._logout_pending = False
        self._close_pending = False
        self._pending_warning = ""
        self._processing_delay_ms = max(0, processing_delay_ms)
        self._after_id = None
        configure_theme(root)
        root.title("ATM 제어 및 관리 시스템")
        root.geometry("1000x780")
        root.minsize(940, 740)

        header = ttk.Frame(root, style="Header.TFrame", padding=(30, 20))
        header.pack(fill="x")
        ttk.Label(header, text="ATM  |  가상 계좌 시뮬레이터", style="Header.TLabel").pack(anchor="w")
        self.session_var = tk.StringVar(master=root, value="계좌에 로그인하여 시작하세요")
        ttk.Label(header, textvariable=self.session_var, style="HeaderSmall.TLabel").pack(anchor="w", pady=(5, 0))
        footer = ttk.Frame(root, style="App.TFrame", padding=(30, 0, 30, 14))
        footer.pack(side="bottom", fill="x")
        ttk.Label(footer, text="학습용 가상 거래 · 실제 은행 연동 없음", style="Footer.TLabel").pack(side="left")
        ttk.Label(footer, text="앱 재시작 시 초기 계좌로 복구됩니다", style="Footer.TLabel").pack(side="right")
        host = ttk.Frame(root, style="App.TFrame", padding=(28, 20))
        host.pack(fill="both", expand=True)
        host.rowconfigure(0, weight=1)
        host.columnconfigure(0, weight=1)
        self.login_screen = LoginScreen(host, self)
        self.menu_screen = MenuScreen(host, self)
        self.deposit_screen = DepositScreen(host, self)
        self.withdrawal_screen = WithdrawalScreen(host, self)
        self.transfer_screen = TransferScreen(host, self)
        self.screens = {
            "login": self.login_screen,
            "menu": self.menu_screen,
            "deposit": self.deposit_screen,
            "withdrawal": self.withdrawal_screen,
            "transfer": self.transfer_screen,
        }
        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<Return>", self._on_return)
        root.bind("<Escape>", self._on_escape)
        root.report_callback_exception = self._handle_callback_exception
        self.login_screen.show()

    def show_page(self, name: str) -> None:
        self.current_view = name
        self.screens[name].tkraise()
        number = self.screen_data.account_number
        self.session_var.set(f"이용 계좌  {number}" if number else "계좌에 로그인하여 시작하세요")

    def request_login(self, account_number: str, password: str) -> None:
        """OP-01. PIN is never retained in ScreenData or controller attributes."""
        if self.processing or self.current_view != "login":
            return
        self.login_screen.pin_var.set("")
        self.last_error_code = None
        try:
            if not validate_account_number(account_number) or not self.login_screen.validate_pin(password):
                raise BusinessError(Code.INVALID_FORMAT)
            result = Code(self.account_manager.authenticate(account_number, password))
            if result == Code.SUCCESS:
                self.screen_data.set_account_number(account_number)
                self.login_screen.account_var.set("")
                self.login_screen.warning_var.set("")
                self._refresh_balance()
            elif result == Code.ACCOUNT_BLOCKED:
                self.end_session()
                self.last_error_code = result
                self.login_screen.show_warning(MESSAGES[result])
            else:
                self.last_error_code = result
                self.login_screen.show_warning(MESSAGES[result])
        except BusinessError as exc:
            self.last_error_code = exc.code
            self.login_screen.show_warning(str(exc))
        except Exception as exc:
            self._unexpected_error(exc)

    def _require_session(self) -> tuple[str, int]:
        number = self.screen_data.get_account_number()
        if number is None:
            raise AccountAccessError(Code.NOT_AUTHENTICATED)
        return number, self.account_manager.get_balance(number)

    def select_menu(self, menu: str) -> None:
        """OP-02. Cancelling clears input without reloading account data."""
        if self.processing:
            return
        if menu == "exit":
            self.end_session()
            return
        try:
            self._require_session()
            if menu not in {"menu", "deposit", "withdrawal", "transfer"}:
                self._refresh_balance()
                self.menu_screen.warning_var.set("메뉴에서 이용할 거래를 선택해 주세요.")
                return
            self._generation += 1
            for screen in self._financial_screens():
                reset_transaction(screen)
            self.screen_data.set_transaction_input("", "", "")
            self.last_error_code = None
            self._refresh_balance()
            if menu != "menu":
                self.screen_data.set_transaction_input(menu, "", "")
                self.screens[menu].show()
        except AccountAccessError as exc:
            self._end_with_warning(exc.code)
        except Exception as exc:
            self._unexpected_error(exc)

    def request_deposit(self, amount_text: str) -> None:
        """OP-03."""
        self._request_transaction("deposit", amount_text)

    def request_withdrawal(self, amount_text: str) -> None:
        """OP-04."""
        self._request_transaction("withdrawal", amount_text)

    def request_transfer(self, target_account_number: str, amount_text: str) -> None:
        """OP-05."""
        self._request_transaction("transfer", amount_text, target_account_number)

    def _request_transaction(self, kind: str, amount_text: str, target: str = "") -> None:
        if self.processing:
            return
        screen = self.screens[kind]
        try:
            number, balance = self._require_session()
            if self.current_view != kind or screen.stage != "input":
                return
            self.last_error_code = None
            self.screen_data.set_transaction_input(kind, amount_text, target)
            if kind == "transfer" and (not validate_account_number(target) or target == number):
                raise BusinessError(Code.INVALID_TARGET)
            amount = parse_amount(amount_text)
            if kind == "deposit":
                if not screen.validate_amount(amount_text):
                    raise BusinessError(Code.INVALID_AMOUNT)
                if not screen.validate_limit(amount):
                    raise BusinessError(Code.LIMIT_EXCEEDED)
                check_deposit(amount, balance)
            elif kind == "withdrawal":
                if not screen.validate_unit(amount):
                    raise BusinessError(Code.INVALID_UNIT)
                if not screen.validate_limit(amount):
                    raise BusinessError(Code.LIMIT_EXCEEDED)
                check_withdrawal(amount, balance)
            else:
                check_transfer(number, target, amount, balance)
            self.processing = True
            screen.stage = "processing"
            if kind == "deposit":
                screen.show_progress()
            else:
                screen.message_var.set("출금 중입니다." if kind == "withdrawal" else "가상 이체 중입니다.")
                lock_form(screen, True)
            self._after_id = self.root.after(
                self._processing_delay_ms,
                lambda generation=self._generation: self._complete_transaction(kind, number, amount, target, generation),
            )
        except AccountAccessError as exc:
            self._end_with_warning(exc.code)
        except BusinessError as exc:
            self.last_error_code = exc.code
            self._present_result(kind, str(exc), False, 0)
        except Exception as exc:
            self.processing = False
            self._unexpected_error(exc)

    def _complete_transaction(self, kind: str, number: str, amount: int, target: str, generation: int) -> None:
        self._after_id = None
        try:
            current_number, _ = self._require_session()
            if generation != self._generation or current_number != number:
                raise AccountAccessError(Code.NOT_AUTHENTICATED)
            if kind == "deposit":
                approved = self.account_manager.deposit(number, amount)
            elif kind == "withdrawal":
                approved = self.account_manager.withdraw(number, amount)
            else:
                approved = self.account_manager.transfer(number, target, amount)
            if not approved:
                self.last_error_code = Code.PROCESSING_FAILED
            self._refresh_balance()
            message = {
                "deposit": "입금이 완료되었습니다.",
                "withdrawal": "출금이 완료되었습니다.",
                "transfer": "이체가 완료되었습니다. (송신 계좌만 차감하는 가상 거래)",
            }[kind] if approved else MESSAGES[Code.PROCESSING_FAILED]
            self._present_result(kind, message, approved, amount)
            if kind == "withdrawal" and approved:
                self.withdrawal_screen.show_receipt_prompt()
        except AccountAccessError as exc:
            self._end_with_warning(exc.code)
        except Exception as exc:
            self._unexpected_error(exc)
        finally:
            self.processing = False
            lock_form(self.screens[kind], False)
            if self._logout_pending or self._close_pending:
                warning = self._pending_warning
                close_pending = self._close_pending
                self._logout_pending = False
                self._pending_warning = ""
                self.end_session()
                if warning:
                    self.login_screen.show_warning(warning)
                if close_pending:
                    self.root.destroy()

    def _present_result(self, kind: str, message: str, success: bool, amount: int) -> None:
        number, balance = self._require_session()
        self.screen_data.set_shown_balance(balance)
        self.screen_data.set_transaction_input("", "", "")
        screen = self.screens[kind]
        screen.result_success = success
        screen.result_balance = balance
        screen.result_amount = amount
        screen.show_result(message)

    def _financial_screens(self):
        return self.deposit_screen, self.withdrawal_screen, self.transfer_screen

    def end_session(self) -> None:
        """OP-06. An already approved request finishes before logout or close."""
        if self.processing:
            self._logout_pending = True
            return
        self._generation += 1
        self.screen_data.clear()
        for screen in self._financial_screens():
            reset_transaction(screen)
        self.menu_screen.clear()
        self.login_screen.show()

    def _refresh_balance(self) -> None:
        """OP-07. Always read the account; the displayed copy is never authority."""
        number = self.screen_data.get_account_number()
        if number is None:
            return
        balance = self.account_manager.get_balance(number)
        self.screen_data.set_shown_balance(balance)
        self.menu_screen.show(balance)

    def _end_with_warning(self, code: Code) -> None:
        self.last_error_code = code
        if self.processing:
            self._pending_warning = MESSAGES[code]
        self.end_session()
        if not self.processing:
            self.login_screen.show_warning(MESSAGES[code])

    def _unexpected_error(self, exc: BaseException) -> None:
        # Log only the exception type, never credentials or arbitrary exception text.
        logger.error("ATM callback failed (%s)", type(exc).__name__)
        self._end_with_warning(Code.UNEXPECTED_ERROR)

    def _handle_callback_exception(self, exc_type, exc, traceback) -> None:
        self._unexpected_error(exc)

    def _on_return(self, event=None):
        if self.processing:
            return "break"
        if self.current_view == "login":
            self.login_screen.submit()
        elif self.current_view in {"deposit", "withdrawal", "transfer"}:
            screen = self.screens[self.current_view]
            if screen.stage == "input":
                screen.confirm_button.invoke()
            elif screen.stage == "result" and screen.continue_button.instate(("!disabled",)):
                self.select_menu("menu")
        return "break"

    def _on_escape(self, event=None):
        if self.processing:
            return "break"
        if self.current_view in {"deposit", "withdrawal", "transfer"}:
            self.select_menu("menu")
        elif self.current_view == "menu":
            self.end_session()
        else:
            self.login_screen.show()
        return "break"

    def close(self) -> None:
        if self.processing:
            self._close_pending = True
            self._logout_pending = True
            return
        self.end_session()
        self.root.destroy()
