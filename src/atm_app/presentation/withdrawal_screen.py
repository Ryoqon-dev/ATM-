from tkinter import ttk

from ..domain.constants import WITHDRAWAL_LIMIT, WITHDRAWAL_UNIT
from .widgets import setup_transaction, show_transaction, show_transaction_result


class WithdrawalScreen(ttk.Frame):
    withdrawal_unit = WITHDRAWAL_UNIT
    withdrawal_limit = WITHDRAWAL_LIMIT

    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame", padding=28)
        setup_transaction(self, controller, "withdrawal", "출금하기", "10,000원 단위로, 1회 최대 1,000,000원까지 출금할 수 있습니다.")

    def show(self) -> None:
        """OP-17."""
        show_transaction(self)

    @staticmethod
    def validate_unit(amount: int) -> bool:
        """OP-18."""
        return type(amount) is int and amount > 0 and amount % WITHDRAWAL_UNIT == 0

    @staticmethod
    def validate_limit(amount: int) -> bool:
        """OP-19."""
        return type(amount) is int and 1 <= amount <= WITHDRAWAL_LIMIT

    def show_result(self, message: str) -> None:
        """OP-20."""
        show_transaction_result(self, message)

    def show_receipt_prompt(self) -> None:
        """OP-21: 성공한 출금의 화면 안내만 제공한다."""
        if self.stage != "result" or not self.result_success:
            return
        self.receipt_var.set("명세표를 출력하시겠습니까? (화면 안내만 제공하며 실제로 인쇄하지 않습니다.)")
        self.receipt_frame.pack(fill="x", before=self.result_actions, pady=(0, 10))
        self.receipt_actions.pack(anchor="w", pady=(10, 0))
        self.continue_button.configure(state="disabled")
        self.end_button.configure(state="disabled")
