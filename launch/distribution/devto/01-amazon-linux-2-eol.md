---
title: Amazon Linux 2 is EOL on June 30, 2026 — here's everything that breaks
canonical_url: https://eolkits.com/amazon-linux-2-eol-checklist/
description: Amazon Linux 2 reaches end of life June 30, 2026. What changes on AL2023 (dnf, extras, chronyd, nftables, Python), and a step-by-step migration checklist.
tags: aws, devops, linux, sre
---

Amazon Linux 2 reaches **end of life on June 30, 2026**. After that: no security patches, no new AMIs, no extras updates. Anything still pinned to AL2 in a launch template, EKS node group, ECS task, Beanstalk platform, or container base image is running unpatched from that day on.

Here's what actually changes when you move to Amazon Linux 2023 — the stuff that breaks boot scripts and CI.

## What changes on AL2023

| Area | Amazon Linux 2 | Amazon Linux 2023 |
|---|---|---|
| Package manager | `yum` | `dnf` (a `yum` symlink remains) |
| Extras | `amazon-linux-extras` | **removed** — packages are default, version-namespaced (`python3.11`, `nginx1.24`), or in SPAL |
| Time sync | `ntpd` | `chronyd` |
| Firewall | `iptables` | `nftables` |
| Python | 2.7 and 3.x | **3.x only — no Python 2** |
| glibc | 2.26 | 2.34 |

## The errors you'll hit (and the fix)

- **`amazon-linux-extras: command not found`** — it doesn't exist on AL2023. Install directly with `dnf`, version-namespaced, or via SPAL.
- **`Failed to start ntpd.service: Unit ntpd.service not found`** — use `chronyd` instead.
- **`/usr/bin/env: 'python2': No such file or directory`** — there's no Python 2; port the script to `python3`.
- **`Error: Unable to find a match: <package>`** — the package was renamed/version-namespaced/moved to SPAL. `dnf search` for the real name.

## The migration checklist

1. **Inventory** every AL2 AMI, launch template, EKS node group, ECS task, Beanstalk platform, and container base image.
2. **Rebuild the base AMI** on AL2023 (Packer / EC2 Image Builder).
3. **Package manager**: move `yum` usage to `dnf`, drop `amazon-linux-extras`.
4. **Services**: `ntpd` → `chronyd`, `iptables` → `nftables`.
5. **Python**: port `python2` scripts/shebangs to `python3`.
6. **Test** boot, app start, networking, and time sync on a canary.
7. **Roll out** staged (5 → 25 → 50 → 100%) with a tested rollback.

---

I got tired of grepping for this by hand, so I built a **free scanner** — drop your Terraform / CloudFormation / Packer / Ansible into the browser and it flags every AL2 reference and the errors above, with the AWS source for each. Nothing is uploaded. **[Try it free → eolkits.com/scan](https://eolkits.com/scan)**. There's also an MIT CLI that does the codemods, and a paid audit if you want it done for you.

Full checklist with the per-error fixes: **[eolkits.com/amazon-linux-2-eol-checklist](https://eolkits.com/amazon-linux-2-eol-checklist/)**
