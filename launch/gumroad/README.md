# Gumroad bundle — Bet A′ (fast, low-ticket)

Everything an owner needs to list the "AWS Runtime EOL Migration Toolkit" on Gumroad, built in-jail, $0 spend.

- **`MIGRATION-PLAYBOOK.md`** — the value-add content that goes inside the bundle (not just the free CLIs).
- **`ATTRIBUTIONS.md`** — the license/provenance disclosure that goes inside the bundle (§9 pre-publish gate).
- **`LISTING-COPY.md`** — the entire Gumroad listing, ready to paste, plus the exact publish steps.
- **`build_bundle.sh`** — assembles the zip from the current kit sources + the two docs above. Run it before every
  publish/republish so the bundle always reflects the latest kit code:
  ```bash
  bash launch/gumroad/build_bundle.sh
  ```
  Output: `launch/gumroad/dist/eolkits-migration-toolkit.zip` (gitignored — regenerate, don't hand-edit or commit).

**Owner's only remaining step:** HUMAN_QUEUE HQ-1′ (create the Gumroad account) + HQ-2′ (run the script above,
upload the zip, paste `LISTING-COPY.md`, click publish). See `LISTING-COPY.md` for the full walkthrough.
