#!/usr/bin/env python3
"""Prepare only the pinned native-build assembler; no host-package installation."""
import json
import sys
from environment import ROOT, prepare_tool


if __name__ == '__main__':
    try:
        spec = json.loads((ROOT / 'references/tools-lock.json').read_text())['tools']['sjasmplus']
        print(prepare_tool(ROOT, 'sjasmplus', spec))
    except Exception as error:
        print(f'CI source-tool preparation failed: {error}', file=sys.stderr)
        sys.exit(1)
