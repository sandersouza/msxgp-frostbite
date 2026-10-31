#!/usr/bin/env python3
"""Repeat the synthetic build and preserve the published version's byte identity."""
import hashlib
import json
import sys
from rom import ROOT, ROM, VERSION, build


def check_artifact(data, version, baseline):
    if version != baseline['version']:
        raise ValueError('new diagnostic version requires an explicitly reviewed baseline/release')
    if len(data) != baseline['rom']['size'] or hashlib.sha256(data).hexdigest() != baseline['rom']['sha256']:
        raise ValueError('changed ROM bytes under declared version; create a new version/release')


if __name__ == '__main__':
    try:
        build()
        first = ROM.read_bytes()
        build()
        if ROM.read_bytes() != first:
            raise ValueError('repeated diagnostic builds differ')
        check_artifact(first, VERSION, json.loads((ROOT / 'references/diagnostic-baseline.json').read_text()))
        print('Repeated synthetic build matches the declared diagnostic baseline; no release published.')
    except Exception as error:
        print(f'CI verification failed: {error}', file=sys.stderr)
        sys.exit(1)
