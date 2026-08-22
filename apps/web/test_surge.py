"""Deadline-context and flat-pricing regression tests."""

from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "eolkits_web_build", Path(__file__).with_name("build.py")
)
assert SPEC and SPEC.loader
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)

DEP = {"date": "2027-02-01", "block_update_date": "2027-03-03"}


def test_nearest_future_enforcement_date_is_used_for_context():
    assert build.nearest_enforcement(DEP, today=date(2027, 1, 20)) == (12, "2027-02-01")
    assert build.nearest_enforcement(DEP, today=date(2027, 2, 15)) == (16, "2027-03-03")
    assert build.nearest_enforcement(DEP, today=date(2027, 2, 28)) == (3, "2027-03-03")
    days, deadline = build.nearest_enforcement(DEP, today=date(2027, 3, 10))
    assert days < 0
    assert deadline == "2027-03-03"


def test_audit_price_does_not_change_with_deadline():
    assert {build.get_surge_price(299, days) for days in (-5, 0, 3, 16, 365)} == {299}
