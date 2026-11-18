from tkinter import ttk

from .widgets import setup_transaction, show_transaction, show_transaction_result


class TransferScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame", padding=28)
        setup_transaction(self, controller, "transfer", "가상 이체하기", "대상 번호로 보내는 과정을 모의 처리합니다. 송신 계좌에서만 차감되며 실제 송금은 발생하지 않습니다.")

    def show(self) -> None:
        """OP-22."""
        show_transaction(self)

    def show_result(self, message: str) -> None:
        """OP-23."""
        show_transaction_result(self, message)
