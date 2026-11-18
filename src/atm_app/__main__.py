import argparse
import sys
from pathlib import Path

from .infrastructure.bootstrap import load_seed
from .shared.errors import SeedDataError
from .application import AccountManager


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="로컬 가상 계좌 ATM 시뮬레이터")
    parser.add_argument("--seed", type=Path, help="별도 UTF-8 JSON 시드 파일 (기본: 앱에 포함된 가상 계좌)")
    parser.add_argument("--check", action="store_true", help="시드와 계좌 규칙만 검사하고 GUI 없이 종료")
    args = parser.parse_args(argv)
    try:
        accounts = load_seed(args.seed)
        manager = AccountManager(accounts)
    except SeedDataError as exc:
        if args.check:
            print(f"초기화 실패: {exc}", file=sys.stderr)
        else:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("ATM 초기 자료 오류", str(exc), parent=root)
            root.destroy()
        return 1
    if args.check:
        print(f"초기 계좌 {len(manager.accounts)}개: 형식·범위·유일성·차단 상태 검사 통과")
        return 0
    import tkinter as tk
    from .presentation.transaction_screen import TransactionScreen
    root = tk.Tk()
    TransactionScreen(root, manager)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
