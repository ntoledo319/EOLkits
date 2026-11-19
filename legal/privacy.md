# Privacy Policy — EOLkits

**Last updated:** November 19, 2026

## 1. Scope

EOLkits is operated by Toledo Technologies LLC, 2389 Main St. STE 100,
Glastonbury, CT 06033, United States. Toledo Technologies LLC is the controller
of personal data described in this policy unless a provider acts as an
independent controller under its own terms.

This policy describes data used by the EOLkits website, free browser tools, the
$79 Offline Migration & Audit Toolkit purchase/delivery flow, the $299 hosted
repository evidence report, and product-research forms. Self-serve paid Stripe
checkouts are offered to US buyers only. Migration Pack, Drift Watch, Partner
Program, and Organization License are not available for purchase.

## 2. Data We Process

- **Free browser scanner and EOL checker:** Source files and pasted snippets are
  processed in your browser; file names and contents are not uploaded by those
  tools.
- **$79 Offline Migration & Audit Toolkit:** Stripe Checkout metadata, customer
  email, order/fulfillment state, and delivery of the unlisted HTTPS ZIP
  download link. All toolkit scans and codemods run locally on your machine; no
  repository data is sent to EOLkits.
- **$299 Hosted Repository Evidence Report:** Email address, original upload
  filename, uploaded ZIP/source bytes, content hash, generated PDF, evidence
  fingerprint, and fulfillment status.
- **Purchases:** Stripe Checkout identifiers, price/SKU, amount, currency,
  customer email, refund state, and limited attribution fields. Card numbers are
  handled by Stripe and are not stored by EOLkits.
- **Product research:** The Audit-interest form opens a public GitHub issue.
  GitHub publishes the submitting account and selected form answers; EOLkits
  instructs submitters not to include project, company, security, or personal
  data.
- **First-party usage events and aggregate analytics:** Canonical page category,
  allowlisted event name (`view`, `scan`, `checkout_start`, `scan_completed`,
  `checkout_click`), product/kit token, supplied source/UTM tokens, and bounded
  aggregate file and finding counts. EOLkits uses first-party cookieless
  telemetry and does not use advertising trackers, cross-site cookies, or
  browser local storage.
- **Abuse prevention:** A server-secret-keyed pseudonymous network-source token
  is used for rate limiting; the originating address is not written to the
  application database.
- **Infrastructure logs:** Hosting and transactional email providers process
  request metadata such as IP address, user agent, delivery status, and
  timestamps for security and delivery operation.

## 3. Why We Process It

| Purpose | Data | Basis |
|---|---|---|
| Deliver a purchased toolkit download or hosted report | Email, purchase/job state, and (for Audit v2) uploaded archive | Contract fulfillment |
| Process or refund payment | Stripe/purchase state | Contract fulfillment and accounting |
| Protect and operate the service | Request/job/error and aggregate usage data | Legitimate interest |
| Respond to a support or refund email | Customer correspondence | Contract fulfillment / request |

## 4. Storage and Retention

### Audit v2 uploads and reports

- Uploads and generated PDFs for the $299 hosted report are stored on the
  EOLkits API's managed filesystem.
- A successfully delivered report causes its source upload to be deleted
  immediately. Uploads that do not reach checkout expire within 24 hours.
  Checkout-bound uploads are retained for up to 48 hours so fulfillment retries
  can finish, then are swept.
- Generated report PDFs and their `/verify/` verification metadata expire within
  30 days.
- Download and verification URLs contain high-entropy identifiers. Anyone who
  receives the full URL can access it while active, so keep delivery links
  private within your team.

### Operational and financial records

- Purchase, refund, and fulfillment records are stored in Stripe and managed
  SQLite outbox state on our US server as needed to deliver downloads/reports,
  reconcile webhooks, issue refunds, and maintain accounting records.
- Financial records are retained as required by tax, accounting, fraud, or legal
  obligations.
- Raw first-party funnel events in the EOLkits API are automatically deleted
  after 30 days. Pseudonymous abuse-rate keys are deleted after two days.

## 5. Providers

EOLkits uses:

| Provider | Purpose | Data shared |
|---|---|---|
| Stripe | Checkout, tax calculation, and refunds | Email and transaction metadata |
| Transactional SMTP / Resend | Purchase download links, report delivery, and support | Email and message content |
| GitHub | Public source, issues, discussions, and releases | Information you submit to GitHub |
| Hosting provider (US VPS) | Static site, download hosting, and API operation | Requests, operational state, and (for Audit v2) temporary uploads/reports |

EOLkits does not sell personal data.

## 6. Security

- Traffic is served over HTTPS.
- Generated pages enforce a restrictive Content-Security-Policy limiting scripts
  and browser network connections to first-party origins.
- Archive scanning is bounded and does not extract uploaded files onto the host
  filesystem.
- No security control eliminates all risk; avoid uploading secrets, credentials,
  private keys, or data unrelated to a requested scan.

## 7. Your Choices and Rights

You may request access, correction, or deletion of eligible personal data by
emailing `hello@toledotechnologies.com` from the address associated with the
data with subject `EOLkits Privacy Request`, or by mail to Toledo Technologies
LLC, 2389 Main St. STE 100, Glastonbury, CT 06033, United States. Financial and
legal records needed to document or resolve a transaction are retained as
required by law.

## 8. United States Processing and Children

Data is processed in the United States. EOLkits is a developer software service
not directed to children under 16 and does not knowingly collect their data.

## 9. Changes

Material changes will be published on this page with a new update date.
