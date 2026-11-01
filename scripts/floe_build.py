"""Build the native build-loop diagnostic from a verified complete floe catalog."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from environment import ROOT,verified_tool
from floe_tables import compile_catalog
import movement_build
from native_fast import generate_fast
from reference_inventory import verified_input
from reference_traces import private_output
from render_build import symbols
import render_model as model

VERSION='0.0.4-buildloop'
OUT=ROOT/'outputs/floes/build'
ROM=OUT/f'frostbite-{VERSION}.rom'
FILES=(*movement_build.FILES,'src/floe_visible.asm','scripts/floe_tables.py','scripts/floe_build.py')


def presentation(ram,layout=0,width=0):
    scene=movement_build.presentation(ram,layout,width);progress=ram[0x4D]
    scene['igloo']=0 if progress==255 else 3 if progress==15 else 1 if progress<8 else 2
    return scene


def diagnostic_names(scene):
    names=bytearray(model.static_names(scene));names[:96]=bytes(96)
    model.text(names,0,1,'FROSTBITE BUILD LOOP DIAG');model.text(names,1,1,'REAL FLOES NO AUDIO')
    model.text(names,2,1,'F1 RESET F2 SELECT F3 F4 VIEW')
    model.text(names,1,27,f'{scene["player_x"]:02X}');model.text(names,1,30,str(scene['palette']))
    return bytes(names)


def expected_pixels(scene):
    pixels=model.background_pixels(scene);names=diagnostic_names(scene);patterns,colors=model.static_patterns()
    water=1 if scene['palette'] else 4
    for y in range(24):
        for x in range(256):
            offset=names[(y//8)*32+x//8]*8+y%8
            color=(colors[offset]>>(4 if patterns[offset]&(128>>(x%8)) else 0))&15
            pixels[y*256+x]=color or water
    return model.paint_sprites(pixels,scene)


def capacity(banks):
    if type(banks) is not int or not 1<=banks<=256:raise ValueError('ASCII16 supports at most256 eight-bit16KiB bank selections')
    return 1<<(banks-1).bit_length()


def build(catalog,out=OUT):
    out=private_output(out);rom=out/f'frostbite-{VERSION}.rom'
    source=verified_input(ROOT/'references/roms/frostbite.bin');original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    out.mkdir(parents=True,exist_ok=True)
    table_out=out/'tables'
    if table_out.exists():raise ValueError('existing table build must remain immutable; select a fresh build directory')
    tables=compile_catalog(catalog,table_out)
    (out/'core.inc').write_text(generate_fast(original,carry_fusion=True));(out/'data.bin').write_bytes(original[0xC00:])
    previous=movement_build.OUT;previous_names=movement_build.diagnostic_names
    try:
        movement_build.OUT=out;movement_build.diagnostic_names=diagnostic_names;atlas=movement_build.write_assets()
    finally:movement_build.OUT=previous;movement_build.diagnostic_names=previous_names
    total=14+tables['banks'];cartridge_banks=capacity(total)
    (out/'cartridge_padding.inc').write_text(''.join('    ORG $8000\n    DS $4000,$FF\n' for _ in range(cartridge_banks-total)))
    (out/'entry.asm').write_text('    DEFINE WITH_FLOES\n    INCLUDE "movement.asm"\n')
    assembler=verified_tool('sjasmplus')
    result=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={out}',f'--inc={table_out}',
        f'--raw={rom}',f'--sym={out/"floes.sym"}',f'--lst={out/"floes.lst"}',str(out/'entry.asm')],
        cwd=ROOT,capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise ValueError('floe assembler failed: '+'\n'.join((result.stdout+result.stderr).splitlines()[-18:]))
    artifact=rom.read_bytes()
    if len(artifact)!=cartridge_banks*16384 or artifact[:2]!=b'AB' or artifact[16:20]!=b'FBF0':raise ValueError('floe cartridge header/capacity mismatch')
    syms=symbols(out/'floes.sym')
    metadata={'version':VERSION,'diagnostic':True,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'original':source,
        'rom':{'filename':rom.name,'size':len(artifact),'sha256':hashlib.sha256(artifact).hexdigest(),'mapper':'ASCII16'},
        'banks':{'resident_used':syms['resident_end']-0x4000,'assets_used':syms['assets_end']-0x8000,
                 'native_used':syms['native_end']-0x8000,'row_banks':11,'contact_banks':tables['banks'],'cartridge_banks':cartridge_banks},
        'source_files':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES},'atlas':atlas,'tables':tables,
        'assembler_sha256':hashlib.sha256(assembler.read_bytes()).hexdigest(),
        'limitations':'Native source mechanics and real floe acquisition; synthetic presentation/no audio. Full hazard/shore acquisition and whole-game/hardware acceptance remain pending.'}
    (out/'build.json').write_text(json.dumps(metadata,indent=2)+'\n');return metadata


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=OUT);args=parser.parse_args();print(json.dumps(build(args.catalog,args.out),indent=2))
