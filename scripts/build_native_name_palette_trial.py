"""Rebase the independently proved compact NAME palette onto the native parent."""
import argparse
import json
from pathlib import Path
from build_compact_grid_palette import build as palette_build
from build_compact_packet_experiment import digest
from environment import ROOT
from render_build import symbols


def build(base,out):
    palette_build(base,out)
    m=json.loads((out/'build.json').read_bytes());s=symbols(out/'presentation.sym')
    old=out/m['rom']['filename'];target=bytearray(old.read_bytes())
    # This bootstrap was installed as a verified fixed patch, not an exported
    # assembly symbol; bind its complete existing instruction sequence.
    at=0x7C51-0x4000
    before=bytes((0x3E,63,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xCD,0,0xBF))
    if target[at:at+len(before)]!=before:raise ValueError('exact selected NAME preload entry required')
    target[at+1]=45
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=digest(target[bank*16384:(bank+1)*16384])
    m['source_files']['scripts/build_native_name_palette_trial.py']=digest(Path(__file__).read_bytes())
    m['native_name_palette_trial']=dict(preload_bank=45,previous_preload_bank=63,additional_lower_RAM_bytes_reclaimed=3474,
                                      mapperless=False,human_test_candidate=False)
    filename='frostbite-native-name-palette-trial-internal.rom'
    (out/filename).write_bytes(target);m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),additional_lower_RAM_bytes_reclaimed=3474))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base.resolve(),a.out.resolve())
