"""Build the native movement diagnostic, with explicit scripted contacts."""
import hashlib
import json
import subprocess

from environment import ROOT,verified_tool
from reference_inventory import verified_input
from native_fast import generate_fast
from render_build import symbols
import render_model as model
from movement_atlas import compile_atlas

VERSION='0.0.3-movement'
OUT=ROOT/'outputs/movement'
ROM=OUT/f'frostbite-{VERSION}.rom'
FILES=('scripts/movement_build.py','scripts/movement_atlas.py','scripts/render_build.py','scripts/render_model.py','scripts/native_codegen.py','scripts/native_fast.py','scripts/native_analysis.py',
       'src/movement_rows.asm','src/movement_cache.asm','src/movement.asm','src/native_input.asm','src/native_cpu.asm','src/render.asm','references/mechanics-cases.json',
       'scripts/environment.py','scripts/reference_inventory.py','references/manifest.json','references/tools-lock.json')


def presentation(ram,layout=0,width=0):
    if len(ram)!=128:raise ValueError('full canonical RAM required')
    get=lambda a:ram[a-128]
    rows=(3,2,1,0)
    result={'floes':[get(0x9F+r)%160 for r in rows],'threats':[get(0xD4+r)%160 for r in rows],
        'colors':[int(get(0xAB+r)!=12) for r in rows],'kinds':[min(2,get(0x91+r)&3) for r in rows],
        'counts':[min(3,get(0xD8+r)) for r in rows],'spacing':[int(bool(get(0x91+r)&64)) for r in rows],
        'player_x':get(0xE6)%160,'player_y':min(191,get(0xE4)+21),'bear_x':min(151,get(0xE8)),
        'bear_y':51,'palette':int(bool(get(0xCB)&4)),'igloo':min(3,get(0xCD)//4),'layout':layout,'width':width}
    model.encode_scene(result);return result


def validate_rom(data):
    errors=[]
    if len(data)!=262144:errors.append('256KiB ASCII16 required')
    if data[:2]!=b'AB' or data[16:20]!=b'FBM0':errors.append('movement diagnostic signature required')
    if len(data)<20 or not 0x4014<=int.from_bytes(data[2:4],'little')<0x8000 or any(data[4:16]):errors.append('resident cartridge entry/vectors required')
    return errors


def diagnostic_names(scene):
    names=bytearray(model.static_names(scene));names[:96]=bytes(96)
    model.text(names,0,1,'FROSTBITE MOVEMENT DIAG');model.text(names,1,1,'SCRIPTED CONTACTS NO AUDIO')
    model.text(names,2,1,'F1 RESET F2 SELECT F3 F4 VIEW')
    model.text(names,1,27,f'{scene["player_x"]:02X}');model.text(names,1,30,str(scene['palette']))
    return bytes(names)


def expected_pixels(scene):
    pixels=model.expected_pixels(scene);names=diagnostic_names(scene);patterns,colors=model.static_patterns()
    water=1 if scene['palette'] else 4
    for y in range(24):
        for x in range(256):
            tile=names[(y//8)*32+x//8];offset=tile*8+y%8
            color=(colors[offset]>>(4 if patterns[offset]&(128>>(x%8)) else 0))&15
            pixels[y*256+x]=color or water
    return pixels


def write_assets():
    atlas=compile_atlas();blobs={'font_patterns':model.static_patterns()[0],'font_colors':model.static_patterns()[1],
        'sprites':model.sprite_patterns(),'initial_scene':model.encode_scene(model.scene(64)),
        'atlas1_patterns':atlas['patterns'][0],'atlas1_colors':atlas['colors'][0],
        'atlas2_patterns':atlas['patterns'][1],'atlas2_colors':atlas['colors'][1],'patch_patterns':atlas['patches']}
    blobs['names']=diagnostic_names(model.scene(0))
    resident={'x_positions':bytes(model.display_x(x) for x in range(160)),'patch_flags':atlas['patch_flags'],
        'igloo':b''.join(model.static_names({**model.scene(0),'igloo':stage})[(3+y)*32+22:(3+y)*32+30] for stage in range(4) for y in range(4)),
        'object_variants':bytes(255 if count==0 else 4+kind*6+spacing*3+count-1 for kind in range(3) for spacing in range(2) for count in range(4))}
    def emit(filename,assets):
        lines=[]
        for name,data in assets.items():
            path=OUT/(name+'.bin');path.write_bytes(data);lines.extend((name+'_data:',f'    INCBIN "{path}"'))
        (OUT/filename).write_text('\n'.join(lines)+'\n')
    emit('boot_tables.inc',blobs);emit('resident_tables.inc',resident)
    rows=atlas['rows'];padded=rows+bytes([255])*(11*16384-len(rows));lines=[]
    for bank in range(11):
        path=OUT/f'rows-{bank}.bin';path.write_bytes(padded[bank*16384:(bank+1)*16384]);lines+=['    ORG $8000',f'    INCBIN "{path}"']
    (OUT/'row_banks.inc').write_text('\n'.join(lines)+'\n')
    source=(ROOT/'src/render.asm').read_text()
    renderer=source[:source.index('prepare:\n')]+source[source.index('digit_tile:\n'):source.index('prepare_band:\n')]+source[source.index('stage_sprites:\n'):]
    (OUT/'movement_render.inc').write_text(renderer)
    return {'tiles':atlas['colored_tiles'],'ordinary_tiles':atlas['ordinary_tiles'],'rows_bytes':len(rows),
        'variants':len(atlas['variants']),'generated':{n:hashlib.sha256(d).hexdigest() for n,d in {**blobs,**resident,'rows':rows}.items()}}


def build():
    source=verified_input(ROOT/'references/roms/frostbite.bin');original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'core.inc').write_text(generate_fast(original));(OUT/'data.bin').write_bytes(original[0xC00:])
    atlas=write_assets();assembler=verified_tool('sjasmplus')
    result=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={OUT}',f'--raw={ROM}',
        f'--sym={OUT/"movement.sym"}',f'--lst={OUT/"movement.lst"}',str(ROOT/'src/movement.asm')],cwd=ROOT,capture_output=True,text=True,timeout=60)
    (OUT/'assembler.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise ValueError('movement assembler failed: '+'\n'.join((result.stdout+result.stderr).splitlines()[-18:]))
    artifact=ROM.read_bytes();errors=validate_rom(artifact)
    if errors:raise ValueError('; '.join(errors))
    syms=symbols(OUT/'movement.sym')
    metadata={'version':VERSION,'diagnostic':True,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'original':source,
        'rom':{'filename':ROM.name,'size':len(artifact),'sha256':hashlib.sha256(artifact).hexdigest(),'mapper':'ASCII16'},
        'banks':{'resident_used':syms['resident_end']-0x4000,'assets_used':syms['assets_end']-0x8000,'native_used':syms['native_end']-0x8000,'row_banks':11},
        'source_files':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},'atlas':atlas,
        'assembler_sha256':hashlib.sha256(assembler.read_bytes()).hexdigest(),
        'limitations':'Synthetic presentation; scripted contact inputs; no natural collision, original graphics, audio or whole-game acceptance'}
    (OUT/'build.json').write_text(json.dumps(metadata,indent=2)+'\n');return metadata


if __name__=='__main__':print(json.dumps(build(),indent=2))
