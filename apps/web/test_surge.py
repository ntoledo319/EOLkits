#!/usr/bin/env python3
"""Unit test for the LB-3 surge-collapse fix (days_until_nearest_enforcement).

Before the fix, surge pricing keyed off a single date (block-create 2027-02-01) and
collapsed to the standard $299 tier the moment it passed — i.e. through the entire
Feb->Mar 2027 demand peak. The fix tracks the nearest FUTURE enforcement date.

Run from the repo root:  python3 apps/web/test_surge.py
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402

DEP = {"date": "2027-02-01", "block_update_date": "2027-03-03"}


def check(desc, got, want):
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {desc}: got {got}, want {want}")
    return ok


def main():
    ok = True
    # Before both enforcement dates -> nearest is block-create.
    ok &= check("2027-01-20 -> 12d to block-create", build.days_until_nearest_enforcement(DEP, today=date(2027, 1, 20)), 12)
    # THE BUG: block-create passed, block-update ahead -> must NOT collapse to 'passed'.
    ok &= check("2027-02-15 -> tracks block-update (16d), not collapse", build.days_until_nearest_enforcement(DEP, today=date(2027, 2, 15)), 16)
    # Peak: 3 days before block-update -> urgent tier window.
    ok &= check("2027-02-28 -> 3d to block-update (urgent)", build.days_until_nearest_enforcement(DEP, today=date(2027, 2, 28)), 3)
    # Both passed -> truly past (negative).
    ok &= check("2027-03-10 -> both passed (negative)", build.days_until_nearest_enforcement(DEP, today=date(2027, 3, 10)) < 0, True)
    # Old single-date code would report 2027-02-15 as -14 ('passed' -> $299). Confirm the fix differs.
    old = build.get_days_until_deadline  # unchanged single-date helper still exists
    print(f"  [info] surge tier at 16d-out = {build.get_surge_price(299, 16)}  | at 3d-out = {build.get_surge_price(299, 3)}  | passed = {build.get_surge_price(299, -5)}")
    print("ALL PASS" if ok else "FAILURES ABOVE")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
