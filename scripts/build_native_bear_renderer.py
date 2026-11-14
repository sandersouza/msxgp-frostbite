"""Replace expanded native bear tiles with the source-picture mask grammar."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from environment import ROOT, verified_tool
from reference_traces import private_output
from render_build import symbols


def remove_interval(rows, bank, first, end):
    result=[]
    for row in rows:
        if bank is not None and row.get('bank')!=bank:
            result.append(row);continue
        a,b=row['address'],row['address']+row['size']
        if b<=first or a>=end:
            result.append(row);continue
        if a<first:result.append({**row,'size':first-a})
        if b>end:result.append({**row,'address':end,'size':b-end})
    return result


def build(base, grid, painter, out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes())
    parent=(base/m['rom']['filename']).read_bytes()
    if digest(parent)!='5ffac6a983c6bb770bf540db33a7fb506f2120fb5c3e7d9c7d47af2e64ea9717':
        raise ValueError('exact selected resident-enemy parent required')
    for directory,cases in ((grid,512),(painter,38400)):
        proof=json.loads((directory/'component-result.json').read_bytes())
        if not proof['complete'] or proof['cases']!=cases or proof['input_rom_sha256']!=m['rom']['sha256']:
            raise ValueError('complete exact native component proof required')
    s=symbols(base/'presentation.sym')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in s.items() if '.' not in n)+'\n')
    data=b''.join((grid/n).read_bytes() for n in ('info.bin','rows.bin','shifted.bin'))
    if len(data)!=856:raise ValueError('32alias+120selectors+704shifted rows required')
    (out/'nb-rows.bin').write_bytes(data)
    source=''' INCLUDE "symbols.inc"
ng_info EQU $9FF2
ng_rows EQU ng_info+32
ng_shifted EQU ng_rows+120
 ORG $538A
 INCLUDE "native_bear_renderer.asm"
nb_body_end:
 ASSERT $ <= $55FF
 ORG $6A50
 INCLUDE "native_bear_grid_rows.asm"
 INCLUDE "native_bear_painter.asm"
nb_helpers_end:
 ASSERT $ <= $6B4E
'''
    (out/'nb-renderer.asm').write_text(source)
    r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--inc={ROOT/"src"}',
                      f'--raw={out/"nb-renderer.bin"}',f'--sym={out/"nb-renderer.sym"}',str(out/'nb-renderer.asm')],capture_output=True,text=True)
    (out/'nb-renderer.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError('native bear assembly failed: '+(r.stdout+r.stderr)[-1800:])
    q=symbols(out/'nb-renderer.sym');code=(out/'nb-renderer.bin').read_bytes()
    body=code[:q['nb_body_end']-0x538A]
    helpers=code[len(body):]
    if len(helpers)!=q['nb_helpers_end']-0x6A50:raise ValueError('explicit body/helper object extents required')
    target=bytearray(parent)
    target[0x138A:0x15FF]=body+bytes([255])*(0x55FF-q['nb_body_end'])
    target[0x2A50:0x2B4E]=helpers+bytes([255])*(0x6B4E-q['nb_helpers_end'])
    at=2*16384+0x1FF2
    target[at:at+0x40E]=data+bytes([255])*(0x40E-len(data))
    # Public early and late entries retain their addresses. Only the early
    # native fallback needs to select the atlas's already resident core bank.
    entry=s['ai_entry'];at=115*16384+0x3800+entry-0xE900
    gate=bytes((0xCD,s['p_fast_primitive_dirty']&255,s['p_fast_primitive_dirty']>>8,0xC8,
                0x3E,2,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xC3,0x8A,0x53))
    if len(gate)!=s['ai_call']-entry:raise ValueError('exact public native entry extent required')
    target[at:at+len(gate)]=gate
    graph=m['compact_retired_graphics']
    graph['ranges']=remove_interval(graph['ranges'],2,0x9FF2,0xA34A)
    graph['retired_physical_bytes']=sum(r['size'] for r in graph['ranges'])
    resident=m['compact_retired_resident']
    for first,end in ((0x538A,q['nb_body_end']),(0x6A50,q['nb_helpers_end'])):
        resident['ranges']=remove_interval(resident['ranges'],None,first,end)
    for first,end in ((q['nb_body_end'],0x55FF),(q['nb_helpers_end'],0x6B4E)):
        if first<end:resident['ranges'].append(dict(address=first,size=end-first,kind='unused native bear module suffix'))
    for n,v in q.items():
        if n.startswith(('nb_','ng_','np_')):s[n]=v
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    fixed=m['fixed_clock'];at=115*16384+0x3800
    fixed['ram_code_sha256']=digest(target[at:at+fixed['ram_code_bytes']])
    files=('scripts/build_native_bear_renderer.py','scripts/native_bear_keys.py','scripts/presentation_fixed_ownership.py',
           'src/native_bear_renderer.asm','src/native_bear_grid_rows.asm','src/native_bear_painter.asm')
    for n in files:m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['native_bear_renderer']=dict(parent_rom_sha256=digest(parent),kind=10,body_bytes=len(body),helper_bytes=len(helpers),
          atlas_bytes=len(data),atlas_address=0x9FF2,source_grid_cases=512,palette_native_cases=38400,
          sprite_admission_unchanged=True,expanded_assets_retired=False,mapperless=False,human_test_candidate=False)
    filename='frostbite-native-bear-renderer-internal.rom'
    (out/filename).write_bytes(target);m['rom'].update(filename=filename,sha256=digest(target))
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),body_bytes=len(body),helper_bytes=len(helpers),atlas_bytes=len(data)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','grid','painter','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.base,a.grid,a.painter,a.out)
