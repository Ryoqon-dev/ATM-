import json
from pathlib import Path
from typing import Any

from ..domain.constants import MAX_BALANCE, MAX_PIN_FAILURES
from ..domain import VirtualAccount
from ..shared.errors import SeedDataError
from ..domain.validation import validate_account_number, validate_pin

DEFAULT_SEED = Path(__file__).parent / "data" / "accounts.seed.json"
ACCOUNT_FIELDS = {"accountNumber", "password", "balance", "failedCount", "blocked"}


def validate_seed(data: Any) -> None:
    if type(data) is not dict or set(data) != {"schemaVersion", "accounts"}:
        raise SeedDataError("초기 자료의 최상위 필드가 올바르지 않습니다.")
    if type(data["schemaVersion"]) is not int or data["schemaVersion"] != 1:
        raise SeedDataError("지원하지 않는 초기 자료 버전입니다.")
    if type(data["accounts"]) is not list:
        raise SeedDataError("accounts는 배열이어야 합니다.")
    seen = set()
    for index, row in enumerate(data["accounts"], 1):
        prefix = f"초기 자료 {index}번째 계좌: "
        if type(row) is not dict or set(row) != ACCOUNT_FIELDS:
            raise SeedDataError(prefix + "필수 필드 또는 허용 필드가 올바르지 않습니다.")
        if not validate_account_number(row["accountNumber"]) or not validate_pin(row["password"]):
            raise SeedDataError(prefix + "계좌번호 또는 가상 PIN 형식이 올바르지 않습니다.")
        if row["accountNumber"] in seen:
            raise SeedDataError(prefix + "계좌번호가 중복되었습니다.")
        seen.add(row["accountNumber"])
        if type(row["balance"]) is not int or not 0 <= row["balance"] <= MAX_BALANCE:
            raise SeedDataError(prefix + "잔액이 허용 범위를 벗어났습니다.")
        if type(row["failedCount"]) is not int or not 0 <= row["failedCount"] <= MAX_PIN_FAILURES:
            raise SeedDataError(prefix + "오류 횟수가 허용 범위를 벗어났습니다.")
        if type(row["blocked"]) is not bool or row["blocked"] != (row["failedCount"] == MAX_PIN_FAILURES):
            raise SeedDataError(prefix + "오류 횟수와 차단 상태가 일치하지 않습니다.")


def _unique_fields(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise SeedDataError("초기 자료 JSON에 중복된 필드가 있습니다.")
        result[key] = value
    return result


def load_seed(path: str | Path | None = None) -> list[VirtualAccount]:
    """Validate the entire JSON before constructing any usable account list."""
    try:
        with Path(path if path is not None else DEFAULT_SEED).open(encoding="utf-8-sig") as stream:
            data = json.load(stream, object_pairs_hook=_unique_fields)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SeedDataError("초기 계좌 자료를 읽을 수 없습니다. UTF-8 JSON 파일을 확인해 주세요.") from exc
    validate_seed(data)
    return [
        VirtualAccount(row["accountNumber"], row["password"], row["balance"], row["failedCount"], row["blocked"])
        for row in data["accounts"]
    ]
