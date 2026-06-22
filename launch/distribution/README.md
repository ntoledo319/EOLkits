# EOLkits — Autonomous Distribution Kit (prepared)

_Everything here is built and dry-run-ready. Each lever is **one credential away** from firing,
then runs autonomously (I can wire it into the same box cron as the daily site deploy)._

This is the salvageable core of the empire's "GRACE distributes autonomously" bet. The empire's
**bulk cold-outreach** engine was deliberately removed in GRACE's rebuild (deliverability/compliance)
and is **not** revived here. What's prepared instead is **own-content publishing** (legit, builds the
backlinks the new domain lacks) + a **surgical** value-first email option.

---

## What's prepared

| Lever | Files | Status | What it does |
|---|---|---|---|
| **dev.to / Hashnode** (★ top ROI) | `devto/publish_devto.py` + 3 articles | ready, dry-run | Publishes your own articles with `canonical_url` → **backlinks + dev reach**, the exact thing capping the revenue projection |
| **X / Twitter** | `x/threads.md` | content ready | Deadline alerts + fix tips (own content) for the dev crowd |
| **Value-first email** | `email/template.md`, `targets.md`, `send_value_first.py` | ready, dry-run, capped | Surgical, true, opt-out B2B "found money" emails. Risky — separate sending subdomain enforced |
| **Faceless video** | `video/scripts.md` | scripts ready | YouTube Shorts / TikTok via GRACE `media_manager` |

All scripts are **dry-run by default** and refuse to do anything destructive/outward without `--apply`.

---

## ⭐ WHAT I NEED FROM YOU (ranked — do the first one and stop if that's all you've got)

**1. A dev.to API key — 2 minutes, free. This is the one that matters.**
   - dev.to → Settings → Extensions → "DEV Community API Keys" → Generate.
   - Paste it to me (or drop it on the box as `DEVTO_API_KEY`).
   - Then I publish the 3 articles + wire `publish_devto.py` into the daily cron so new content
     auto-cross-posts forever. **This builds the backlinks/authority that move first-dollar from
     "months / maybe never" to "weeks."** Highest leverage by far.

**2. ~~Hashnode~~ — its publishing API went PAID on 2026-05-13** (the endpoint now 301s to a
   "graphql-api-paid-access" notice). `publish_hashnode.py` is ready if you ever turn on paid API
   access; otherwise skip — not a free lever anymore.

**3. (Optional, higher-risk) Greenlight the value-first email** — needs:
   - a **separate sending subdomain** (e.g. `mail.eolkits.com`) with its own SPF/DKIM/DMARC, **or**
     confirmation I can use GRACE's SMTP from a non-apex identity, plus `SMTP_*` creds, and
   - your "go" — it's outward-facing, so I show you the exact emails first and never send without it.
   - Honest: targets are mostly OSS samples (low conversion). Long shot, not the engine.

**4. (Optional, low priority) X auto-post** — X's write API is paid (~$100/mo). Skip unless you
   already have access; the content's ready either way.

**5. (Optional, later) YouTube/TikTok creds** — then I install `ffmpeg`/`Piper` on the box and
   GRACE auto-renders the shorts. Weaker B2B fit; do it after dev.to proves out.

---

## How it fires once unlocked
- **dev.to:** `DEVTO_API_KEY=... python3 devto/publish_devto.py --apply` → I then add it to
  `/home/ubuntu/bin/deploy-eolkits-web`'s nightly run so fresh content auto-publishes.
- **email:** I assemble a hand-verified `targets.tsv`, you review the drafts, then
  `--apply` sends ≤15/day throttled from the subdomain.
- **video:** GRACE `media_manager` renders + posts on a schedule.

## Bottom line
The autonomous machine is built and self-deploying. Distribution is now gated on **one free API key**,
not on your time. Hand me the **dev.to key** and the projection's biggest constraint (zero backlinks)
starts dissolving the same day.
