"""Reuse the independent6502/Z80 CPU-RAM matrix for packed effect rows."""
import argparse
import json
from pathlib import Path

import compact_core_loop
from environment import ROOT
import native_write_loop_check as oracle
from native_shift_check import HELPERS as BASE_HELPERS


def check(out):
    oracle.emit_summary=compact_core_loop.emit_summary
    oracle.emit_tables=compact_core_loop.emit_tables
    oracle.HELPERS=tuple(dict.fromkeys((*oracle.HELPERS,'scripts/compact_core_loop.py','scripts/compact_core_loop_probe.py')))
    result=oracle.check(out,explore=True)
    print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.out)
