#!/bin/sh
set -eu

# Customer source, generated reports, SQLite state, and temporary renderer files
# must never inherit a world-readable host/container umask.
umask 077

exec "$@"
