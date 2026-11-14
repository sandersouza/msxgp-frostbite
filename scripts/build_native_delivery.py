"""Reproducibly build the shared flat game and all three genuine native formats.

Private, hash-qualified game/authority inputs are required. No emulator snapshot,
operating-system disk or BIOS is a product build input. Qualification is separate.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from build_native_flat_image import build as link, digest
from native_flat_catalog import catalog
from native_cold_image import build as cold
from build_native_plain32 import build as cartridge
from build_native_disk import build as disk
from native_p0_fast_probe import check as p0_check
from native_bear_grid_sparse_probe import check as bear_check
from native_grid_palette_fast_probe import check as grid_check


def sources():
    # Archive the complete maintained producer/checker tree. Original/generated
    # assets are private inputs, not source files to copy into this archive.
    names=set()
    for folder in ('scripts','src'):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and (p.suffix in ('.py','.asm','.inc','.tcl') or p.name=='LICENSE'):
                names.add(str(p.relative_to(ROOT)))
    names.discard('scripts/build_compact_grid_experiment.py') # unrelated preserved local experiment
    names.update(str(p.relative_to(ROOT)) for p in (ROOT/'references').glob('*.json'))
    return {n:digest((ROOT/n).read_bytes()) for n in sorted(names)}


def build(base,control,out,compressor):
    base,control,out=base.resolve(),control.resolve(),out.resolve()
    if out.exists():raise ValueError('fresh delivery output required')
    before=sources();out.mkdir(parents=True)
    p0_check(base,out/'proof-P0')
    bear_check(base,out/'proof-bear','sparse')
    grid_check(control,out/'proof-grid',True)
    catalog(base,out/'layout',native_lifetimes=True,fast_P0=True,fast_bands=True)
    link(base,out/'layout',out/'linked',out/'proof-P0/component-result.json',
         dict(bear=out/'proof-bear',grid=out/'proof-grid'),True)
    cold(base,out/'linked',out/'cold')
    cartridge(out/'cold',out/'cartridge',compressor)
    disk(out/'cartridge',out/'disk')
    if sources()!=before:raise ValueError('producer/checker source changed during native build')
    for name,sha in before.items():
        target=out/'source'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,target)
        if digest(target.read_bytes())!=sha:raise ValueError('source archive differs')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    files={str(p.relative_to(out)):dict(size=p.stat().st_size,sha256=digest(p.read_bytes()))
           for p in (out/'cartridge/FROSTBIT.ROM',*(out/'disk'/n for n in ('FROSTBIT.COM','FROSTBIT.BIN','FBGFX.BIN','FROSTBIT.BAS')))}
    result=dict(complete=False,native_formats_built=True,qualification_required=True,
                source_commit=commit,source_files=before,source_archive='source',files=files,
                build_input=str(base.relative_to(ROOT)),accepted_control=str(control.relative_to(ROOT)),
                no_mapper=True,RAM_KiB=64,VRAM_KiB=16,emulator_state_used_as_input=False,
                remaining=['fresh all-format qualification','accepted whole-frame cadence','independent review/release/integration'])
    (out/'native-delivery-build.json').write_text(json.dumps(result,indent=2)+'\n')
    print(dict(native_formats_built=True,source_commit=commit,files=files))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','control','out','compressor'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.base,a.control,a.out,a.compressor)
