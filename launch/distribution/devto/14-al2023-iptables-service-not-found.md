---
title: "Failed to start iptables.service — Amazon Linux 2023 dropped it for nftables"
canonical_url: https://eolkits.com/fix/amazon-linux-2023-iptables-service-not-found/
description: User-data, cloud-init, or Ansible that enables iptables.service fails on Amazon Linux 2023 with "Unit iptables.service not found." Here's why, and how to move to nftables.
tags: aws, linux, devops, security
---

> [!CAUTION]
> Archived launch copy — do not publish or reuse. This draft predates the current
> bounded browser scanner, telemetry disclosure, lifecycle-date corrections, and
> readiness-gated paid scope; claims and `eolkits.com` links below may be false or stale.
> Use the [current README](../../../README.md) and
> [verified public site](https://ntoledo319.github.io/EOLkits/) instead.

You moved an AMI, launch template, or Ansible playbook from Amazon Linux 2 to Amazon Linux 2023, and a step that used to just work now fails:

```
Failed to start iptables.service: Unit iptables.service not found.
```

The instance is healthy, `dnf` works, but whatever enabled or started `iptables.service` — user-data, cloud-init, a Packer build, a config-management run — breaks on first boot.

## Why this happens

On Amazon Linux 2, the `iptables-services` package provided an `iptables.service` unit that saved and restored firewall rules across reboots (`iptables-save` / `iptables-restore` under systemd). Amazon Linux 2023 doesn't install that package or unit by default — it standardizes on **nftables** as the default firewall backend instead. Anything that assumes `iptables.service` exists — a `systemctl enable --now iptables` line baked into a golden AMI, a cloud-init runcmd, an Ansible task — has nothing to attach to on AL2023.

The `iptables` command itself isn't gone (there's an `iptables-nft` compatibility layer), but the systemd unit your automation expects is.

## The fix, two ways

**Move to native nftables (recommended for anything new):**

```bash
# Convert existing iptables rules to nftables syntax
sudo iptables-save > /tmp/rules.v4
sudo iptables-translate -f /tmp/rules.v4 > /etc/nftables/rules.nft   # per-rule; wrap in a table/chain if starting fresh

# Enable and start the nftables service instead of iptables.service
sudo systemctl enable --now nftables

# Verify
sudo nft list ruleset
```

`iptables-translate` converts rules one at a time — for anything beyond a handful of rules, review the generated nftables syntax rather than trusting a blind bulk conversion.

**Keep iptables syntax via the compatibility layer (faster migration, same commands):**

```bash
sudo dnf install -y iptables-nft
```

Rules written with `iptables`/`ip6tables` commands are transparently stored in the nftables backend. You keep your existing `iptables -A ...` scripts, but **persistence is managed by the `nftables` service**, not `iptables.service` — update any `systemctl enable iptables` reference to `systemctl enable nftables`.

## Fixing the automation, not just the instance

The one-time instance fix doesn't help if the same user-data or Ansible role provisions the next hundred instances. Grep your provisioning code for the old assumption and update it once at the source:

```bash
grep -rl "iptables.service\|iptables-services" user-data/ ansible/ packer/
```

Replace `systemctl enable --now iptables` with `systemctl enable --now nftables` (or the `iptables-nft` equivalent), and drop any `dnf install iptables-services` line — that package doesn't exist on AL2023.

---

This is one piece of the broader Amazon Linux 2 → 2023 migration (package manager, firewall, time sync, and Python version all shift at once) — the full checklist is at **[eolkits.com/fix/amazon-linux-2-eol](https://eolkits.com/fix/amazon-linux-2-eol/)**. If you want to know which instances in your account are still on AL2 before support ends, the free **[EOLkits scanner](https://eolkits.com/scan)** checks in about 30 seconds — nothing uploaded, and I maintain it.
