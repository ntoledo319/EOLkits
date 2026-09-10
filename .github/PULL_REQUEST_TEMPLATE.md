## Summary

<!-- What changed and why. Every claim about the product must be demonstrable today. -->

## History-impact declaration (exactly one; no naked skip)

<!-- Run `python3 scripts/project_history.py assess` and keep ONE line below. -->

- `history:recorded <event-id>` — a capsule was added or amended under `.project-history/events/` and `python3 scripts/project_history.py render && validate` pass
- `history:none — <specific reason>` — immaterial (typo, formatting, lockfile churn, generated refresh, behaviour-preserving refactor, patch bump)
- `history:defer — <tracking item, owner, deadline>` — emergency rollback, incident containment or security hotfix; the deferral is recorded in `.project-history/deferrals.yml` and expires

## Verification

<!-- Commands run and their results. A green unit suite is not evidence that payment, email, DNS or production routing works. -->
