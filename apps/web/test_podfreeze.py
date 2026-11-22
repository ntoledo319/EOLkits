"""podfreeze mirror page (P2.7): both copies carried, gated Dec 2 2026 switch."""

from __future__ import annotations

from datetime import date

import build

ACTIVE_POST = "<p>On <strong>2 December 2026</strong>, CocoaPods trunk stopped"
ACTIVE_PRE = "<p>The CocoaPods maintainer&rsquo;s plan: from <strong>2 December 2026</strong>"


def test_podfreeze_page_carries_both_copies_and_the_brief_line():
    page = build.build_podfreeze_page()
    assert "Moving off CocoaPods?" in page
    assert "https://toledotechnologies.com/brief/?from=podfreeze" in page
    # Both the pre-freeze and the post-freeze copy are present in every build;
    # the inactive one sits in a labelled HTML comment for review.
    assert "stops accepting new" in page
    assert "stopped accepting new" in page
    assert "2&ndash;6 November 2026" in page
    assert "https://blog.cocoapods.org/CocoaPods-Specs-Repo/" in page


def test_podfreeze_copy_never_claims_the_test_run_is_upcoming_or_happened():
    for day in (date(2026, 11, 10), date(2026, 12, 3)):
        for confirmed in (False, True):
            page = build.build_podfreeze_page(today=day, confirmed=confirmed)
            assert "is scheduled" not in page
            assert "test ran" not in page
            assert "plan set a read-only test run" in page


def test_podfreeze_meta_description_is_tense_neutral():
    page = build.build_podfreeze_page()
    assert 'content="CocoaPods trunk read-only from 2 December 2026:' in page
    assert "goes read-only" not in page


def test_podfreeze_page_switches_only_on_or_after_dec_2_and_when_confirmed():
    pre = build.build_podfreeze_page(today=date(2026, 12, 1), confirmed=True)
    post = build.build_podfreeze_page(today=date(2026, 12, 2), confirmed=True)
    unconfirmed = build.build_podfreeze_page(today=date(2026, 12, 3), confirmed=False)
    assert "<!--\n" + ACTIVE_POST in pre
    assert "\n" + ACTIVE_POST in post and "<!--\n" + ACTIVE_POST not in post
    assert "<!--\n" + ACTIVE_PRE in post
    # The calendar alone never flips the copy: without a dated receipt the
    # plan-worded pre-freeze copy stays active.
    assert "<!--\n" + ACTIVE_POST in unconfirmed
    assert "\n" + ACTIVE_PRE in unconfirmed and "<!--\n" + ACTIVE_PRE not in unconfirmed


def test_podfreeze_default_build_is_unconfirmed():
    assert build.PODFREEZE_FREEZE_CONFIRMED is False


def test_podfreeze_page_is_self_canonical_and_passes_the_pages_url_gate():
    page = build.build_podfreeze_page()
    assert '<link rel="canonical" href="' + build.SITE_URL + '/podfreeze/">' in page
    # CI rejects github.io URLs outside the /EOLkits/ project path.
    assert "ntoledo319.github.io/podfreeze" not in page
    assert "https://github.com/ntoledo319/podfreeze" in page


def test_podfreeze_page_makes_no_cross_origin_beacon():
    page = build.build_podfreeze_page()
    # Attribution is the from= tag on the brief link only (the EOLkits
    # privacy page covers first-party events, not a studio pixel).
    assert "px.toledotechnologies.com" not in page
    assert "<img" not in page
