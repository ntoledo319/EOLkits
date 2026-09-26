"""Operator tools for the `leads` table. Run inside the eolkits-api container:

    docker exec eolkits-api python -m eolkits_grace.lead_admin delete --email person@example.com --dry-run
    docker exec eolkits-api python -m eolkits_grace.lead_admin delete --email person@example.com
    docker exec eolkits-api python -m eolkits_grace.lead_admin delete --id 41 --id 42
    docker exec eolkits-api python -m eolkits_grace.lead_admin purge --dry-run
    docker exec eolkits-api python -m eolkits_grace.lead_admin purge --days 365 --dry-run
    docker exec eolkits-api python -m eolkits_grace.lead_admin list --since 2026-09-01 --status suspect
    docker exec eolkits-api python -m eolkits_grace.lead_admin reclassify --dry-run

`delete` removes one person's lead rows (matched on the stored email, ignoring
A-Z letter case and surrounding spaces) and/or specific rows by id. `purge`
removes rows older than N days, where N defaults to EOLKITS_LEAD_RETENTION_DAYS;
it is the same purge the running API applies in its retention sweep when that
setting is on.

`list` shows lead rows with their screening status (ok, suspect, spam,
duplicate) and why, never what the visitor wrote unless --show-message is
given. `reclassify` applies the current screening rules to the rows already
stored; it changes the status only and never deletes or edits a row.

None of these commands touches email. The owner-notification emails for a lead
live in the LEAD_NOTIFY_TO mailbox and must be deleted there separately.

See deploy/grace/runbooks/lead-deletion.md and deploy/grace/README.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from typing import Any, TextIO

from .config import settings
from .store import LEAD_ALERT_STATUSES, LEAD_STATUSES, Store

MAILBOX_REMINDER = (
    "Reminder: this does not touch email. Delete this person's owner-notification "
    'emails (subject "New lead: ..." or "Likely spam: New lead: ...") from the '
    "LEAD_NOTIFY_TO mailbox separately."
)
NO_STATUS_COLUMN = (
    "This database has no lead screening status yet. The API adds it when the "
    "version with lead screening starts; run this again after that deploy."
)


def _open_store(out: TextIO) -> Store | None:
    # Refuse to run against a path with no database: sqlite would quietly create
    # an empty one, and "deleted 0 rows" there would be a false answer. The
    # store is opened without running its schema migrations; the API owns those.
    path = settings.db_path
    if path.is_symlink() or not path.is_file():
        print(
            f"No lead database at {path}. Run this inside the eolkits-api container, "
            "or set EOLKITS_DATA_DIR to the directory that holds state.sqlite3.",
            file=out,
        )
        return None
    print(f"Database: {path}", file=out)
    return Store(path, initialize=False)


def _clean(value: Any, limit: int | None = None) -> str:
    """Form text made safe to print in a terminal: control and formatting
    characters (escape sequences, bidi overrides) are shown as \\u escapes."""
    text = str(value if value is not None else "")
    if limit is not None and len(text) > limit:
        text = text[: limit - 3] + "..."
    return "".join(ch if ch.isprintable() else f"\\u{ord(ch):04x}" for ch in text)


def _describe(rows: list[dict[str, Any]]) -> str:
    return ", ".join(
        f"id {row['id']} ({str(row['ts'])[:10]}, "
        f"{_clean(row.get('product') or row.get('source') or 'no product', 80)})"
        for row in rows
    )


def _when(ts: Any) -> str:
    return str(ts or "")[:16].replace("T", " ")


def _finish_erasure(store: Store, out: TextIO) -> None:
    if store.checkpoint_wal():
        print("Database file updated (WAL checkpoint complete).", file=out)
    else:
        print(
            "The rows are deleted, but the API was reading the database, so the WAL "
            "checkpoint did not finish and old copies may remain in the database file "
            "for now. Run the same command again in a minute: it will match nothing "
            "and retry the checkpoint.",
            file=out,
        )


def cmd_delete(args: argparse.Namespace, out: TextIO) -> int:
    email = args.email.strip() if args.email is not None else None
    if email is not None and "@" not in email:
        print(f"Not an email address: {args.email!r}", file=out)
        return 2
    if email is None and not args.id:
        print("Give --email or at least one --id.", file=out)
        return 2
    store = _open_store(out)
    if store is None:
        return 1
    result = store.delete_leads(email=email, ids=args.id or None, dry_run=args.dry_run)
    rows = result["matched"]
    target = " and ".join(
        part
        for part in (
            f"email {email}" if email else "",
            f"id {', '.join(map(str, args.id))}" if args.id else "",
        )
        if part
    )
    if rows:
        print(f"Matched {len(rows)} lead row(s) for {target}: {_describe(rows)}", file=out)
    else:
        print(f"Matched 0 lead rows for {target}.", file=out)
    if args.dry_run:
        print("Dry run: nothing was deleted.", file=out)
    else:
        print(f"Deleted {result['deleted']} lead row(s).", file=out)
        _finish_erasure(store, out)
    if email:
        others = store.lead_ids_mentioning(email, exclude_ids=[row["id"] for row in rows])
        if others:
            print(
                f"Also: {len(others)} other lead row(s) mention this address in their name or "
                f"form details but were sent from a different email "
                f"(id {', '.join(map(str, others))}). They were not deleted. Check them, and "
                "delete any that belong to this person with --id.",
                file=out,
            )
    print(MAILBOX_REMINDER, file=out)
    return 0


def cmd_purge(args: argparse.Namespace, out: TextIO) -> int:
    days = args.days if args.days is not None else settings.lead_retention_days
    if not days:
        print(
            "Lead retention is off (EOLKITS_LEAD_RETENTION_DAYS is unset or 0). "
            "Pass --days N to preview or purge once by hand.",
            file=out,
        )
        return 2
    store = _open_store(out)
    if store is None:
        return 1
    origin = "--days" if args.days is not None else "EOLKITS_LEAD_RETENTION_DAYS"
    cutoff = datetime.now(UTC) - timedelta(days=days)
    result = store.purge_leads_before(cutoff.isoformat(), dry_run=args.dry_run)
    print(
        f"Retention: {days} days (from {origin}). "
        f"Cutoff: {cutoff.strftime('%Y-%m-%d %H:%M')} UTC.",
        file=out,
    )
    print(f"Matched {result['matched']} lead row(s) captured before the cutoff.", file=out)
    if result["unnotified"]:
        print(f"{result['unnotified']} of them were never alerted to the owner.", file=out)
    if args.dry_run:
        print("Dry run: nothing was deleted.", file=out)
    else:
        print(f"Deleted {result['deleted']} lead row(s).", file=out)
        _finish_erasure(store, out)
    return 0


def _row_line(row: dict[str, Any], status: str, reason: str | None) -> str:
    return " | ".join(
        (
            f"id {row['id']}",
            _when(row["ts"]),
            status,
            _clean(row.get("product") or row.get("source") or "no product", 60),
            _clean(reason or "-", 120),
        )
    )


def _print_message(row: dict[str, Any], out: TextIO) -> None:
    stored = row.get("fields") or ""
    try:
        fields = json.loads(stored or "{}")
    except (TypeError, ValueError):
        fields = None
    if not isinstance(fields, dict):
        fields = {"(stored text, shortened)": stored}
    if not fields:
        print("    (no form fields)", file=out)
    for key, value in fields.items():
        lines = str(value).splitlines() or [""]
        print(f"    {_clean(key, 60)}: {_clean(lines[0])}", file=out)
        for line in lines[1:]:
            print(f"      {_clean(line)}", file=out)


def cmd_list(args: argparse.Namespace, out: TextIO) -> int:
    store = _open_store(out)
    if store is None:
        return 1
    if not store.has_lead_status():
        print(NO_STATUS_COLUMN, file=out)
        return 1
    counts: Counter[str] = Counter()
    for row in store.iter_leads(
        since=args.since, status=args.status, with_fields=args.show_message
    ):
        counts[row["status"]] += 1
        print(_row_line(row, row["status"], row["status_reason"]), file=out)
        if args.show_message:
            _print_message(row, out)
    listed = sum(counts.values())
    summary = ", ".join(f"{status} {counts[status]}" for status in LEAD_STATUSES if counts[status])
    scope = " and ".join(
        part
        for part in (
            f"captured on or after {args.since} UTC" if args.since else "",
            f"with status {args.status}" if args.status else "",
        )
        if part
    )
    print(
        f"Listed {listed} lead row(s){' ' + scope if scope else ''}"
        f"{': ' + summary if summary else ''}.",
        file=out,
    )
    if not args.show_message and listed:
        print("Form contents are not shown; add --show-message to see them.", file=out)
    return 0


def cmd_reclassify(args: argparse.Namespace, out: TextIO) -> int:
    store = _open_store(out)
    if store is None:
        return 1
    if not store.has_lead_status():
        print(NO_STATUS_COLUMN, file=out)
        return 1
    result = store.reclassify_leads(dry_run=args.dry_run)
    changes = result["changes"]
    verb = "would change" if args.dry_run else "to change"
    print(f"Checked {result['checked']} lead row(s); {len(changes)} {verb}.", file=out)
    for change in changes:
        print(
            "  "
            + _row_line(change, f"{change['old_status']} -> {change['status']}", change["reason"]),
            file=out,
        )
    if changes:
        moves = Counter((c["old_status"], c["status"]) for c in changes)
        print(
            "By change: "
            + ", ".join(f"{old} -> {new} {n}" for (old, new), n in sorted(moves.items()))
            + ".",
            file=out,
        )
    owed = [
        c
        for c in changes
        if c["status"] in LEAD_ALERT_STATUSES
        and c["old_status"] not in LEAD_ALERT_STATUSES
        and not c["notified"]
    ]
    if owed:
        print(
            f"{len(owed)} of them were never alerted to the owner and become alertable; "
            "the API's re-send sweep (at startup, then hourly) will alert the owner about them.",
            file=out,
        )
    if args.dry_run:
        print("Dry run: nothing was changed.", file=out)
        return 0
    print(
        f"Updated the status of {result['updated']} lead row(s). "
        "No row was deleted and no form data was changed.",
        file=out,
    )
    if result["updated"] < len(changes):
        print(
            f"{len(changes) - result['updated']} row(s) changed while this ran and were left "
            "as they are. Run reclassify again to re-check them.",
            file=out,
        )
    return 0


def _since_date(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {value!r}")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a real date: {value!r}") from None


def _positive_days(value: str) -> int:
    try:
        days = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a whole number: {value!r}") from None
    if not 1 <= days <= 36500:
        raise argparse.ArgumentTypeError("must be between 1 and 36500")
    return days


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m eolkits_grace.lead_admin",
        description="Review, screen and delete lead rows in the EOLkits lead database.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    delete = sub.add_parser("delete", help="delete one person's lead rows, or rows by id")
    delete.add_argument("--email", help="delete every lead row captured with this email address")
    delete.add_argument(
        "--id", type=int, action="append", help="delete this lead row id (repeatable)"
    )
    delete.add_argument(
        "--dry-run", action="store_true", help="show what would be deleted, change nothing"
    )
    delete.set_defaults(func=cmd_delete)

    purge = sub.add_parser("purge", help="delete lead rows older than the retention period")
    purge.add_argument(
        "--days",
        type=_positive_days,
        help="age limit in days (default: EOLKITS_LEAD_RETENTION_DAYS)",
    )
    purge.add_argument(
        "--dry-run", action="store_true", help="show what would be deleted, change nothing"
    )
    purge.set_defaults(func=cmd_purge)

    listing = sub.add_parser(
        "list", help="list lead rows with their screening status (no form contents)"
    )
    listing.add_argument(
        "--since", type=_since_date, help="only rows captured on or after this UTC date"
    )
    listing.add_argument("--status", choices=LEAD_STATUSES, help="only rows with this status")
    listing.add_argument(
        "--show-message",
        action="store_true",
        help="also print each row's form fields (what the visitor wrote)",
    )
    listing.set_defaults(func=cmd_list)

    reclassify = sub.add_parser(
        "reclassify",
        help="apply the screening rules to stored rows (status only, never deletes)",
    )
    reclassify.add_argument(
        "--dry-run", action="store_true", help="show what would change, change nothing"
    )
    reclassify.set_defaults(func=cmd_reclassify)
    return parser


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    args = build_parser().parse_args(argv)
    # Any file SQLite creates here (a -wal or -shm while the API is stopped)
    # must be private, like the rest of the customer-data directory.
    previous_umask = os.umask(0o077)
    try:
        return args.func(args, out or sys.stdout)
    finally:
        os.umask(previous_umask)


if __name__ == "__main__":
    raise SystemExit(main())
