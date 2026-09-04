"""Demand-capture gates: measurable, price-qualified, and never a fake order."""

from pathlib import Path

import build
import yaml

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
ISSUE_FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "audit-interest.yml"


def test_interest_form_is_public_nonbinding_and_price_qualified() -> None:
    form = yaml.safe_load(ISSUE_FORM.read_text(encoding="utf-8"))
    assert form["title"].startswith("[Audit interest]")
    assert all(item["type"] in {"markdown", "dropdown", "checkboxes"} for item in form["body"])

    rendered = ISSUE_FORM.read_text(encoding="utf-8").lower()
    for phrase in (
        "$299",
        "real project files",
        "relevant finding",
        "would consider purchasing",
        "public, nonbinding",
        "not an order",
        "do not include repository names",
    ):
        assert phrase in rendered

    qualification = next(item for item in form["body"] if item.get("id") == "qualification")
    assert all(option.get("required") is True for option in qualification["attributes"]["options"])


def test_closed_audit_page_offers_only_qualified_public_interest() -> None:
    page = (DOCS / "audit" / "index.html").read_text(encoding="utf-8")
    assert "repository evidence report" in page
    assert "$299" in page
    assert "issues/new?template=audit-interest.yml" in page
    assert "not an order, reservation, waitlist, or promise of a reply" in page
    assert '<form id="auditForm" hidden>' in page
    assert '<script defer src="/EOLkits/track.js"></script>' in page
    assert '<link rel="canonical" href="https://ntoledo319.github.io/EOLkits/audit/">' in page
    assert 'property="og:title"' in page
    assert "No AWS credentials or AWS account access are requested" in page
    assert "width:300px" not in page
    assert page.index('<div class="pricing">') < page.index('id="auditGate"')
    assert page.index('id="auditGate"') < page.index("Why you can trust")


def test_schedule_routes_search_traffic_to_a_source_linked_audit_offer() -> None:
    page = (DOCS / "lambda-runtime-deprecation-schedule" / "index.html").read_text(encoding="utf-8")
    assert "Need archive-wide source evidence?" in page
    assert "$299 report" in page
    assert "source=lambda_schedule" in page
    assert "utm_campaign=repo_audit" in page
    assert "https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html" in page


def test_scanner_interest_appears_only_in_the_findings_branch() -> None:
    source = build._SCAN_JS
    no_findings, findings = source.split("const rows =", maxsplit=1)
    assert "INTEREST_URL" not in no_findings
    assert "INTEREST_URL" in findings
    assert "report ($299)" in findings


def test_distribution_links_identify_their_source() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    action_readme = (ROOT / "apps" / "github-action" / "README.md").read_text(encoding="utf-8")
    assert "source=github_readme" in readme
    assert "source=github_action" in action_readme
