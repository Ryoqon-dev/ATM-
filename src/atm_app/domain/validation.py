import re

from .constants import DEPOSIT_LIMIT, MAX_BALANCE, WITHDRAWAL_LIMIT, WITHDRAWAL_UNIT
from ..shared.errors import BusinessError, Code


def validate_account_number(text: object) -> bool:
    return isinstance(text, str) and re.fullmatch(r"[0-9]{12}", text) is not None


def validate_pin(text: object) -> bool:
    return isinstance(text, str) and re.fullmatch(r"[0-9]{4}", text) is not None


def parse_amount(text: str) -> int:
    if not isinstance(text, str) or re.fullmatch(r"[0-9]{1,10}", text) is None:
        raise BusinessError(Code.INVALID_AMOUNT)
    value = int(text)
    require_positive_amount(value)
    return value


def require_positive_amount(amount: int) -> None:
    # bool is an int subclass in Python; accepting True as one won is forbidden.
    if type(amount) is not int or not 1 <= amount <= MAX_BALANCE:
        raise BusinessError(Code.INVALID_AMOUNT)


def check_deposit(amount: int, balance: int) -> None:
    require_positive_amount(amount)
    if amount > DEPOSIT_LIMIT:
        raise BusinessError(Code.LIMIT_EXCEEDED)
    if balance + amount > MAX_BALANCE:
        raise BusinessError(Code.BALANCE_LIMIT)


def check_withdrawal(amount: int, balance: int) -> None:
    require_positive_amount(amount)
    if amount % WITHDRAWAL_UNIT:
        raise BusinessError(Code.INVALID_UNIT)
    if amount > WITHDRAWAL_LIMIT:
        raise BusinessError(Code.LIMIT_EXCEEDED)
    if amount > balance:
        raise BusinessError(Code.INSUFFICIENT_FUNDS)


def check_transfer(source: str, target: str, amount: int, balance: int) -> None:
    if not validate_account_number(target) or target == source:
        raise BusinessError(Code.INVALID_TARGET)
    require_positive_amount(amount)
    if amount > balance:
        raise BusinessError(Code.INSUFFICIENT_FUNDS)
