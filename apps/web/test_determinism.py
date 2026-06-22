#!/usr/bin/env python3
"""Determinism gate for the web build (apps/web/build.py).

EOLkits sells deterministic output, but nothing enforced it for the SITE build —
only the CLI kits had a determinism CI gate. The build also used to embed
sub-second wall-clock timestamps, so two rebuilds seconds apart were not
byte-identical. These tests assert the timestamp-bearing builders now produce
identical bytes across consecutive rebuilds (within the same UTC day).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402


def test_migration_pages_byte_identical_across_rebuilds():
    deps = build.load_deprecations()
    pricing = build.load_pricing()
    assert build.build_migration_pages(deps, pricing) == build.build_migration_pages(deps, pricing)


def test_feeds_and_status_seed_byte_identical():
    deps = build.load_deprecations()
    assert build.build_deprecations_rss(deps) == build.build_deprecations_rss(deps)
    assert build.build_deprecations_ics(deps) == build.build_deprecations_ics(deps)
    assert build.build_status_data_seed() == build.build_status_data_seed()


def test_build_date_is_date_only():
    # The single build timestamp must be date-granular (no sub-second component).
    assert len(build._build_date()) == 10 and build._build_date().count("-") == 2


def test_og_image_is_deterministic_and_valid_png(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    build.write_og_image(a)
    build.write_og_image(b)
    assert a.read_bytes() == b.read_bytes()
    assert a.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
