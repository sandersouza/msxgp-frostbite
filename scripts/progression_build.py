"""Versioned all-mode progression diagnostic using the unchanged native core."""
import argparse
import json
from pathlib import Path

from environment import ROOT
import hazard_build

VERSION = '0.0.6-progression'
BANNER = ('FROSTBITE PROGRESSION DIAG', 'ALL GAME MODES NO AUDIO')
OUT = ROOT / 'outputs/progression/build'
ROM = OUT / f'frostbite-{VERSION}.rom'
FILES = (*hazard_build.FILES, 'scripts/progression_build.py')
presentation = hazard_build.presentation


def diagnostic_names(scene): return hazard_build.diagnostic_names(scene, BANNER)


def expected_pixels(scene): return hazard_build.expected_pixels(scene, BANNER)


def build(floes, edge, ordinary, shore, aliases, out=OUT):
    return hazard_build.build(floes, edge, ordinary, shore, aliases, out,
        version=VERSION, banner=BANNER, additional_files=('scripts/progression_build.py',))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('floes', 'edge', 'ordinary', 'shore', 'aliases'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--out', type=Path, default=OUT)
    print(json.dumps(build(**vars(p.parse_args())), indent=2))
