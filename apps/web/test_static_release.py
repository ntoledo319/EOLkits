"""A deploy build must be complete without touching the committed Pages mirror."""

import hashlib
import importlib.util
import tempfile
from pathlib import Path

import build
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "static_release", ROOT / "scripts/verify_static_release.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def snapshot(directory):
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*")
        if path.is_file()
    }


@pytest.fixture
def staged(monkeypatch):
    monkeypatch.setattr(build, "SITE_URL", "https://eolkits.com")
    monkeypatch.setattr(build, "API_URL", "https://eolkits.com")
    monkeypatch.setattr(build, "PROJECT_BASE_PATH", "")
    scratch = ROOT / "tmp/verify"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix="release-test-") as directory:
        target = Path(directory)
        target.chmod(0o755)
        before = snapshot(ROOT / "docs")
        assert build.main(target) == 0
        assert snapshot(ROOT / "docs") == before
        yield target


def test_isolated_release_is_complete_and_reproducible(staged):
    assert release.validate(staged) >= 60
    assert not list(staged.rglob("*.md"))
    assert not (staged / "history").exists()
    first = snapshot(staged)
    assert build.main(staged) == 0
    assert snapshot(staged) == first
    assert (staged / "style.css").read_bytes() == (ROOT / "apps/web/static/site.css").read_bytes()


@pytest.mark.parametrize(
    "defect", ["asset", "origin", "script", "csp", "sample", "internal", "symlink", "permissions"]
)
def test_release_guard_rejects_broken_or_unsafe_output(staged, defect):
    home = staged / "index.html"
    if defect == "asset":
        (staged / "style.css").unlink()
    elif defect == "origin":
        home.write_text(
            home.read_text().replace("https://eolkits.com", "https://ntoledo319.github.io")
        )
    elif defect == "script":
        home.write_text(home.read_text() + '<script src="//example.invalid/a.js"></script>')
    elif defect == "csp":
        home.write_text(home.read_text().replace("Content-Security-Policy", "Disabled-Policy"))
    elif defect == "sample":
        (staged / "audit/sample/eolkits-sample-report.pdf").write_bytes(b"corrupted")
    elif defect == "internal":
        (staged / "internal.md").write_text("Must not deploy operator notes")
    elif defect == "permissions":
        (staged / "style.css").chmod(0o600)
    else:
        (staged / "linked.css").symlink_to(ROOT / "apps/web/static/site.css")
    with pytest.raises(release.ReleaseError):
        release.validate(staged)


def test_builder_rejects_output_outside_repository_and_root():
    for path in (ROOT, ROOT.parent / "outside-output"):
        with pytest.raises(ValueError, match="subdirectory of the repository"):
            build.main(path)


def test_builder_rejects_nested_output_symlink(staged):
    original = staged / "audit/index.html"
    original.unlink()
    # A link may not redirect a generated page outside the requested output.
    original.symlink_to(ROOT / "tmp/verify/forbidden-generated-output.html")
    with pytest.raises(ValueError, match="escapes the selected directory"):
        build.main(staged)
    assert not (ROOT / "tmp/verify/forbidden-generated-output.html").exists()
