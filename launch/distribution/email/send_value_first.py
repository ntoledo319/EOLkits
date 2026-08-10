#!/usr/bin/env python3
"""Value-first outreach sender — DRY-RUN by default.

Sends one personalized, true, opt-out-able email per target via SMTP. Built to be
safe: low daily cap, throttled, refuses to send from the apex domain (protects the
Resend pipe that delivers audits). Cold email is the riskiest lever — the GRACE
rebuild quarantined the bulk version on purpose. Surgical use only, or skip it.

Targets file (TSV, one per line, # = comment):
  email <TAB> maintainer <TAB> repo <TAB> finding <TAB> fix

Env (use a SEPARATE sending subdomain, e.g. nick@mail.eolkits.com — NEVER the apex):
  SMTP_HOST  SMTP_PORT(=587)  SMTP_USER  SMTP_PASS  MAIL_FROM

Usage:
  python3 send_value_first.py targets.tsv           # dry run, sends nothing
  python3 send_value_first.py targets.tsv --apply   # send (capped + throttled)
"""
import os
import sys
import ssl
import time
import smtplib
from email.message import EmailMessage

DAILY_CAP = 15
THROTTLE_SECONDS = 45
SUBJECT = "{repo} pins {finding_short} — heads-up before the AWS cutoff"
BODY = """Hi {maintainer},

I was scanning public infra-as-code for AWS end-of-life exposure and {repo} came up:

  {finding}

Not selling you anything — just didn't want it to bite you in prod. The fix:

  {fix}

If it's useful, there's a free scanner that flags the rest of your stack in ~30s
(in-browser, nothing uploaded): https://eolkits.com/scan

— Nick / EOLkits

Don't want infra heads-ups like this? Reply "stop" and I won't email again.
"""


def main():
    if len(sys.argv) < 2:
        print("usage: send_value_first.py <targets.tsv> [--apply]")
        sys.exit(1)
    apply = "--apply" in sys.argv
    frm = os.environ.get("MAIL_FROM", "")
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    pw = os.environ.get("SMTP_PASS", "")
    if apply and not (frm and host and user and pw):
        print("ERROR: set SMTP_HOST/SMTP_USER/SMTP_PASS/MAIL_FROM (use a separate sending subdomain)")
        sys.exit(1)
    if apply and "eolkits.com" in frm and "mail.eolkits.com" not in frm and "@eolkits.com" in frm:
        print("REFUSING: MAIL_FROM is the apex domain — that would risk the audit-delivery pipe. Use a subdomain.")
        sys.exit(1)
    rows = []
    for line in open(sys.argv[1], encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 5:
            rows.append(parts[:5])
    server = None
    if apply:
        server = smtplib.SMTP(host, port, timeout=30)
        server.starttls(context=ssl.create_default_context())
        server.login(user, pw)
    sent = 0
    for email_addr, maintainer, repo, finding, fix in rows:
        if sent >= DAILY_CAP:
            print(f"daily cap {DAILY_CAP} reached — stopping")
            break
        fshort = (finding[:40] + "...") if len(finding) > 43 else finding
        subj = SUBJECT.format(repo=repo, finding_short=fshort)
        body = BODY.format(maintainer=maintainer, repo=repo, finding=finding, fix=fix)
        if not apply:
            print(f"DRY -> {email_addr}\n  {subj}\n")
            continue
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = frm, email_addr, subj
        msg.set_content(body)
        server.send_message(msg)
        sent += 1
        print(f"sent -> {email_addr} ({sent}/{DAILY_CAP})")
        time.sleep(THROTTLE_SECONDS)
    if server:
        server.quit()
    if not apply:
        print("\nDry run. Re-run with --apply once SMTP + a SEPARATE sending subdomain are configured.")


if __name__ == "__main__":
    main()
