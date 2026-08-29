# Archived DEV source drafts

These 25 articles mirror material already observed on the owner's DEV profile.
They are retained only to support a manual truth review. The automated publisher
was removed: no file here is approved for republication, and no agent may edit
or post through the owner's account without explicit approval.

Review the live posts against current AWS primary sources, remove closed-product
promotions, and unpublish any article that cannot be corrected honestly. The
batched owner task is tracked in `revenue/HUMAN_QUEUE.md`.

Known critical error: article 24 invents a universal December 31, 2025 IMDSv1
enforcement deadline. AWS documents configurable account, AMI, launch, and
instance-type behavior instead. Unpublish that article; do not republish its
local draft.

Known critical error: article 04's "Timeline recap" table lists `python3.10` as
"Deprecated 2026-03-31". Every other primary-source-derived record in this
repository — `rules/public/deprecations.yml` (`lambda-python-3.10-eol`,
`deprecation_date: "2026-10-31"`) and `kits/lambda-lifeline/src/scan/index.mjs`
(`PHASE_DATES['python3.10'].phase1 = '2026-10-31'`) — agrees on 2026-10-31.
2026-03-31 does not appear as a python3.10 date anywhere else in the codebase
and instead matches this repo's own `ruby3.2` phase-1 date, which suggests a
copy/mix-up rather than a since-superseded AWS date. This is exactly the kind
of superseded/incorrect 2026 date the project has repeatedly had to correct
elsewhere (see `revenue/DECISIONS.md`); flag it during the manual review before
any republication and correct the same row to 2026-10-31 if this article is
ever revived.
