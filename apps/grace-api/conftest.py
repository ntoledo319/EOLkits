import sys
from pathlib import Path

# Make `eolkits_grace` (this app) and the sibling `runner` package importable from
# tests regardless of pytest's import-mode / rootdir, matching how app.py wires the
# runner onto sys.path at runtime.
_ROOT = Path(__file__).resolve().parent
for _p in (_ROOT, _ROOT.parent / "runner"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
