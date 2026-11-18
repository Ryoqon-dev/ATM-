"""Verify the design's method catalog and local README links against the code."""
import importlib
import inspect
import json
from pathlib import Path
import re
import sys
import tomllib
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
MODULES = {
    "TransactionScreen": "atm_app.presentation.transaction_screen",
    "LoginScreen": "atm_app.presentation.login_screen",
    "MenuScreen": "atm_app.presentation.menu_screen",
    "DepositScreen": "atm_app.presentation.deposit_screen",
    "WithdrawalScreen": "atm_app.presentation.withdrawal_screen",
    "TransferScreen": "atm_app.presentation.transfer_screen",
    "ScreenData": "atm_app.application.screen_data",
    "AccountManager": "atm_app.application.account_manager",
    "VirtualAccount": "atm_app.domain.virtual_account",
}


def main():
    catalog = json.loads((ROOT / "docs/development/interface_catalog.json").read_text(encoding="utf-8"))
    operations = []
    for entry in catalog:
        cls = getattr(importlib.import_module(MODULES[entry["name"]]), entry["name"])
        for operation in entry["ops"]:
            method = getattr(cls, operation["en"])
            parameters = [p for p in inspect.signature(method).parameters if p != "self"]
            expected = len(operation["params"].split(",")) if operation["params"] else 0
            assert len(parameters) == expected, (operation["id"], parameters, expected)
            operations.append(operation["id"])
    assert len(operations) == len(set(operations)) == 44
    seed = json.loads((ROOT / "src/atm_app/infrastructure/data/accounts.seed.json").read_text(encoding="utf-8"))
    reference = json.loads((ROOT / "docs/development/data/accounts.seed.json").read_text(encoding="utf-8"))
    assert seed == reference
    with (ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)
    assert project["project"]["dependencies"] == []
    count = 0
    for filename in ("README.md", "read.md", "docs/results/구현현황.md", "docs/results/테스트결과.md"):
        path = ROOT / filename
        text = path.read_text(encoding="utf-8")
        assert "\ufffd" not in text
        for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
            if "://" in link or link.startswith("#"):
                continue
            assert (path.parent / unquote(link.split("#")[0])).exists(), (filename, link)
            count += 1
    assert (ROOT / "README.md").read_bytes() == (ROOT / "read.md").read_bytes()
    print(f"44/44 operation signatures verified; seed matches design; {count} local links verified; README files match")


if __name__ == "__main__":
    main()
