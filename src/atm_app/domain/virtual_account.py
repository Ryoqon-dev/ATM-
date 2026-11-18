from .constants import MAX_BALANCE, MAX_PIN_FAILURES
from ..shared.errors import AccountAccessError, BusinessError, Code
from .validation import require_positive_amount, validate_account_number, validate_pin


class VirtualAccount:
    """One account's state, OP-36..44. Public state properties are read-only."""

    __slots__ = ("_account_number", "_password", "_balance", "_failed_count", "_blocked")

    def __init__(
        self,
        account_number: str,
        password: str,
        balance: int,
        failed_count: int = 0,
        blocked: bool = False,
    ):
        if not validate_account_number(account_number) or not validate_pin(password):
            raise ValueError("계좌번호 또는 가상 PIN의 형식이 올바르지 않습니다.")
        if type(balance) is not int or not 0 <= balance <= MAX_BALANCE:
            raise ValueError("초기 잔액의 범위가 올바르지 않습니다.")
        if type(failed_count) is not int or not 0 <= failed_count <= MAX_PIN_FAILURES:
            raise ValueError("초기 오류 횟수의 범위가 올바르지 않습니다.")
        if type(blocked) is not bool or blocked != (failed_count == MAX_PIN_FAILURES):
            raise ValueError("오류 횟수와 차단 상태가 일치하지 않습니다.")
        self._account_number = account_number
        self._password = password
        self._balance = balance
        self._failed_count = failed_count
        self._blocked = blocked

    @property
    def account_number(self) -> str:
        return self._account_number

    @property
    def balance(self) -> int:
        return self._balance

    @property
    def failed_count(self) -> int:
        return self._failed_count

    @property
    def blocked(self) -> bool:
        return self._blocked

    def __repr__(self) -> str:
        return f"VirtualAccount(account_number={self.account_number!r}, blocked={self.blocked})"

    def get_account_number(self) -> str:
        """OP-36: 계좌번호읽기."""
        return self._account_number

    def matches_pin(self, password: str) -> bool:
        """OP-37: 문자열 비교로 선행 0을 보존한다."""
        return validate_pin(password) and password == self._password

    def get_balance(self) -> int:
        """OP-38: 잔액읽기."""
        return self._balance

    def _require_active(self) -> None:
        if self._blocked:
            raise AccountAccessError(Code.ACCOUNT_BLOCKED)

    def credit(self, amount: int) -> None:
        """OP-39: 검사를 끝낸 뒤 한 번만 잔액을 변경한다."""
        self._require_active()
        require_positive_amount(amount)
        new_balance = self._balance + amount
        if new_balance > MAX_BALANCE:
            raise BusinessError(Code.BALANCE_LIMIT)
        self._balance = new_balance

    def debit(self, amount: int) -> None:
        """OP-40: 실패 시 기존 잔액을 유지한다."""
        self._require_active()
        require_positive_amount(amount)
        if amount > self._balance:
            raise BusinessError(Code.INSUFFICIENT_FUNDS)
        self._balance -= amount

    def increment_failed_count(self) -> int:
        """OP-41: 다섯 번째 실패와 차단 변경을 같은 호출에서 수행한다."""
        if not self._blocked:
            self._failed_count += 1
            if self._failed_count == MAX_PIN_FAILURES:
                self._blocked = True
        return self._failed_count

    def reset_failed_count(self) -> None:
        """OP-42: 차단 계좌의 오류 횟수를 초기화하지 않는다."""
        self._require_active()
        self._failed_count = 0

    def block(self) -> None:
        """OP-43: 반복 호출에도 같은 차단 상태를 유지한다."""
        self._failed_count = MAX_PIN_FAILURES
        self._blocked = True

    def is_blocked(self) -> bool:
        """OP-44: 거래차단여부확인."""
        return self._blocked
