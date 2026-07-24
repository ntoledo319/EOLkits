---
title: "Error: Unable to find a match — fixing dnf package lookups after migrating off Amazon Linux 2"
canonical_url: https://eolkits.com/fix/amazon-linux-2023-dnf-unable-to-find-a-match/
description: A yum/dnf install that worked on Amazon Linux 2 fails with "Unable to find a match" on Amazon Linux 2023. Why package names changed and how to find the real one.
tags: aws, linux, devops, dnf
---

You moved an instance, AMI, or user-data script from Amazon Linux 2 to Amazon Linux 2023, and a package install that's worked for years suddenly fails:

```
Error: Unable to find a match: python3-devel
```

(or whatever package your script names). The instance boots fine, `dnf` works, but this one package is gone.

## Why this happens

Amazon Linux 2023's repositories aren't the same tree as AL2's — they were rebuilt, and along the way packages got renamed, version-namespaced, moved to a supplementary repo, or dropped outright:

- **Version-namespaced.** AL2023 ships multiple versions of things side by side instead of one default, so the plain name is gone in favor of a versioned one: `python3` → `python3.11` (or `python3.12`), `nginx` → `nginx1.24`, `postgresql` → `postgresql15`.
- **Moved out of the base repo.** Packages that lived in `amazon-linux-extras` on AL2 (which doesn't exist on AL2023 at all) are now either default `dnf` packages, version-namespaced ones, or live in **SPAL** (Supplementary Packages for Amazon Linux) — a repo you have to enable separately.
- **Moved to EPEL.** Some AL2 packages were never Amazon's to begin with and only ever came from EPEL; if your script assumed they'd resolve from the base AL2023 repos, they won't until EPEL is enabled.
- **Actually removed.** A handful of packages just aren't packaged for AL2023 at all.

Scripts that hardcode an AL2-era name and run `yum install <name>` (which on AL2023 is a symlink straight to `dnf`) hit this the moment they run against the new repo set.

## Finding the real name

Don't guess — ask dnf directly:

```bash
# Search by keyword
dnf search python3-devel

# Search by the actual binary/file you need, if you know it
dnf provides '*/pip3'
dnf provides '*/nginx'
```

`dnf provides` is the more reliable of the two when you know the file the old package used to install (a binary, a `.so`, a config path) but not what the new package is called.

## The fix, by cause

**Version-namespaced package:** install the versioned name directly.

```bash
dnf install -y python3.11 python3.11-devel   # or python3.12
dnf install -y nginx1.24
dnf install -y postgresql15 postgresql15-server
```

**Used to come from `amazon-linux-extras`:** that command doesn't exist on AL2023 — there's nothing to enable it against. Check whether the package is now a default `dnf` package, a version-namespaced one, or lives in SPAL:

```bash
dnf repository-packages amazon-linux-extras-equivalent-repo list  # naming varies by topic; check SPAL docs for the exact repo id
```

In practice most former `amazon-linux-extras` topics (nginx, php, docker CLIs, etc.) are just direct or version-namespaced `dnf install`s on AL2023 now — the extras layer was there because AL2's base repo shipped one old version of everything; AL2023's doesn't have that constraint.

**Genuinely EPEL-only:** enable EPEL for AL2023, then install normally.

```bash
dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
dnf install -y <package>
```

(Confirm the EPEL release package that matches AL2023's current EPEL support before pinning a version — the AL2023 user guide documents which EPEL release to use.)

**Actually dropped, no replacement:** vendor a static binary, build from source against AL2023's toolchain, or containerize the workload instead of installing it as a system package.

## Before you standardize on a name

AL2023 versions packages more aggressively than AL2 did, which means today's `python3.11` might not be tomorrow's default. Check a package's support window before hardcoding it into a golden AMI or long-lived user-data script:

```bash
dnf install -y dnf-plugin-support-info
dnf support-info <package>
```

That tells you how long the specific package version is supported — useful for avoiding a repeat of this exact migration in a couple of years.

---

This is one piece of the broader Amazon Linux 2 → 2023 migration (package manager, firewall, time sync, and Python version all shift at once) — the full checklist is at **[eolkits.com/fix/amazon-linux-2-eol](https://eolkits.com/fix/amazon-linux-2-eol/)**. If you want to know which instances in your account are still on AL2 before support ends, the free **[EOLkits scanner](https://eolkits.com/scan)** checks in about 30 seconds — nothing uploaded, and I maintain it.
