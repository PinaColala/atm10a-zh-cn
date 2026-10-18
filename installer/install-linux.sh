#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'Python 3.8+ is required. Install your distribution python3 package first.' >&2
    exit 1
fi
exec python3 "$SCRIPT_DIR/install.py" "$@"
