"""Run directly from a source checkout without installing the package."""
from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).resolve().parent / "src"


def main(argv: list[str] | None = None) -> int:
    source = str(SOURCE_ROOT)
    if source not in sys.path:
        sys.path.insert(0, source)
    from atm_app.__main__ import main as app_main
    return app_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
