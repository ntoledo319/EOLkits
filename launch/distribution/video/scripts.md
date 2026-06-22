# Faceless short-video scripts (YouTube Shorts / TikTok)

For GRACE's `media_manager` (ffmpeg + Piper TTS faceless render) or manual. ~30–45s each,
screen-recording of the free scanner + captions. Channel fit: YouTube Shorts > TikTok for a
dev audience. Each ends on eolkits.com/scan.

---

## Short 1 — "AWS is about to brick your servers" (AL2)
- HOOK (0–3s): "Amazon Linux 2 dies June 30th. If you're still on it, your servers stop getting security patches — permanently."
- BODY (3–25s): screen-rec dropping a Terraform file on eolkits.com/scan → findings table lights up (AL2 AMI, yum, amazon-linux-extras). "yum's gone. extras is gone. ntpd's gone. Python 2's gone."
- CTA (25–35s): "Scan your own stack free — nothing gets uploaded. Link in bio. eolkits.com/scan"

## Short 2 — "This one line breaks every Lambda upgrade" (Node)
- HOOK: "Upgrading a Lambda to Node 22 and getting `Cannot find module 'aws-sdk'`? It's not your code."
- BODY: "AWS stopped bundling the v2 SDK on Node 18+. Only v3 ships now." show the fix. "Plus native addons need rebuilding and OpenSSL 3 breaks old hashing."
- CTA: "Free scanner finds all of it in 30 seconds → eolkits.com/scan"

## Short 3 — "Python 3.12 deleted these" (Python)
- HOOK: "`No module named 'distutils'` after moving a Lambda to Python 3.12? Python deleted it."
- BODY: "distutils, imp, and the collections ABCs are gone in 3.12. Here's the 1-line fix for each." show fixes.
- CTA: "Check your functions free → eolkits.com/scan"

---
**Gate to auto-produce:** TikTok/YouTube API creds + `ffmpeg` + `Piper` on the box (I can install
ffmpeg/Piper; creds are yours). Lower priority than dev.to — weaker B2B fit, more setup.
