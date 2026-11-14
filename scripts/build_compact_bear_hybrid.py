"""Share exact hybrid bear planes and retain original physical key publication."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_bear_hybrid_probe import assets
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_header_ram') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound RAM header stage required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-hybrid-native-01';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=352 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('complete hybrid component proof required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('component source changed')
    data,expected=assets(ROOT/'outputs/presentation/credit-reference-at/build-final')
    for i in range(352):
        at=(134+i//46)*16384+0x3800+(i%46)*44
        if parent[at:at+44]!=expected[i*44:i*44+44]:raise ValueError('accepted hybrid row changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    s=symbols(base/'presentation.sym');origin=0x55FF;arena_end=0x5790
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in s.items() if '.' not in n and not n.startswith(('an_','ao_')) and n not in ('AN_RECORD','AN_TILE','AN_KEYS','AO_INFO','AO_PACKET','AN_HUD_CONT'))+f'\nAN_HUD_CONT EQU ${s["presentation_hud_prepare"]+3:04X}\n')
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1600:])
        return (out/(name+'.bin')).read_bytes(),symbols(out/(name+'.sym'))
    # The accepted open-view stage changed five background bytes in the ROM,
    # while its historical generated include was not refreshed. Preserve the
    # complete current36-byte literal table, then reproduce all bank114 bytes.
    bg=out/'bear-background-rows.bin'
    if len(bg.read_bytes())!=36:raise ValueError('four exact three-row backgrounds required')
    bg_at=114*16384+s['an_background_rows']-0x8000
    bg.write_bytes(parent[bg_at:bg_at+36])
    source=(ROOT/'src/presentation_bear_three.asm').read_text();old,q0=assemble('bh-original',source)
    slot=s['w_selected']-s['w_header']
    if parent[114*16384+0x3800:115*16384]!=old[slot:]:raise ValueError('complete original bank114 body must reproduce before relinking')
    def pointers(blob):
        b=bytearray(blob)
        if len(b)%22:raise ValueError('whole22-byte records required')
        for at in range(0,len(b),22):
            for field in range(6):
                p=at+field*3;a=int.from_bytes(b[p:p+2],'little');bank=b[p+2]
                if not 134<=bank<=141 or (a-0xB800)%44:raise ValueError('whole original row pointer required')
                n=(bank-134)*46+(a-0xB800)//44
                if not 0<=n<352:raise ValueError('bounded program ID required')
                b[p:p+3]=(0xA100+n*10).to_bytes(2,'little')+bytes((59,))
        return bytes(b)
    records=pointers(parent[133*16384+0x3800:133*16384+0x3800+2046]);extra=pointers((out/'bear-extra-records.bin').read_bytes())
    (out/'bear-extra-records.bin').write_bytes(extra)
    start=source.index('    PUSH DE\n    LD A,(p_tf_column)\n    LD B,16\n',source.index('an_draw:'))
    end=source.index('    LD IX,(p_fx_meta)\n',start)
    source=source[:start]+f'    CALL ${origin:04X}\n    LD HL,$C520\n    LD DE,(p_fx_meta)\n    LD BC,12\n    LDIR\n'+source[end:]
    body,q=assemble('bh-body',source)
    if q['an_early']!=s['an_early'] or q['an_ram_end']!=q0['an_ram_end']:raise ValueError('public native RAM ABI changed')
    for n,b in data.items():(out/('bh-'+n+'.bin')).write_bytes(b)
    code,_=assemble('bh-row','\n'.join([' ORG $A000','BH_COLOR_OFFSET EQU $2000',f'vdp_write EQU ${s["vdp_write"]:04X}',f'vdp_stream EQU ${s["vdp_stream"]:04X}',
        ' INCLUDE "compact_bear_hybrid_row.asm"',' ASSERT $ <= $A100',' DS $A100-$,$FF','bh_recipes:',f' INCBIN "{out/"bh-recipes.bin"}"','bh_patterns:',f' INCBIN "{out/"bh-patterns.bin"}"','bh_colors:',f' INCBIN "{out/"bh-colors.bin"}"',' ASSERT $ <= $B800'])+'\n')
    bridge,_=assemble('bh-bridge',f' ORG ${origin:04X}\n PUSH DE\n LD A,59\n CALL ${s["t_mapper"]:04X}\n POP DE\n CALL $A000\n LD A,114\n JP ${s["t_mapper"]:04X}\n ASSERT $ <= ${arena_end:04X}\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    at=59*16384+0x2000
    if parent[at:at+len(code)]!=bytes([255])*len(code):raise ValueError('erased compact arena required')
    patch(at,code,'shared plane dictionary and exact hybrid row streamer')
    patch(origin-0x4000,bridge,'mapped hybrid row bridge in reclaimed NAME decoder')
    patch(114*16384+0x3800,body[slot:],'same hybrid admission/source logic with dictionary stream and unchanged physical keys')
    patch(133*16384+0x3800,records,'compact hybrid row far pointers')
    remaining=352
    for bank in range(134,142):
        size=min(remaining,46)*44;remaining-=size//44
        patch(bank*16384+0x3800,bytes([255])*size,'retired prepared hybrid row programs')
        m['compact_retired_graphics']['ranges'].append(dict(bank=bank,address=0xB800,size=size,kind='retired prepared hybrid bear programs'))
    m['compact_retired_graphics']['retired_physical_bytes']+=15488
    pool=next(r for r in m['compact_retired_pools']['ranges'] if r['bank']==59)
    if pool['size']!=0x3800:raise ValueError('exact retired59 prefix required')
    pool['size']=0x2000;m['compact_retired_pools']['retired_physical_bytes']-=0x1800
    rows=m['compact_retired_resident']['ranges'];row=next(r for r in rows if r['address']==origin and r['size']==arena_end-origin)
    row['address']+=len(bridge);row['size']-=len(bridge);m['compact_retired_resident']['reused_for_resident_code_bytes']+=len(bridge)
    m['bear_hybrid'].update(registry_address=q['an_registry'],extra_records_address=q['an_extra_records'],program_banks=[59,59],program_bytes=10,programs_per_bank=352,program_address=0xA100)
    m['bear_three']['body_bytes']=q['an_body_end']-q['an_body']
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    names=('scripts/build_compact_bear_hybrid.py','scripts/compact_bear_hybrid.py','scripts/compact_bear_hybrid_probe.py','src/compact_bear_hybrid_row.asm','tests/test_compact_bear_hybrid.py')
    for n in names:m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_bear_hybrid']=dict(parent_rom_sha256=digest(parent),patches=patches,prepared_program_bytes=15488,dictionary_bytes=5712,stream_code_bytes=proof['code_bytes']-6,
        component_cases=352,existing_C520_keys_only=True,original_admission_and_keys_retained=True,mapperless=False,human_test_candidate=False)
    s.update({n:v for n,v in q.items() if n.startswith(('an_','ao_'))});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    filename='frostbite-compact-bear-hybrid-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();m.update(source_commit=commit,source_dirty=True,version='compact-bear-hybrid-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Exact hybrid plane dictionary; whole-frame qualification required, native formats unfinished.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),dictionary_bytes=5712,prepared_bytes=15488,stream_bytes=len(code),bridge_bytes=len(bridge)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
