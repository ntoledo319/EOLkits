"""Allow `python -m al2023_gate ...`."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
