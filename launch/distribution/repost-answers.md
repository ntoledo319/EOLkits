# Turnkey "buyer burst" — helpful answers to real, live high-intent questions

Each item below is a **real person asking about this exact EOL right now**. Posting a genuinely useful answer
(with the tool mentioned once, disclosed) is the closest-to-a-buyer, $0, TOS-clean move that exists — and it's a
**one-time ~10–15 min** effort, not ongoing. The agent drafted these (it may not post as you); **you paste them.**

**Keep it clean & on-brand (so it helps, doesn't get flagged):**
- Answer the question **substantively first**; mention the free tool **once**, as a resource, and **disclose** you maintain it.
- **Do not paste the same text twice** — re:Post / Stack Overflow flag duplicate self-promotion. Each answer below is already unique.
- Use the AWS-official dates in these drafts (many blogs are stale — that's part of the value you're adding).
- **Links:** `/scan/` and `/amazon-linux-2-eol-checklist/` and `/fix/` are **live now**; `/eol-checker/` goes live on the next deploy (tonight) — if you post before then, drop that one link.

---

## 1 — AWS re:Post: "Amazon Linux 2 End of Life Migration"
**Post at:** https://repost.aws/questions/QUjhyVpUEPShyFSWrWT3mICw/amazon-linux-2-end-of-life-migration

> Amazon Linux 2 reached end of **standard support on June 30, 2026** — it no longer receives security patches, so the priority is getting off it (AWS's paid Extended Support is only a stopgap). The target is **Amazon Linux 2023**, and the things that actually break in practice are:
>
> - **Package manager:** `yum` → `dnf`. `amazon-linux-extras` is gone — packages are now default, version-namespaced (`dnf install python3.11`, `nginx1.24`), or in **SPAL** (which replaces EPEL).
> - **Time sync:** `ntpd` → `chronyd`.
> - **Firewall:** the `iptables-services` unit isn't installed by default — AL2023 uses **nftables**.
> - **Python 2** isn't available at all.
> - **cloud-init / user-data** written for AL2 often fails on first boot for the reasons above.
>
> A safe path: (1) snapshot/AMI first; (2) rebuild your base AMI on AL2023 (Packer helps); (3) port user-data + Ansible/config; (4) canary a small % behind a health check before the whole fleet; (5) keep a rollback AMI.
>
> To find your exposure quickly, I maintain a **free, open-source** scanner + browser tool (no signup, nothing uploaded) that flags AL2 AMIs/user-data and the specific breakages, plus a step-by-step AL2→AL2023 checklist: https://eolkits.com/scan/ and https://eolkits.com/amazon-linux-2-eol-checklist/ . *(Disclosure: I built these; the CLIs are MIT on GitHub.)* If you hit a specific error there are per-error fix pages (e.g. `dnf: Unable to find a match`).

---

## 2 — AWS re:Post: "AWS Lambda Python runtime 3.9 EoL"
**Post at:** https://repost.aws/questions/QUwvZZcO78S2iFe9UF6rK4nw/aws-lambda-python-runtime-3-9-eol

> Worth clearing up the dates first, because they've moved and most blog posts are stale: `python3.9` was **deprecated on 2025-12-15** (no more security patches). AWS originally set the create/update block dates for early 2026, then **delayed them** — per the current [AWS Lambda runtime deprecation table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) the block-create date is **2027-02-01** and block-update is **2027-03-03**. Since AWS has moved these before, treat that table as the source of truth — but either way it's already unpatched, so migrate now.
>
> Target is **python3.12** (3.13 is available). The breakages that actually bite on 3.9 → 3.12:
> - `distutils` and `imp` are **removed** (`ModuleNotFoundError`) — use `setuptools` / `importlib`.
> - `collections.Mapping` etc. moved to `collections.abc`.
> - **Native wheels:** anything with C extensions needs a `cp312` wheel built for Amazon Linux 2023 (glibc), or you get an import error at cold start.
> - `datetime.utcnow()` is deprecated.
>
> Find every function on 3.9 across regions (Trusted Advisor's "Lambda Functions Using Deprecated Runtimes" check, or `aws lambda list-functions --query "Functions[?Runtime=='python3.9']"`), fix the code, then update the runtime with a canary + a CloudWatch alarm to auto-rollback.
>
> I maintain a **free, open-source** CLI + browser checker that scans for exactly these and codemods the mechanical parts: https://eolkits.com/scan/ . *(Disclosure: I built it — MIT.)* There are also fix pages for the specific errors (e.g. `No module named 'distutils'`).

---

## 3 — AWS re:Post: "Amazon Linux 2 motd says EOL is 2025-06-30"
**Post at:** https://repost.aws/questions/QU8_7ivy19Q7Wq3CKUE5b7Jw/amazon-linux-2-motd-says-eol-is-2025-06-30

> That motd is stale — AWS **extended** Amazon Linux 2's end of life. The old date was **2025-06-30** (what your motd shows); the final date was **June 30, 2026**, and it has now passed, so AL2 is out of standard support and no longer getting patches. AWS's announcement: https://aws.amazon.com/blogs/aws/update-on-amazon-linux-2-end-of-life/ .
>
> Practically: if you're still on AL2 you're now unpatched. Options are AWS's **paid Extended Support** (a bridge, not a fix) or migrating to **Amazon Linux 2023** (the real move) — the main gotchas are `yum`→`dnf`, `amazon-linux-extras` gone (use dnf/SPAL), `ntpd`→`chronyd`, and nftables instead of the iptables service. A **free** browser tool to check your specific exposure (nothing uploaded): https://eolkits.com/scan/ . *(Disclosure: I maintain it.)*

---

## Optional next targets (search these, answer only if genuinely helpful)
- Stack Overflow: `[amazon-linux] end of life`, `nodejs20.x lambda deprecated`, `No module named 'distutils' lambda`
- AWS re:Post tag: https://repost.aws/tags/questions/TAl4y_oRX1RjmpJJGVndhKtA (Amazon Linux)
- Each answer must be **unique** and **help-first**. One good answer > ten copy-pasted ones.
