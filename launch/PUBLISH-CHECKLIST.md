# PUBLISH CHECKLIST — one-time flywheel activation

Every step here is **one-time setup, no ongoing time** (fits the owner constraint). Each command below was
**verified to work on 2026-07-14** (packages build, pass `twine check`, install clean, console scripts run; all
names confirmed free). Do them in any order; each is independent. Nothing here needs the GRACE VPS.

> The compounding flywheel (these listings + the free CLIs + dev.to backlinks) is now the **primary** growth engine.
> Each publish is a permanent discovery surface funnelling to the $299 audit / $1,499 Pack. See `revenue/PLAN.md`.

---

## 1. PyPI — the two Python CLIs  ✅ verified buildable + installable, names free
Makes `pip install al2023-gate` (in the READMEs) actually work, and puts the tools in PyPI search.

**One-time account:** register at https://pypi.org/account/register/ → verify email → enable 2FA (mandatory) →
create an API token at https://pypi.org/manage/account/#api-tokens (scope: "Entire account" for the first upload).

**Publish (from the repo root):**
```bash
python3 -m pip install --upgrade build twine        # or use a venv
for k in al2023-gate python-pivot; do
  python3 -m build kits/$k                           # writes kits/$k/dist/*.whl + *.tar.gz
  TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-XXXX twine upload kits/$k/dist/*
done
```
Live at https://pypi.org/project/al2023-gate/ and /python-pivot/ within ~1–5 min.
_Verified: both build, `twine check` PASSED, install into a clean venv, and `--version` runs. Names available._

## 2. npm — lambda-lifeline  ✅ verified packable, name free
```bash
cd kits/lambda-lifeline
npm login            # one-time (or npm adduser)
npm publish          # public by default; name "lambda-lifeline" is available
```
_Verified: `npm pack` produces a clean 35.9 kB tarball (34 files, node_modules excluded)._

## 3. VS Code Marketplace — the scanner extension  ✅ packaged + metadata + icon ready
Reaches ~30M+ VS Code users; funnels to the $299 audit (utm-tagged).

**One-time publisher:** create publisher **`eolkits`** at https://aka.ms/vscode-create-publisher (Microsoft account)
→ get a Personal Access Token at https://dev.azure.com (User Settings → PAT → scope **Marketplace: Manage**).
```bash
cd apps/vscode-extension
npx vsce login eolkits      # paste PAT
npx vsce publish            # recompiles + uploads; live in minutes. Zero fees.
```
_Verified: packages to a valid 23.9 KB `.vsix` (compiles via tsc); scanner dates corrected to AWS-authoritative._

## 4. Open VSX — same extension, open registry  ✅ ready
Reaches Cursor / VSCodium / Gitpod users.
```bash
cd apps/vscode-extension
# sign in at https://open-vsx.org with GitHub → create a token → sign the Publisher Agreement, then:
npx ovsx publish -p <token>
```

## 5. GitHub Action Marketplace — publish directly from this repo  ✅ ready (no dedicated repo needed)
Verified against the GitHub docs: Marketplace requires `action.yml` at the repo **root** (✅ `./action.yml` is there,
with `name` + `description` + `branding`) plus a published release. A **monorepo is permitted** — nested manifests
(e.g. `apps/github-action/action.yml`) simply aren't listed. The existing tags (v1 / v1.0.0 / v1.1.0) qualify.
**Steps (one-time):** on GitHub, open `action.yml` → **Draft a release** → check **Publish this Action to the GitHub
Marketplace** → accept the Developer Agreement (first time only) → pick categories → set the tag + title → **Publish**
(requires 2FA). Actions can't charge (funnel only), but it reaches engineers at the exact CI-failure moment.

---

### Notes
- All publishes are free ($0). PyPI/npm/VS Code/Open VSX take no commission (payment stays on the eolkits.com Stripe rail).
- After publishing, watch `eolkits.com/status` (`data.json`) and `track.js` for the first `utm_source=vscode` / install-driven audit session — that's the flywheel converting.
