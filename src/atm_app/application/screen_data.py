from dataclasses import dataclass


@dataclass(slots=True)
class ScreenData:
    account_number: str | None = None
    shown_balance: int | None = None
    selected_menu: str | None = None
    amount_text: str = ""
    target_account_number: str = ""

    def set_account_number(self, account_number: str) -> None:
        """OP-24."""
        self.account_number = account_number

    def get_account_number(self) -> str | None:
        """OP-25."""
        return self.account_number

    def set_shown_balance(self, balance: int) -> None:
        """OP-26: 표시용 사본이며 거래 승인에 사용하지 않는다."""
        self.shown_balance = balance

    def set_transaction_input(self, menu: str, amount_text: str, target_account_number: str) -> None:
        """OP-27."""
        self.selected_menu = menu or None
        self.amount_text = amount_text
        self.target_account_number = target_account_number

    def clear(self) -> None:
        """OP-28: PIN 필드는 없으며 모든 세션 속성을 초기화한다."""
        self.account_number = None
        self.shown_balance = None
        self.selected_menu = None
        self.amount_text = ""
        self.target_account_number = ""
