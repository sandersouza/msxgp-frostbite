"""Measure existing native P0 generation instead of standing-shore recipes."""
import argparse
import json
from pathlib import Path
import shutil
from build_compact_packet_experiment import digest
from reference_traces import private_output
from render_build import symbols
from environment import ROOT


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('native_bear_retirement') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('qualified native-bear parent required')
    for mode in ('ntsc','pal','bear-ntsc','bear-pal','matrix'):
        p=json.loads((base.parent/mode/'native-bear-renderer-check.json').read_bytes())
        if not p['complete'] or p['rom_sha256']!=m['rom']['sha256']:raise ValueError('all five parent checks required')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    s=symbols(base/'presentation.sym');target=bytearray(parent)
    at=2*16384+s['ak_try']-0x8000
    if parent[at:at+3]!=bytes((0x3A,0x6B,0xF0)):raise ValueError('original standing-shore recipe entry required')
    target[at:at+3]=bytes((0xC3,s['ak_fallback']&255,s['ak_fallback']>>8))
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=digest(target[bank*16384:(bank+1)*16384])
    m['source_files']['scripts/build_native_p0_shore_trial.py']=digest(Path(__file__).read_bytes())
    m['native_p0_shore_trial']=dict(parent_rom_sha256=digest(parent),optional_prepared_recipe_bypassed=True,
          original_native_fallback_unchanged=True,assets_not_retired=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-native-p0-shore-trial-internal.rom'
    (out/filename).write_bytes(target);m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),changed_code_bytes=3))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
