# Runbook: delete a person's lead data

Use this when someone asks you to delete what they sent through a contact form
(any Toledo site, or eolkits.com), or when a lead row must go for any other
reason.

## Where a lead lives

| Place | What it holds | Removed by this runbook? |
|---|---|---|
| `leads` table in `/data/eolkits/state.sqlite3` inside the `eolkits-api` container | email, name, product, source, and every form field (stored up to 4,000 characters) | **Yes**: the CLI below |
| The `LEAD_NOTIFY_TO` mailbox (default `hello@toledotechnologies.com`) | one "New lead: ..." or "Likely spam: New lead: ..." email per alerted lead and recipient, from `noreply@eolkits.com`, with every field. Leads screened as spam or duplicate get none | **No**: delete by hand (step 4) |
| Resend (the email provider) | its own log of each notification email | **No**: check the Resend dashboard and Resend's current retention terms |
| Database backups and volume snapshots (for example `~/backups/eolkits-state.backup-*.sqlite3` and `/home/ubuntu/backups/eolkits/*.tgz` on the server) | full copies of the database at the time they were taken | **No**: step 5 |
| `events` table | one `lead` row per lead: lead id, product, source. No contact details | Not needed |
| Container logs | lead ids and the owner's alert address. The lead code does not log visitor details | Not needed |

## Steps

Run these on the server as the deploy user (prefix `docker` with `sudo` if that
user is not in the `docker` group). Deleting rows does not restart anything and
is safe while the API is serving.

1. **Preview.** Nothing changes.

   ```bash
   docker exec eolkits-api python -m eolkits_grace.lead_admin delete --email person@example.com --dry-run
   ```

   Matching ignores letter case (A to Z) and stray spaces around the stored
   address. The output lists the matching row ids, dates and product, never the
   form contents. It also lists **other** rows that mention the address in their
   name or form fields. Those are usually a colleague writing on the person's
   behalf.

2. **Delete.** The same command without `--dry-run`:

   ```bash
   docker exec eolkits-api python -m eolkits_grace.lead_admin delete --email person@example.com
   ```

   Expect `Deleted N lead row(s).` and
   `Database file updated (WAL checkpoint complete).` If it says the checkpoint
   did not finish, run the same command again a minute later. It will match
   nothing and retry the checkpoint.

3. **Other rows.** If step 1 listed other rows that belong to this person,
   delete them by id:

   ```bash
   docker exec eolkits-api python -m eolkits_grace.lead_admin delete --id 41 --id 42
   ```

4. **The mailbox.** In the `LEAD_NOTIFY_TO` mailbox, search for the address.
   The notifications have the subject `New lead: ...` or
   `Likely spam: New lead: ...`. Delete those emails, then empty them from Trash
   too. The CLI cannot reach email.

5. **Backups.** Copies taken before the deletion still hold the rows. List what
   exists (`ls -l ~/backups /home/ubuntu/backups/eolkits`) and delete the copies
   you no longer need for rollback. Keep a copy only as long as its rollback
   purpose lasts; if you restore one, repeat steps 1 to 3 afterwards.

## How the delete works

- Everything runs in one database transaction, so the rows it reports are
  exactly the rows it removed.
- SQLite `secure_delete` is on for the delete, so the row content is
  overwritten, not just unlinked. A WAL checkpoint then writes the result into
  the database file. The checkpoint never waits on other work; if the API is
  busy it reports that and you re-run the command.
- The CLI opens the existing database only. It refuses to run if there is no
  database at the path (it will not create an empty one) and never changes the
  schema.
- Exit codes: `0` done (including "matched 0"), `1` no database found (you are
  not inside the container, or `EOLKITS_DATA_DIR` is wrong), `2` bad input
  (or `purge` with retention off and no `--days`).

## Retention (optional, off by default)

`EOLKITS_LEAD_RETENTION_DAYS` in `.env.production` controls automatic deletion.
Unset or `0` keeps leads until you delete them (the code default). A positive
number N makes the API delete leads older than N days, once at startup and then
every hour, in the same way as the delete above. Production sets `730` (two
years; see `deploy/grace/README.md`). Rows screened as spam or duplicate are
kept and deleted on the same schedule as every other lead. A value that is not
a whole number from 0 to 36500 stops the API at startup with a message naming
the variable.

Preview what a given period would delete, without deleting anything:

```bash
docker exec eolkits-api python -m eolkits_grace.lead_admin purge --days 365 --dry-run
```

`purge --dry-run` without `--days` shows what the current setting deletes, or
says retention is off.

The API reads the setting at startup. Changing it means recreating the
container, which is a restart: plan it like a deploy and get the go-ahead
first. Update the privacy notices on the sites to match the period you choose.
