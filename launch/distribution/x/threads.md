# X / Twitter — ready-to-post content (own account, own content)

Dev audience lives on X (where Reddit is now a dud). These are evergreen + deadline-timed
posts. Auto-postable via the X API (see ../email/../README for the cred gate — X's API is
the weak link: the usable write tier is paid ~$100/mo, so this lever may stay manual/low-priority).
All content is first-party (your tools, your facts) — not spam.

---

## Thread 1 — Amazon Linux 2 EOL (pin until Jun 30)

1/ Amazon Linux 2 is EOL **June 30, 2026**. After that: no patches, no new AMIs. Anything pinned to AL2 in a launch template or EKS node group is running unpatched.

Free 30-sec check on your own stack (in-browser, nothing uploaded): https://eolkits.com/scan

2/ What breaks on AL2023:
• `yum` → `dnf`
• `amazon-linux-extras` → gone
• `ntpd` → `chronyd`
• `iptables` → `nftables`
• no Python 2
Each with the exact fix: https://eolkits.com/amazon-linux-2-eol-checklist/

3/ Most "Unable to find a match" errors on AL2023 = the package was renamed or moved to SPAL. `dnf search <keyword>` finds the new name. Full list of gotchas in the checklist above.

---

## Thread 2 — Lambda runtime deprecation schedule

1/ AWS blocks deprecated Lambda runtimes in 2 steps: first **creating** new functions, then ~30 days later **updating** existing ones. After that your function is frozen until you redeploy on a new runtime.

The full schedule (python3.8–3.11, nodejs18/20), with dates + sources: https://eolkits.com/lambda-runtime-deprecation-schedule/

2/ Moving to python3.12? `distutils`, `imp`, and `collections.Mapping` are gone. Moving to nodejs22? `aws-sdk` v2 isn't bundled anymore. The exact errors + fixes: https://eolkits.com/fix/

---

## Singles (rotate, ~2–3/week)

- `ModuleNotFoundError: No module named 'distutils'` after moving a Lambda to python3.12? It was removed in 3.12. Fix: setuptools + packaging. https://eolkits.com/fix/python-no-module-named-distutils/
- `Cannot find module 'aws-sdk'` on nodejs18+? The v2 SDK isn't preinstalled anymore — only @aws-sdk v3. https://eolkits.com/fix/node-cannot-find-module-aws-sdk/
- `GLIBC_2.28 not found` in a Lambda native dep? The wheel was built for a newer glibc than the runtime. Build manylinux2014 or move to an AL2023 runtime. https://eolkits.com/fix/lambda-glibc-version-not-found/
