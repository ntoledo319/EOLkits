# Value-first B2B email — the empire's "Found Money Lead", done safely

Lead with a **genuine free finding** about the recipient's own public repo. No pitch up top.
Soft CTA, easy opt-out. This only works if it's true and specific — never blast a generic template.

## Subject
`{repo} pins {finding_short} — heads-up before the AWS cutoff`

## Body (personalize every bracket with something real)
```
Hi {maintainer},

I was scanning public infra-as-code for AWS end-of-life exposure and {repo} came up:

  {finding}            e.g. ".github/workflows/deploy.yml and packer/al2.json still build on
                       Amazon Linux 2, which is EOL Jun 30, 2026 — no patches/AMIs after."

Not selling you anything — just didn't want it to bite you in prod. The specific fix:

  {fix}                e.g. "rebuild the AMI on AL2023; yum->dnf, drop amazon-linux-extras,
                       ntpd->chronyd. Details: https://eolkits.com/amazon-linux-2-eol-checklist/"

If it's useful, there's a free scanner that flags the rest of your stack in ~30s (in-browser,
nothing uploaded): https://eolkits.com/scan — and an MIT CLI that does the codemods.

— Nick / EOLkits

Don't want infra heads-ups like this? Reply "stop" and I won't email again.
```

## Rules (non-negotiable — this is how it stays value-first, not spam)
- **One touch per maintainer. No follow-up if no reply.**
- Every `{finding}` must be verified true against their *public* repo.
- **≤ 10–20/day**, warmed slowly. Honor "stop" immediately.
- Send from a **separate sending identity** (see ../README — never the apex domain that
  Resend uses for audit delivery, or you torch fulfillment deliverability).
