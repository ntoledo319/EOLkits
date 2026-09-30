"""The report sample must remain reachable before and after any scan result."""
from html.parser import HTMLParser
import build

class BridgeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.bridges = []
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get('id')=='report-scope-link':self.bridges.append((attrs,list(self.stack)))
        if tag not in {'meta','link','input','br','img','hr','source','area','base','embed','param','track','wbr'}:self.stack.append((tag,attrs))
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:self.stack=self.stack[:i];break

def assert_persistent(page):
    parser = BridgeParser()
    parser.feed(page)
    assert len(parser.bridges)==1
    attrs,parents=parser.bridges[0]
    assert 'hidden' not in attrs
    assert not any('hidden' in a or a.get('id') in {'results','scan-output','next-step'} for _,a in parents)
    assert '<a href="/audit/">Inspect the sample and $299 report scope</a>' in page
    assert 'A scan with no matches is not proof' in page

def test_report_bridge_is_outside_mutable_and_hidden_results():
    assert_persistent(build.build_scan_page(build.load_deprecations()))

def test_bridge_control_rejects_missing_or_hidden_links():
    import pytest
    page=build.build_scan_page(build.load_deprecations())
    for bad in (page.replace('id="report-scope-link"','id="missing"'),page.replace('id="report-scope-link"','id="report-scope-link" hidden')):
        with pytest.raises(AssertionError):assert_persistent(bad)
