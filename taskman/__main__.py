"""Entry point enabling ``python -m taskman``."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
