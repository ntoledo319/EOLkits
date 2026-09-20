"""A return URL is not payment evidence; template rendering must preserve that boundary."""

import json
import re
import subprocess

import build


def test_direct_success_url_does_not_claim_payment_or_fulfillment():
    page = build.build_success_page()
    script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
    for query in ("", "?sku=audit", "?sku=unknown"):
        result = subprocess.run(
            [
                "node",
                "--input-type=module",
                "-e",
                "import vm from 'node:vm';"
                "const nodes={title:{},body:{}};"
                "vm.runInNewContext(" + json.dumps(script) + ", {"
                "URLSearchParams,location:{search:" + json.dumps(query) + "},"
                "document:{getElementById:id=>nodes[id]}});"
                "console.log(JSON.stringify(nodes));",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        nodes = json.loads(result.stdout)
        assert "does not confirm a payment" in nodes["body"]["innerHTML"]
        assert "Payment received" not in nodes["body"]["innerHTML"]
        assert "on the way" not in nodes["title"].get("textContent", "")


def test_template_origins_follow_deployment_configuration(monkeypatch):
    monkeypatch.setattr(build, "SITE_URL", "https://example.com/project")
    monkeypatch.setattr(build, "API_URL", "https://api.example.com")
    page = build.build_audit_page(build.load_pricing())
    assert 'href="https://example.com/project/audit/"' in page
    assert "const API = 'https://api.example.com';" in page
    assert "fetch(API + '/api/audit/checkout'" in page
    assert "{API_URL}" not in page


def test_conditional_checkout_copy_matches_the_fulfilment_hold():
    """The page must never hold checkout closed and read as open, or the reverse.

    EOL-04: four sentences saying checkout is not open yet once rendered beside a
    live buy form. Tie the two halves together so they cannot drift apart again.
    """
    page = build.build_audit_page(build.load_pricing())
    held = "const FULFILMENT_PROVEN = false;" in page
    conditional = (
        "When checkout is open",
        "When the readiness gate opens",
        "readiness-gated",
    )
    present = [phrase for phrase in conditional if phrase in page]
    if held:
        assert present, (
            "checkout is held closed but no copy says so; the page reads as if it "
            "were open for business"
        )
    else:
        assert not present, (
            "checkout is open but the page still tells the buyer it is gated: "
            + ", ".join(present)
        )
