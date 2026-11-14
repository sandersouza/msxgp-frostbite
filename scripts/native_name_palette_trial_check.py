"""Use the exact palette allocation audit with every native-bear source oracle."""
import argparse
from pathlib import Path
import compact_grid_window_check
import compact_grid_palette_check
import native_bear_renderer_check


def check(build,out,mode):
    old=compact_grid_window_check.check
    compact_grid_window_check.check=compact_grid_palette_check.check
    try:native_bear_renderer_check.check(build,out,mode)
    finally:compact_grid_window_check.check=old


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
