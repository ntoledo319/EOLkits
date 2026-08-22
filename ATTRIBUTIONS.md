# EOLkits attributions and provenance

This file records the license review for the repository's distributable tools
and paid static evidence report. Node surfaces use checked-in npm lockfiles.
Production Python containers install the hash-locked graphs in
`apps/grace-api/requirements.lock` and `apps/runner/requirements.lock`.
The generated resolved inventories are `THIRD_PARTY_LICENSES_GRACE.md` and
`THIRD_PARTY_LICENSES_RUNNER.md`.

## EOLkits code and artifacts

EOLkits source code is licensed under the repository's MIT license unless a file
says otherwise. The paid repository evidence report is original generated HTML
and PDF content. It does not redistribute the Python or Node.js implementation,
scanner packages, AWS SDK, or their source code.

The production container installs DejaVu fonts and the PDF renderer may embed
font subsets. DejaVu fonts are distributed under the Bitstream Vera/DejaVu
license; see <https://dejavu-fonts.github.io/License.html>.

## Runtime dependencies

The following direct dependencies are installed on the server or installed by a
user's package manager; they are not incorporated into the paid report:

| Surface | Direct dependencies | Licenses |
|---|---|---|
| Lambda Lifeline | AWS SDK for JavaScript v3 clients and credential providers | Apache-2.0; transitive helpers also include MIT and 0BSD |
| AL2023 Gate and Python Pivot optional AWS mode | boto3 and botocore | Apache-2.0 |
| Grace API + inline report runner | FastAPI, Uvicorn, python-multipart, Requests, Jinja2, WeasyPrint, PyYAML | MIT, BSD-3-Clause/BSD, Apache-2.0 |
| Audit runner | Requests, Jinja2, WeasyPrint, PyYAML | Apache-2.0, BSD, MIT, MPL |
| Retired Cloudflare tombstone | None | Repository MIT license |

The GitHub Action installs declared dependencies at runtime. The VS Code VSIX
contains the compiled extension, project README, icon, manifest, and MIT license;
it does not bundle `node_modules`.

`pyphen`, a WeasyPrint dependency, offers GPL-2.0-or-later,
LGPL-2.0-or-later, or MPL-1.1 terms; EOLkits relies on the MPL-1.1 option. It is
used server-side and neither its implementation nor its dictionaries are copied
into a paid PDF. The remaining reviewed production graph uses permissive or
file-level MPL terms. No GPL/AGPL/LGPL implementation is redistributed in the
paid report artifact.

The two hash-locked Python graphs were checked with `pip-audit` on August 22,
2026 and reported no known vulnerabilities. Re-run both vulnerability and
license checks whenever a lockfile changes; a past clean result is not a claim
about future vulnerability data.

## Data and source references

AWS service dates and migration guidance are cited to AWS's public documentation
from each report and public rule record. Third-party product names are used only
for factual identification; the retired comparison pages are not part of the
current commercial offer.

## AI-assisted provenance

EOLkits has been developed with AI assistance from Anthropic Claude and OpenAI
Codex under owner direction and review. No testimonial, customer result, traffic
number, or revenue figure is generated or implied by that assistance.
