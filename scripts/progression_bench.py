"""Existing full-density actual-native stress using the progression ROM profile."""
import argparse
import json
from pathlib import Path

from hazard_bench import capture
from hazard_query import RawContacts
import progression_build


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-dir', type=Path, default=progression_build.OUT)
    for name in ('floes', 'edge', 'ordinary', 'shore'): p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--family', choices=('ntsc', 'pal'), default='ntsc')
    p.add_argument('--layout', type=int, choices=(0, 1), default=0); p.add_argument('--width', type=int, choices=(0, 1), default=0)
    p.add_argument('--transitions', action='store_true'); p.add_argument('--explore', action='store_true')
    p.add_argument('--mixed', action='store_true'); p.add_argument('--catalog', choices=('dense', 'counts'), default='dense')
    p.add_argument('--inject', choices=('none', 'state', 'pixel', 'spacing', 'guard', 'sprite', 'contact', 'cache'), default='none')
    args = vars(p.parse_args()); reader = RawContacts(*(args.pop(n) for n in ('floes', 'edge', 'ordinary', 'shore')))
    result = capture(reader=reader, builder=progression_build, additional_helpers=('scripts/progression_bench.py',), **args)
    print(json.dumps({k: result[k] for k in ('directory', 'source_steps', 'max_busy_cycles', 'frame_budget')}))
