---
title: "amazon-linux-extras: command not found — it's gone on Amazon Linux 2023"
canonical_url: https://eolkits.com/fix/amazon-linux-extras-command-not-found/
description: Scripts, Dockerfiles, and user-data that call amazon-linux-extras fail outright on Amazon Linux 2023 — the command doesn't exist there. Here's what replaces it.
tags: aws, linux, devops, sysadmin
---

You moved an AMI, Dockerfile, or user-data script from Amazon Linux 2 to Amazon Linux 2023, and a line that used to work now dies immediately:

```
bash: amazon-linux-extras: command not found
```

Not a missing package, not a stale repo — the `amazon-linux-extras` mechanism itself doesn't exist on AL2023. There's nothing to install to bring it back.

## Why this happens

Amazon Linux 2 shipped one old baseline of everything in its base repo, so AWS layered the **Extras Library** on top — `amazon-linux-extras enable nginx1.20`, `amazon-linux-extras install docker`, and so on — to get newer versions of common packages without breaking the base image. Amazon Linux 2023 dropped that constraint (and the tool with it): its base `dnf` repos ship current versions directly, so there's no separate "extras" layer to enable. Anything still calling `amazon-linux-extras` — a golden-AMI build step, a Dockerfile `RUN`, a cloud-init runcmd — has no command to run.

## The fix

Stop calling `amazon-linux-extras` on AL2023. What it used to gate now falls into one of three places:

```bash
# 1. Most former "extras" packages are just default dnf packages now
sudo dnf install -y docker

# 2. Version-specific ones are version-namespaced package names
sudo dnf install -y python3.11
sudo dnf install -y nginx1.24
sudo dnf install -y postgresql15

# 3. The rest live in SPAL (Supplementary Packages for Amazon Linux) —
#    enable it, then install as normal
sudo dnf install -y python3.11  # example: SPAL packages install like any other dnf package once the repo is present
```

Check which bucket your package landed in with a plain search before assuming it's gone:

```bash
dnf search <package-name>
dnf list --available | grep <package-name>
```

If `dnf search` and `dnf list --available` both come up empty, it's likely an EPEL-only package now (see the related [`Unable to find a match`](https://eolkits.com/fix/amazon-linux-2023-dnf-unable-to-find-a-match/) error for that case) rather than an extras casualty.

## Fixing the automation, not just the instance

The one-off fix is deleting the `amazon-linux-extras` line from whatever's broken right now. The durable fix is finding every place that assumption is baked in before it breaks the next build:

```bash
grep -rl "amazon-linux-extras" Dockerfile* user-data/ ansible/ packer/ cloud-init/
```

Replace each hit with the direct `dnf install` (or version-namespaced equivalent) for that package, and drop the `amazon-linux-extras enable ...` step entirely — AL2023 has no topic to enable against.

---

This is one piece of the broader Amazon Linux 2 → 2023 migration (package manager, firewall, time sync, and Python version all shift at once) — the full checklist is at **[eolkits.com/fix/amazon-linux-2-eol](https://eolkits.com/fix/amazon-linux-2-eol/)**. If you want to know which instances in your account are still on AL2 before support ends, the free **[EOLkits scanner](https://eolkits.com/scan)** checks in about 30 seconds — nothing uploaded, and I maintain it.
