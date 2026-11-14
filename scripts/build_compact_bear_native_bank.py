"""Relink both bear render bodies into the reclaimed native-bank table space."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def once(text,old,new):
    if text.count(old)!=1:raise ValueError('unique source transformation required: '+old[:70])
    return text.replace(old,new,1)


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_core_loop') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound reclaimed native bank required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    s=symbols(base/'presentation.sym');source=(base/'bh-body.asm').read_text();source_hash=digest(source.encode())
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    def defs(exclude):
        (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in s.items() if '.' not in n and n not in exclude and not n.startswith(('an_','ao_')) and n not in ('AN_RECORD','AN_TILE','AN_KEYS','AO_INFO','AO_PACKET','AN_HUD_CONT'))+f'\nAN_HUD_CONT EQU ${s["presentation_hud_prepare"]+3:04X}\n')
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1500:])
        return (out/(name+'.bin')).read_bytes(),symbols(out/(name+'.sym'))
    defs(set());old,q0=assemble('bn-baseline',source);slot=s['w_selected']-s['w_header']
    if old[slot:]!=parent[114*16384+0x3800:115*16384]:raise ValueError('complete current hybrid body must reproduce')
    # The registry is host verification input only, never read by game code.
    # Keep its independent source/ROM check in an explicitly non-runtime bank.
    registry=(out/'bear-registry.bin').read_bytes()
    if len(registry)!=240:raise ValueError('complete80-mask verification registry required')
    source=once(source,'an_registry:\n    INCBIN "bear-registry.bin"\n','an_registry EQU $A800\n')
    source=source.replace('    LD A,114\n','    LD A,2\n')
    source=once(source,'an_native:\n    LD A,102\n    CALL t_mapper\n    CALL ai_body\n    LD A,2\n    JP t_mapper\n',
        'an_native:\n    CALL ai_body\n    LD A,2\n    JP t_mapper\n    DS 5,$FF\n')
    source=once(source,'    ORG $B800\nan_body:','    ORG $9C10\nan_body:')
    source=once(source,'    ASSERT $ <= $C000\n    DS $C000-$,$FF\nan_body_padded_end:',
        '    ASSERT $ <= $A400\nan_body_padded_end:')
    hybrid,q=assemble('bn-hybrid',source);hybrid_size=q['an_body_end']-q['an_body'];bulk_origin=0x9C10+hybrid_size
    if hybrid_size!=1479 or any(q[n]!=s[n] for n in ('an_early','an_header','an_copy','an_upload','an_native','an_ram_end')):
        raise ValueError('exact compact body or public RAM helper ABI changed')
    full=(base/'bi-resident.asm').read_text();bulk=full[full.rindex('    ORG $B800\nai_bulk:'):]
    labels={line.split(':')[0] for line in bulk.splitlines() if line.startswith('ai_') and ':' in line}
    defs(labels)
    # Reproduce the current patched strip program from source before relinking.
    a=bulk.index('    LD A,D\n    DUP 3\n',bulk.index('.strip_index:'));b=bulk.index('    CALL ai_bulk_bg\n',a)
    replacement='    POP BC\n    CALL $5033\n'
    # The old product jumped across an in-place patch's FF padding. After
    # source relinking there is no dead padding or absolute old resume target.
    bulk=bulk[:a]+replacement+bulk[b:]
    bulk=once(bulk,'    ORG $B800\nai_bulk:',f'    ORG ${bulk_origin:04X}\nai_bulk:')
    bulk=once(bulk,'    ASSERT $ <= $C000\n    DS $C000-$,$FF\nai_bulk_padded_end:',
        '    ASSERT $ <= $A400\nai_bulk_padded_end:')
    native,qi=assemble('bn-bulk','    INCLUDE "symbols.inc"\n'+bulk)
    if hybrid_size+len(native)>2032:raise ValueError('both bear bodies exceed reclaimed native-bank arena')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    native_at=2*16384+0x1C10
    if parent[native_at:native_at+2032]!=bytes([255])*2032:raise ValueError('erased native-bank table arena required')
    patch(native_at,hybrid[slot:]+native,'both native render bodies share the core bank')
    ram_at=115*16384+0x3800+s['w_header']-0xE900
    patch(ram_at,hybrid[:slot],'same public helpers select core bank2 and relocated hybrid entry')
    # Every bulk helper keeps its original public RAM entry and register ABI.
    for start,end in ((s['ai_bulk_enter'],s['ai_bulk_back']),(s['ai_bulk_ids'],s['ai_bulk_upload']),(s['ai_bulk_upload'],s['ai_ram_end'])):
        at=115*16384+0x3800+start-0xE900;buf=bytearray(parent[at:at+end-start])
        if buf.count(bytes((0x3E,112)))!=1:raise ValueError('unique original bulk-bank selector required')
        pos=buf.index(bytes((0x3E,112)));buf[pos+1]=2
        if start==s['ai_bulk_enter']:
            expected=bytes((0xC3,0,0xB8))
            if bytes(buf[-3:])!=expected:raise ValueError('original bulk entry jump required')
            buf[-2:]=bulk_origin.to_bytes(2,'little')
        patch(at,buf,'bulk helper selects the core bank; native helper addresses unchanged')
    bridge_at=0x55FF-0x4000;bridge=bytearray(parent[bridge_at:bridge_at+15])
    if bridge[-5:]!=bytes((0x3E,114,0xC3,s['t_mapper']&255,s['t_mapper']>>8)):raise ValueError('exact hybrid stream bridge required')
    bridge[-4]=2;patch(bridge_at,bridge,'hybrid dictionary streamer returns to its relocated core-bank caller')
    reg_at=60*16384+0x2800
    if parent[reg_at:reg_at+240]!=bytes([255])*240:raise ValueError('empty verification registry arena required')
    patch(reg_at,registry,'host-only cropped-mask registry remains under a CPU read guard')
    for bank in (112,114):
        patch(bank*16384+0x3800,bytes([255])*2048,'retired foreign bear render body')
        m['compact_retired_graphics']['ranges'].append(dict(bank=bank,address=0xB800,size=2048,kind='retired foreign bear render body'))
    m['compact_retired_graphics']['retired_physical_bytes']+=4096
    row=next(r for r in m['compact_retired_graphics']['ranges'] if r['bank']==2 and r['address']==0x9C10 and r['size']==2032)
    row['address']+=hybrid_size+len(native);row['size']-=hybrid_size+len(native)
    m['compact_retired_graphics']['retired_physical_bytes']-=hybrid_size+len(native)
    m['bear_hybrid'].update(body_bank=2,registry_bank=60,registry_address=0xA800,extra_records_bank=2,extra_records_address=q['an_extra_records'])
    m['bear_three'].update(body_bank=2,body_bytes=hybrid_size)
    fixed=m['fixed_clock'];at=115*16384+0x3800;fixed['ram_code_sha256']=digest(target[at:at+fixed['ram_code_bytes']])
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    m['source_files']['scripts/build_compact_bear_native_bank.py']=digest(Path(__file__).read_bytes())
    m['compact_bear_native_bank']=dict(parent_rom_sha256=digest(parent),patches=patches,native_address=0x9C10,hybrid_bytes=hybrid_size,bulk_address=bulk_origin,bulk_bytes=len(native),
        remaining_native_gap=2032-hybrid_size-len(native),generated_hybrid_source_sha256=source_hash,host_registry_not_a_runtime_allocation=True,mapperless=False,human_test_candidate=False)
    s.update({n:v for n,v in q.items() if n.startswith(('an_','ao_'))});s.update({n:v for n,v in qi.items() if n.startswith('ai_bulk') and n in labels or n.startswith('ai_bulk.') or n.startswith('ai_bulk_name.') or n.startswith('ai_bulk_bg.')})
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    filename='frostbite-compact-bear-native-bank-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();m.update(source_commit=commit,source_dirty=True,version='compact-bear-native-bank-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Both native bear render bodies share core bank2; independent whole-game qualification required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),hybrid_bytes=hybrid_size,bulk_bytes=len(native),remaining_native_gap=2032-hybrid_size-len(native)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
