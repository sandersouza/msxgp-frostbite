"""Build the original-free plain32KiB renderer diagnostic with pinned sjasmplus."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from environment import ROOT,verified_tool
import render_model as model

VERSION='0.0.2-renderer'
OUT=ROOT/'outputs/render'
ROM=OUT/f'frostbite-{VERSION}.rom'


def validate_rom(data):
    errors=[]
    if len(data)!=32768:errors.append('plain32KiB ROM required')
    if data[:2]!=b'AB' or len(data)<20 or data[16:20]!=b'FBR8':errors.append('renderer cartridge header/signature required')
    if len(data)>=16 and (not 0x4010<=int.from_bytes(data[2:4],'little')<0xC000 or any(data[4:16])):
        errors.append('invalid cartridge vectors')
    return errors


def validate_identity(data,metadata):
    if (validate_rom(data) or metadata['version']!=VERSION or metadata['rom']['size']!=len(data)
            or metadata['rom']['sha256']!=hashlib.sha256(data).hexdigest()):
        raise ValueError('renderer ROM/build identity mismatch')


def symbols(path):
    result={}
    for line in path.read_text().splitlines():
        match=re.fullmatch(r'([^:]+): EQU 0x([0-9A-Fa-f]+)',line.strip())
        if match:result[match[1]]=int(match[2],16)
    return result


def write_tables():
    OUT.mkdir(parents=True,exist_ok=True)
    blobs={'phase':model.phase_tables(),'sprites':model.sprite_patterns(),
           'font_patterns':model.static_patterns()[0],'font_colors':model.static_patterns()[1],
           'names':model.static_names(model.scene(0)),'initial_scene':model.encode_scene(model.scene(64)),
           'x_columns':bytes(model.display_x(x)//8 for x in range(160)),
           'x_positions':bytes(model.display_x(x) for x in range(160)),
           'igloo':b''.join(model.static_names({**model.scene(0),'igloo':stage})[(3+y)*32+22:(3+y)*32+30]
                            for stage in range(4) for y in range(4))}
    lines=[]
    for name,data in blobs.items():
        path=OUT/(name+'.bin');path.write_bytes(data)
        if name=='phase':lines.append('ALIGN 256')
        lines.extend([name+'_data:',f'INCBIN "{path}"'])
    lines+=['band_y_data:','DB '+','.join(str(y) for row in model.BAND_Y for y in row),
            'color_pointers:','DW color_white,color_blue,color_a,color_b,color_c',
            'color_white: DS 64,$F0','color_blue: DS 64,$50','color_a: DS 64,$A0',
            'color_b: DS 64,$B0','color_c: DS 64,$C0','segment_lists:']
    lines+=['DW '+','.join(f'seg_{layout}_{page}_{band}' for layout in range(2) for page in range(2) for band in range(8))]
    for layout in range(2):
        for page in range(2):
            for band in range(8):
                lines.append(f'seg_{layout}_{page}_{band}:')
                for address,count,offset in model.cache_segments(layout,page,band):
                    lines.extend([f'DW ${address|0x4000:04X}',f'DB {count},{offset}'])
                lines+=['DW 0','DB 0,0']
    lines+=['fast_prepare_functions:','DW fast_all_0_0,fast_all_0_1,fast_all_1_0,fast_all_1_1']
    for layout in range(2):
        for page in range(2):
            lines.append(f'fast_all_{layout}_{page}:')
            lines.extend(f'CALL fast_band_{layout}_{page}_{band}' for band in range(8))
            lines.append('RET')
            for band in range(8):
                lines.append(f'fast_band_{layout}_{page}_{band}:')
                y=model.BAND_Y[layout][band];row=band//2;ice=band%2
                if y%8:
                    # One isolated crossing ice band: bulk both32-byte halves,
                    # including zero pattern padding. Avoid per-column parsing.
                    segments=model.cache_segments(layout,page,band)
                    top=segments[0][0]-y%8;bottom=segments[1][0]
                    lines += [f'LD A,(INPUT+{row})','LD (ROOTX),A','LD A,(INPUT+30)',
                        'RLCA','RLCA','RLCA','RLCA','LD H,A','LD A,(ROOTX)','AND 15','ADD A,H',
                        'ADD A,phase_data/256','LD H,A',f'LD L,{(y%8)//2*64}',
                        f'LD DE,${top|0x4000:04X}','LD B,32','CALL vdp_write',
                        f'LD DE,${bottom|0x4000:04X}','LD B,32','CALL vdp_write',
                        f'LD A,(INPUT+{8+row})','ADD A,A','LD E,A','LD D,0','LD HL,color_pointers',
                        'ADD HL,DE','LD E,(HL)','INC HL','LD D,(HL)','EX DE,HL',
                        f'LD DE,${top|0x6000:04X}','LD B,32','CALL vdp_write',
                        f'LD DE,${bottom|0x6000:04X}','LD B,32','CALL vdp_write',
                        f'LD A,{y}','LD (YPOS),A',f'LD A,{band}','LD (BAND),A',
                        'LD A,3','LD (COPIES),A','LD A,32','LD (GAP),A','JP stage_band_names']
                    continue
                addr=model.cache_segments(layout,page,band)[0][0]
                pos=row if ice else row+4
                lines.extend([f'LD A,(INPUT+{pos})','LD (ROOTX),A',
                    'LD A,(INPUT+30)' if ice else f'LD A,(INPUT+{12+row})'])
                if not ice:lines.append('ADD A,2')
                lines+=['RLCA','RLCA','RLCA','RLCA','LD H,A','LD A,(ROOTX)','AND 15','ADD A,H',
                    'ADD A,phase_data/256','LD H,A','LD L,0',f'LD DE,${addr|0x4000:04X}',
                    'LD B,32','CALL vdp_write',f'LD A,(INPUT+{8+row if ice else 12+row})',
                    'ADD A,A','LD E,A','LD D,0',f'LD HL,color_pointers+{0 if ice else 4}',
                    'ADD HL,DE','LD E,(HL)','INC HL','LD D,(HL)','EX DE,HL',
                    f'LD DE,${addr|0x6000:04X}','LD B,32','CALL vdp_write',
                    'LD A,(ROOTX)','LD E,A','LD D,0','LD HL,x_columns_data','ADD HL,DE','LD C,(HL)']
                if ice:lines+=['LD B,3','LD E,6']
                else:lines += [f'LD A,(INPUT+{16+row})','LD B,A',f'LD A,(INPUT+{20+row})',
                    'INC A','LD E,A','ADD A,A','ADD A,E','LD E,A']
                lines += [f'LD D,{model.cache_base(layout,page,band)}',f'LD HL,NAMES+{y//8*32}',
                    'LD A,L','OR C','LD L,A','JP stage_fixed_row']
    lines=[line if re.match(r'^[A-Za-z_]\w*:',line) else '    '+line for line in lines]
    (OUT/'render_tables.inc').write_text('\n'.join(lines)+'\n')
    return {name:hashlib.sha256(data).hexdigest() for name,data in blobs.items()}


def build():
    table_hashes=write_tables();assembler=verified_tool('sjasmplus')
    result=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={OUT}',
        f'--raw={ROM}',f'--lst={OUT/"render.lst"}',f'--sym={OUT/"render.sym"}',str(ROOT/'src/render_benchmark.asm')],cwd=ROOT,capture_output=True,text=True,timeout=60)
    (OUT/'assembler.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise ValueError('assembler failed: '+'\n'.join((result.stdout+result.stderr).splitlines()[-12:]))
    data=ROM.read_bytes();errors=validate_rom(data)
    if errors:raise ValueError('; '.join(errors))
    syms=symbols(OUT/'render.sym');used=syms['rom_end']-0x4000
    files=('src/render_benchmark.asm','src/render.asm','scripts/render_build.py','scripts/render_model.py',
           'references/renderer-contract.json','references/tools-lock.json')
    report={'version':VERSION,'diagnostic':True,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
        'rom':{'filename':ROM.name,'size':len(data),'used_bytes':used,'padding_bytes':len(data)-used,
               'sha256':hashlib.sha256(data).hexdigest(),'mapper':'Normal/plain32KiB'},
        'source_files':{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in files},
        'assembler_sha256':hashlib.sha256(assembler.read_bytes()).hexdigest(),'generated_tables':table_hashes,
        'acceptance':'Synthetic renderer diagnostic only; no native gameplay/original graphics/hardware acceptance.'}
    (OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Built {VERSION}: {len(data)} bytes, used{used}, SHA-256 {report["rom"]["sha256"]}')
    return report


def main():
    try:build();return 0
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        print(f'Render build failed: {error}',file=sys.stderr);return 1


if __name__=='__main__':sys.exit(main())
