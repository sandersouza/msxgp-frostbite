#!/bin/bash
# Native macOS Bash; does not install/replace the user's Python interpreter.
set -eu
if ! command -v python3 >/dev/null || ! python3 -c 'import sys; sys.exit(sys.version_info < (3,11))'; then
    echo 'Python >=3.11 is required. Install Homebrew Python, then rerun bash scripts/setup.sh.' >&2
    exit 1
fi
script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
exec python3 -B "$script_dir/environment.py" "$@"
