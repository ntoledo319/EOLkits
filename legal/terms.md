# Terms of Service — EOLkits

**Last updated:** August 22, 2026

## 1. Acceptance

By using EOLkits, you agree to these Terms. If you do not agree, do not use the
service.

## 2. Available Services

### Free tools

The local CLI tools, browser scanner, documentation, and GitHub Action are
provided under their applicable open-source licenses. The free scanners detect
configured patterns in the files or inventory you supply; they do not guarantee
a complete AWS account inventory.

### Paid repository evidence report

The only self-serve paid product is a static evidence report for one uploaded
repository ZIP or supported source file. The report includes:

- exact observed file/line evidence for matched rules;
- observed match/file counts and a severity-based remediation order;
- an official or primary project source for each configured rule;
- the input SHA-256, rule-pack/report-engine versions, and a deterministic
  evidence fingerprint; and
- explicit scope and limitations.

The report does **not** query a live AWS account, execute code, prove
exploitability, count resources that are not present in the uploaded source,
estimate downtime dollars, guarantee completeness, or constitute a digitally
signed PDF. Target dates supplied at checkout are context only and do not change
the price or findings.

### Unavailable concepts

Migration Pack, Drift Watch, and Organization License are private research/beta
concepts and are not available for purchase. No listed feature, price, or prior
page creates a right to purchase them. A stale direct payment that cannot be
fulfilled is subject to automatic full refund handling.

## 3. Payment, Delivery, and Refunds

- Payment is processed by Stripe in USD.
- The paid report is generated after verified payment and emailed when processing
  succeeds. Provider outages and unusually large valid inputs can delay delivery.
- If automated paid fulfillment permanently fails after retries, EOLkits queues
  a full refund to the original payment method. If Stripe does not confirm that
  refund, the order is flagged for operator review; customers may always use the
  contact route below.
- You may also request a full Audit refund within 30 days of purchase by emailing
  `hello@toledotechnologies.com` from the purchase address. Include the Stripe
  receipt or Checkout Session identifier. No explanation is required.
- Refund posting time after issuance is controlled by Stripe and the customer's
  financial institution.

## 4. Customer Responsibilities

You confirm that you have authority to upload and analyze the submitted files.
Do not upload credentials, secrets, private keys, regulated personal data, or
unrelated confidential material. Review every finding and test every change in a
non-production environment before deployment.

## 5. Intellectual Property

- Open-source code remains governed by its repository license.
- A purchased report may be used and shared internally within the purchasing
  organization.
- Customer source remains the customer's property. EOLkits receives only the
  limited right to process it for requested fulfillment and security/abuse
  prevention during the stated retention period.

## 6. Acceptable Use

Do not abuse, disrupt, probe without authorization, evade limits, upload
malicious archives, infringe rights, or use EOLkits in violation of law or a
third-party platform's terms.

## 7. Disclaimers

EOLkits is provided "as is" and "as available." AWS and other platforms may
change schedules and behavior. Source analysis can produce false positives,
false negatives, or recommendations that require environment-specific changes.
EOLkits is not a substitute for security, legal, compliance, or production
change review.

To the maximum extent permitted by law, EOLkits is not liable for indirect,
incidental, special, consequential, or lost-profit damages arising from use of
the service. Nothing in these Terms excludes liability that cannot legally be
excluded.

## 8. Changes and Contact

Material changes will be published here with a new update date. Questions and
refund requests: `hello@toledotechnologies.com`.
