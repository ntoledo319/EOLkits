# Security Policy — EOLkits

## Supported Version

Only the current default-branch revision and most recent release are supported.

## Report a Vulnerability

Do not file a public issue containing exploit details, credentials, customer
data, or a private report URL.

Use GitHub private vulnerability reporting:

1. Open `https://github.com/ntoledo319/EOLkits/security/advisories`.
2. Select **Report a vulnerability**.
3. Include the affected revision, impact, reproduction, and any suggested fix.

If private reporting is unavailable, email `hello@toledotechnologies.com` with
the subject `EOLkits security report`. There is no guaranteed response time.

## Current Boundaries

- The free browser scanner processes selected files locally in the browser.
- Paid Audit source uploads are immutable after receipt, size bounded, and
  deleted after successful delivery or swept within 48 hours. Generated reports
  are swept within 30 days.
- Repository ZIPs are inspected in memory with file-count, expanded-size,
  compression-ratio, encryption, and path-safety checks; they are not extracted
  onto the host.
- Paid checkout is gated by the live API capability response. Unavailable SKUs
  reject at the API, and unfulfillable paid sessions enter a durable refund job.
- Migration Pack, Drift Watch, Organization License, and the public GitHub App
  write path are not currently available for purchase.

## Research Rules

Good-faith research must avoid data destruction, privacy violations, persistence,
denial of service, social engineering, and access to other users' data. Stop and
report if you encounter customer data or a secret. Third-party systems such as
Stripe, GitHub, Resend, and the hosting provider are outside EOLkits authorization.

There is no cash or credit bug-bounty program. Coordinated disclosure and clear
credit are welcome when requested by the reporter.

## User Checklist

- Review findings and generated changes before use.
- Test migrations in a non-production environment.
- Do not upload secrets, private keys, or regulated data.
- Pin Actions/releases to a reviewed revision for sensitive pipelines.
- Recheck AWS support dates at the official linked source before scheduling a
  production change.
