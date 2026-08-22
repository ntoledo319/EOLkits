---
title: "Failed to start ntpd.service — Amazon Linux 2023 replaced it with chrony"
canonical_url: https://eolkits.com/fix/amazon-linux-2023-ntpd-service-not-found/
description: User-data, cloud-init, or Ansible that enables ntpd.service fails on Amazon Linux 2023 with "Unit ntpd.service not found." Here's why, and how to move to chrony.
tags: aws, linux, devops, sysadmin
---

You moved an AMI, launch template, or Ansible playbook from Amazon Linux 2 to Amazon Linux 2023, and time-sync provisioning that used to just work now fails:

```
Failed to start ntpd.service: Unit ntpd.service not found.
```

The instance boots fine, `dnf` works, but whatever enabled or started `ntpd.service` — user-data, cloud-init, a Packer build, a config-management run — has nothing to attach to.

## Why this happens

Amazon Linux 2 shipped `ntp`/`ntpd` for time synchronization. Amazon Linux 2023 doesn't install that package or unit by default — it standardizes on **chrony** (`chronyd`) instead, the same time-sync daemon most modern Linux distros have already moved to. Anything that assumes `ntpd.service` exists — a `systemctl enable --now ntpd` line baked into a golden AMI, a cloud-init runcmd, an Ansible task targeting `ntp.conf` — has no unit to enable on AL2023.

## The fix

```bash
# Install and enable chrony (often already present on AL2023 AMIs — check first)
sudo dnf install -y chrony
sudo systemctl enable --now chronyd

# Verify it's syncing
chronyc sources
chronyc tracking
```

If you had custom NTP servers configured in `/etc/ntp.conf`, migrate the `server`/`pool` lines to `/etc/chrony.conf` (chrony's syntax is close enough that most entries port over as-is — just double-check any `iburst`/`prefer` flags still parse).

## Fixing the automation, not just the instance

A one-time fix on a running instance doesn't help if the same user-data or Ansible role provisions the next hundred instances off a stale AL2 assumption. Grep provisioning code for the old unit name and update it once at the source:

```bash
grep -rl "ntpd.service\|ntp\.conf\|dnf install.*ntp[^d]\|yum install.*ntp[^d]" user-data/ ansible/ packer/
```

Replace `systemctl enable --now ntpd` with `systemctl enable --now chronyd`, and drop any `dnf install ntp` line — that package isn't what AL2023 uses for this.

---

This is one piece of the broader Amazon Linux 2 → 2023 migration (package manager, firewall, time sync, and Python version all shift at once) — the full checklist is at **[eolkits.com/fix/amazon-linux-2-eol](https://eolkits.com/fix/amazon-linux-2-eol/)**. If you want to know which instances in your account are still on AL2 before support ends, the free **[EOLkits scanner](https://eolkits.com/scan)** checks in about 30 seconds — nothing uploaded, and I maintain it.
