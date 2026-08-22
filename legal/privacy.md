# Privacy Policy — EOLkits

**Last updated:** August 22, 2026

## 1. Scope

This policy describes data used by the EOLkits website, free browser tools, paid
repository evidence report, and product-research forms. The Migration Pack,
Drift Watch, and Organization License are not currently available for purchase.

## 2. Data We Process

- **Free browser scanner:** Source files are processed in your browser and are
  not uploaded by that tool.
- **Paid evidence report:** Email address, original upload filename, uploaded
  ZIP/source bytes, content hash, generated PDF, evidence fingerprint, and
  fulfillment status.
- **Purchases:** Stripe Checkout identifiers, price/SKU, amount, currency,
  customer email, refund state, and limited attribution fields. Card numbers are
  handled by Stripe and are not stored by EOLkits.
- **Product research:** Email, company/name when supplied, product of interest,
  form fields, and a supplied source or referrer origin/path without its query.
- **First-party usage events:** Page path, event name, product/kit, and supplied
  source or UTM values. EOLkits does not use advertising trackers or third-party
  analytics cookies.
- **Abuse prevention:** A server-secret-keyed pseudonymous network-source token
  is used for rate limiting; the originating address is not written to the
  application database.
- **Infrastructure logs:** The hosting and email providers may process request
  metadata such as IP address, user agent, delivery status, and timestamps for
  security and operation.

## 3. Why We Process It

| Purpose | Data | Basis |
|---|---|---|
| Generate and deliver a purchased report | Upload, email, purchase/job state | Contract fulfillment |
| Process or refund payment | Stripe/purchase state | Contract fulfillment and accounting |
| Protect and operate the service | Request/job/error data | Legitimate interest |
| Respond to a requested research follow-up | Submitted research form | Consent/request |

## 4. Storage and Retention

### Audit uploads and reports

- Uploads and generated PDFs are stored on the EOLkits API's managed filesystem.
- A successfully delivered report causes its source upload to be deleted
  immediately. Uploads that do not reach checkout normally expire within 24
  hours. Checkout-bound uploads are retained for up to 48 hours so fulfillment
  retries can finish, then are swept.
- Generated report PDFs and their verification metadata expire within 30 days.
- Download and verification URLs contain a high-entropy identifier. Anyone who
  receives the full URL can use it during the retention window, so do not share
  it publicly.

### Operational and financial records

- Purchase, refund, and fulfillment records are stored in both Stripe and local
  EOLkits SQLite state as needed to deliver, reconcile, refund, and account for a
  purchase.
- Financial records may be retained as required by tax, accounting, fraud, or
  legal obligations.
- First-party funnel events and product-research leads are retained for product
  operation and may be deleted on a verified request unless legal retention
  applies.
- First-touch source/UTM attribution may be stored in your browser's local
  storage. It contains no random user identifier and can be cleared using your
  browser's site-data controls.

## 5. Providers

EOLkits uses:

| Provider | Purpose | Data shared |
|---|---|---|
| Stripe | Checkout and refunds | Email and transaction metadata |
| Resend | Transactional email and requested lead notifications | Email and message content |
| GitHub | Public source, issues, discussions, and releases | Information you submit to GitHub |
| Hosting provider | Static site and API operation | Requests, uploads, generated reports, operational state |

EOLkits does not sell personal data.

## 6. Security

- Traffic is served over HTTPS.
- Upload identifiers are high entropy and uploads become immutable after receipt.
- Archive scanning is bounded and does not extract files onto the host filesystem.
- Production configuration fails closed when required payment/email secrets are
  absent.
- No security control eliminates all risk; avoid uploading secrets, credentials,
  private keys, or data unrelated to the requested source scan.

## 7. Your Choices and Rights

You may request access, correction, or deletion of eligible data, and may object
to or restrict processing where applicable. Financial/legal records and data
needed to resolve a transaction may be retained as required.

Email `hello@toledotechnologies.com` from the address associated with the data
and use the subject `EOLkits Privacy Request`. You may also open a private contact
request through the operator's GitHub profile; do not put sensitive data in a
public issue or discussion.

## 8. International Processing and Children

Providers may process data in the United States or other locations where they
operate. EOLkits is not directed to children under 16 and does not knowingly
collect their data.

## 9. Changes

Material changes will be published on this page with a new update date.
