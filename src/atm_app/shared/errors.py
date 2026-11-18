from enum import StrEnum


class Code(StrEnum):
    SUCCESS = "SUCCESS"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_BLOCKED = "ACCOUNT_BLOCKED"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    INVALID_UNIT = "INVALID_UNIT"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    INVALID_TARGET = "INVALID_TARGET"
    BALANCE_LIMIT = "BALANCE_LIMIT"
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"


MESSAGES = {
    Code.INVALID_FORMAT: "계좌번호는 숫자 12자리, 비밀번호는 숫자 4자리로 입력해 주세요.",
    Code.INVALID_CREDENTIALS: "계좌번호 또는 비밀번호가 일치하지 않습니다.",
    Code.ACCOUNT_BLOCKED: "비밀번호 연속 오류 5회로 거래가 차단된 계좌입니다.",
    Code.INVALID_AMOUNT: "금액은 1원 이상, 10자리 이하의 숫자로 입력해 주세요. 공백·쉼표·소수·부호는 사용할 수 없습니다.",
    Code.LIMIT_EXCEEDED: "1회 입금·출금 한도는 1,000,000원입니다.",
    Code.INVALID_UNIT: "출금액은 10,000원 단위로 입력해 주세요.",
    Code.INSUFFICIENT_FUNDS: "잔액이 부족합니다.",
    Code.INVALID_TARGET: "본인 계좌와 다른 숫자 12자리의 대상 계좌번호를 입력해 주세요.",
    Code.BALANCE_LIMIT: "입금 후 잔액이 최대 보관 금액인 9,999,999,999원을 초과합니다.",
    Code.NOT_AUTHENTICATED: "로그인 후 거래를 이용해 주세요.",
    Code.PROCESSING_FAILED: "거래를 처리할 수 없습니다. 잔액을 확인한 후 다시 이용해 주세요.",
    Code.UNEXPECTED_ERROR: "처리 중 오류가 발생했습니다. 다시 로그인하여 잔액을 확인해 주세요.",
}


class BusinessError(ValueError):
    def __init__(self, code: Code):
        self.code = code
        super().__init__(MESSAGES.get(code, MESSAGES[Code.PROCESSING_FAILED]))


class AccountAccessError(BusinessError):
    """Missing or blocked account; distinct from a legitimate zero balance."""


class SeedDataError(ValueError):
    """Invalid startup data. Messages must not include account passwords."""
