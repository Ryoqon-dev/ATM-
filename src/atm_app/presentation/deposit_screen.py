from tkinter import ttk

from ..domain.constants import DEPOSIT_LIMIT
from ..shared.errors import BusinessError
from ..domain.validation import parse_amount
from .widgets import lock_form, setup_transaction, show_transaction, show_transaction_result


class DepositScreen(ttk.Frame):
    deposit_limit = DEPOSIT_LIMIT

    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame", padding=28)
        setup_transaction(self, controller, "deposit", "입금하기", "1원부터 1,000,000원까지 가상 계좌에 입금할 수 있습니다.")

    def show(self) -> None:
        """OP-12."""
        show_transaction(self)

    @staticmethod
    def validate_amount(amount_text: str) -> bool:
        """OP-13."""
        try:
            parse_amount(amount_text)
        except BusinessError:
            return False
        return True

    @staticmethod
    def validate_limit(amount: int) -> bool:
        """OP-14."""
        return type(amount) is int and 1 <= amount <= DEPOSIT_LIMIT

    def show_progress(self) -> None:
        """OP-15."""
        self.stage = "processing"
        self.message_var.set("입금 중입니다.")
        lock_form(self, True)

    def show_result(self, message: str) -> None:
        """OP-16."""
        show_transaction_result(self, message)
