# Terms of Service — EOLkits

**Last updated:** November 19, 2026

## 1. Acceptance and Geographic Scope

EOLkits is operated by Toledo Technologies LLC, 2389 Main St. STE 100,
Glastonbury, CT 06033, United States ("EOLkits," "we," or "us").

By using EOLkits, you agree to these Terms. If you do not agree, do not use the
service. Self-serve paid Stripe checkouts on EOLkits are offered to **US buyers
only** purchasing for software engineering, cloud infrastructure, or business
operations.

## 2. Available Services

### Free tools

The local CLI tools, browser scanner, documentation, and GitHub Action are
provided under their applicable open-source licenses. The free scanners detect
configured patterns in the files or inventory you supply; they do not certify
a complete AWS account inventory.

### Paid Offline Migration & Audit Toolkit ($79)

The $79 Offline Migration & Audit Toolkit is a downloadable software and
template archive delivered via an unlisted HTTPS download link sent to the
checkout email address after verified Stripe payment. The archive includes:

- a zero-dependency Python 3.10+ air-gapped CLI scanner that inspects local
  repositories, IaC templates, Dockerfiles, dependency manifests, and optional
  `aws lambda list-functions` JSON exports to emit local HTML/PDF-printable
  reports, Jira CSV exports, and SHA-256 attestation JSON files;
- local AST and source codemod utilities for Python 3.12/3.13 removed standard
  library modules, Node.js `aws-sdk` v2 to `@aws-sdk/*` v3 client mapping, and
  Amazon Linux 2 to AL2023 user-data/Dockerfile checks;
- Amazon Linux 2023 native wheel and N-API Lambda layer Dockerfiles (`x86_64`
  and `arm64`); and
- Terraform, AWS SAM, GitHub Actions canary rollback templates, and Change
  Advisory Board (CAB) sign-off checklists.

All toolkit execution occurs locally in the buyer's environment with no source
code transmitted to EOLkits.

### Paid Hosted Repository Evidence Report ($299)

When its server readiness gate is open, EOLkits also offers a $299 hosted
static evidence report for one uploaded repository ZIP or supported source file.
The report includes:

- exact observed file/line evidence for matched rules;
- observed match/file counts and a severity-based remediation order;
- a configured rule or package reference for each matched finding (dependency
  floors are conservative triage baselines and require target-specific
  verification);
- the input SHA-256, rule-pack/report-engine versions, and a deterministic
  evidence fingerprint; and
- explicit scope and limitations.

Neither paid product queries a live AWS account on its own, executes customer
code, proves exploitability, counts resources absent from supplied inputs,
estimates downtime dollars, certifies completeness, or constitutes a
cryptographically signed PDF. Target dates supplied at checkout are planning
context only and do not alter pricing or findings.

### Unavailable concepts

Migration Pack, Drift Watch, Partner Program, and Organization License are
retired or research concepts and are not available for purchase. No listed
feature, price, or prior page creates a right to purchase them. A stale direct
payment that cannot be fulfilled is subject to automatic full refund handling.

## 3. Payment, Delivery, and Refunds

- Payment is processed by Stripe in USD (**US buyers only**).
- For the $79 Offline Migration & Audit Toolkit, automated fulfillment emails
  the buyer's unlisted HTTPS ZIP download link after Stripe confirms checkout.
- For the $299 Hosted Repository Evidence Report, the PDF is generated after
  verified payment and emailed when processing completes. Provider outages and
  unusually large valid inputs can delay delivery. If automated Audit v2
  fulfillment permanently fails after retries, EOLkits queues a full refund to
  the original payment method and flags any unconfirmed refund for operator
  review.
- **30-day full refund policy:** You may request a full refund on either paid
  product within 30 days of purchase by emailing `hello@toledotechnologies.com`
  from the purchase address with your Stripe receipt. No explanation is
  required.
- Refund posting time after issuance is controlled by Stripe and the customer's
  financial institution.

## 4. Customer Responsibilities and Retention Alignment

For uploaded Audit v2 inputs, you confirm that you have authority to upload and
analyze the submitted files. Do not upload credentials, secrets, private keys,
regulated personal data, or unrelated confidential material. Source uploads for
delivered Audit v2 reports are deleted immediately upon delivery; unchecked
uploads expire within 24 hours; checkout-bound uploads expire within 48 hours so
fulfillment retries can complete; generated Audit v2 PDFs and `/verify/`
metadata expire within 30 days.

Review every finding and test every codemod, container layer, and infrastructure
change in a non-production environment with rollback controls before production
deployment.

## 5. Intellectual Property

- Public repository CLIs remain governed by the MIT license.
- A purchased $79 Offline Migration & Audit Toolkit archive is licensed for
  internal use across unlimited repositories owned or operated by the purchasing
  individual or company. Public redistribution, resale, or republishing of the
  commercial archive is prohibited.
- A purchased $299 report may be used and shared internally and with auditors or
  clients of the purchasing organization.
- Customer source remains the customer's property.

## 6. Acceptable Use

Do not abuse, disrupt, probe without authorization, evade limits, upload
malicious archives, infringe rights, or use EOLkits in violation of law or a
third-party platform's terms.

## 7. Disclaimers

EOLkits is provided "as is" and "as available." AWS and other platforms may
change schedules and behavior. Source analysis and codemods can produce false
positives, false negatives, or changes that require workload-specific adjustment.
EOLkits is not a substitute for security, legal, compliance, or production
change review.

To the maximum extent permitted by law, EOLkits is not liable for indirect,
incidental, special, consequential, or lost-profit damages arising from use of
the service or software, and total aggregate liability for any claim shall not
exceed the amount paid by you for the specific product giving rise to the claim.
Nothing in these Terms excludes liability that cannot legally be excluded.

## 8. Governing Law

These Terms are governed by the laws of the State of Connecticut, without
regard to its conflict-of-law rules.

## 9. Changes and Contact

Material changes will be published here with a new update date. Questions and
refund requests: `hello@toledotechnologies.com`. Postal correspondence may be
sent to Toledo Technologies LLC, 2389 Main St. STE 100, Glastonbury, CT 06033,
United States.
