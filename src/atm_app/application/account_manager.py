from collections.abc import Iterable

from ..domain import VirtualAccount
from ..shared.errors import AccountAccessError, BusinessError, Code
from ..domain.validation import (
    check_deposit,
    check_transfer,
    check_withdrawal,
    validate_account_number,
    validate_pin,
)


class AccountManager:
    """OP-29..35. Authentication sessions belong to the transaction controller."""

    def __init__(self, accounts: Iterable[VirtualAccount]):
        self._accounts = tuple(accounts)
        if any(not isinstance(account, VirtualAccount) for account in self._accounts):
            raise TypeError("가상 계좌 객체만 등록할 수 있습니다.")
        self._by_number = {account.account_number: account for account in self._accounts}
        if len(self._by_number) != len(self._accounts):
            raise ValueError("중복된 계좌번호가 있습니다.")

    @property
    def accounts(self) -> tuple[VirtualAccount, ...]:
        # Callers may inspect accounts but cannot silently alter the search index.
        return self._accounts

    def _find_account(self, account_number: str) -> VirtualAccount | None:
        """OP-29: 가상계좌찾기."""
        if not validate_account_number(account_number):
            return None
        return self._by_number.get(account_number)

    def _require_account(self, account_number: str) -> VirtualAccount:
        account = self._find_account(account_number)
        if account is None:
            raise AccountAccessError(Code.NOT_AUTHENTICATED)
        if account.is_blocked():
            raise AccountAccessError(Code.ACCOUNT_BLOCKED)
        return account

    def _handle_failed_pin(self, account: VirtualAccount) -> None:
        """OP-30: 비밀번호오류처리."""
        if not account.is_blocked() and account.increment_failed_count() == 5:
            account.block()

    def authenticate(self, account_number: str, password: str) -> str:
        """OP-31: 형식·등록·차단·비밀번호 순서로 검사한다."""
        if not validate_account_number(account_number) or not validate_pin(password):
            return Code.INVALID_FORMAT.value
        account = self._find_account(account_number)
        if account is None:
            return Code.INVALID_CREDENTIALS.value
        if account.is_blocked():
            return Code.ACCOUNT_BLOCKED.value
        if account.matches_pin(password):
            account.reset_failed_count()
            return Code.SUCCESS.value
        self._handle_failed_pin(account)
        return (Code.ACCOUNT_BLOCKED if account.is_blocked() else Code.INVALID_CREDENTIALS).value

    def get_balance(self, account_number: str) -> int:
        """OP-32: 접근 오류를 0원으로 처리하지 않는다."""
        return self._require_account(account_number).get_balance()

    def deposit(self, account_number: str, amount: int) -> bool:
        """OP-33: UI를 우회한 호출에도 동일한 규칙을 적용한다."""
        try:
            account = self._require_account(account_number)
            check_deposit(amount, account.get_balance())
            account.credit(amount)
        except BusinessError:
            return False
        return True

    def withdraw(self, account_number: str, amount: int) -> bool:
        """OP-34: 출금처리."""
        try:
            account = self._require_account(account_number)
            check_withdrawal(amount, account.get_balance())
            account.debit(amount)
        except BusinessError:
            return False
        return True

    def transfer(self, from_account_number: str, target_account_number: str, amount: int) -> bool:
        """OP-35: 설계 범위대로 송신 계좌만 차감하며 수신 계좌를 만들지 않는다."""
        try:
            account = self._require_account(from_account_number)
            check_transfer(from_account_number, target_account_number, amount, account.get_balance())
            account.debit(amount)
        except BusinessError:
            return False
        return True
