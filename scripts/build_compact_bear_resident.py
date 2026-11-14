"""Relink the native bear body and sparse context selector into resident RAM."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('unique native source transformation required: '+old[:60])
    return text.replace(old,new,1)


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_retired_names') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound retired NAME decoder required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-bear-context-native-02';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=1024 or not proof['branch_selector'] or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('complete context-selector proof required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('context source changed')
    source=(base/'br-compact.asm').read_text();source_input_sha=digest(source.encode());s=symbols(base/'presentation.sym')
    origin,end=0x538A,0x5790
    if parent[origin-0x4000:end-0x4000]!=bytes([255])*(end-origin):raise ValueError('empty reclaimed decoder required')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in s.items() if '.' not in n and not n.startswith(('ai_','cx_')))+'\n')
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',
            f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes(),symbols(out/(name+'.sym'))
    original,q0=assemble('bi-baseline',source);ram=q0['ai_ram_end']-q0['ai_entry'];ram_at=115*16384+0x3800+q0['ai_entry']-0xE900
    if parent[ram_at:ram_at+ram]!=original[:ram] or parent[102*16384+0x3800:103*16384]!=original[ram:ram+2048]:
        raise ValueError('generated compact native module does not reproduce parent RAM/body')
    source=replace_once(source,'    LD A,102\n    CALL t_mapper\n    JP ai_body\n',
        f'    JP ai_body\n    DS ${s["ai_call"]:04X}-$,0\n')
    source=replace_once(source,'    LDIR\n    LD A,102\n    JP t_mapper\nai_bulk_enter:',
        f'    LDIR\n    LD A,102\n    RET\n    DS ${s["ai_bulk_enter"]:04X}-$,0\nai_bulk_enter:')
    source=replace_once(source,'    LD DE,ai_contexts\n    ADD HL,DE\n    LD A,(HL)\n','    CALL cx_find_context\n')
    if source.count('    ORG $B800')!=2:raise ValueError('two original native/bulk origins required')
    source=source.replace('    ORG $B800',f'    ORG ${origin:04X}',1)
    first=source.index('ai_body_end:');last=source.index('    ORG $B800',first)
    source=source[:first]+f'ai_body_end:\n    INCLUDE "compact_bear_context_branch.asm"\nai_end:\n    ASSERT $ <= ${end:04X}\n\n'+source[last:]
    code,q=assemble('bi-resident',source);new_ram=q['ai_ram_end']-q['ai_entry'];body_size=q['ai_end']-q['ai_body'];body=code[new_ram:new_ram+body_size]
    if new_ram!=ram or any(q[n]!=s[n] for n in ('ai_entry','ai_call','ai_copy','ai_bulk_enter','ai_bulk_back','ai_bulk_ids','ai_bulk_upload')):
        raise ValueError('public native RAM ABI changed')
    if code[new_ram+body_size:]!=original[ram+2048:]:raise ValueError('native bulk code would change; keep its later strip patch intact')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    patch(ram_at,code[:new_ram],'same native helper addresses; resident entry and no102 copy-return map')
    patch(origin-0x4000,body,'resident native bear body plus fully proven sparse context branches')
    patch(102*16384+0x3800,bytes([255])*2048,'retired banked native bear body/context table')
    gate=s['p_template_half'];before=bytes((0x3E,56,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xCD,0,0xA8,0x3E,102,0xC3,s['t_mapper']&255,s['t_mapper']>>8))
    if parent[gate-0x4000:gate-0x4000+len(before)]!=before:raise ValueError('original native tile constructor bridge changed')
    after=before[:10]+bytes((0xC9,255,255))
    patch(gate-0x4000,after,'resident native bear caller does not need102 after tile construction')
    native_at=115*16384+0x3800+s['an_native']-0xE900
    before=bytes((0x3E,102,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xCD,q0['ai_body']&255,q0['ai_body']>>8,0x3E,114,0xC3,s['t_mapper']&255,s['t_mapper']>>8))
    if parent[native_at:native_at+len(before)]!=before:raise ValueError('original three-sprite bear fallback bridge changed')
    after=bytes((0xCD,origin&255,origin>>8,0x3E,114,0xC3,s['t_mapper']&255,s['t_mapper']>>8))+bytes([255])*5
    patch(native_at,after,'three-sprite fallback calls resident native bear and restores its114 caller')
    node=m['compact_retired_resident'];rows=[r for r in node['ranges'] if r['address']==origin and r['size']==end-origin]
    if len(rows)!=1:raise ValueError('exact reclaimed decoder allocation required')
    rows[0].clear();rows[0].update(address=origin+body_size,size=end-origin-body_size)
    node['reused_for_resident_code_bytes']+=body_size;m['compact_retired_names']['reused_for_bear_code_bytes']=body_size
    m['compact_retired_graphics']['ranges'].append(dict(bank=102,address=0xB800,size=2048,kind='retired banked native bear body/context table'))
    m['compact_retired_graphics']['retired_physical_bytes']+=2048
    fixed=m['fixed_clock'];at=115*16384+0x3800;fixed['ram_code_sha256']=digest(target[at:at+fixed['ram_code_bytes']])
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    for n in ('scripts/build_compact_bear_resident.py','scripts/compact_bear_context_probe.py','src/compact_bear_context_branch.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_bear_resident']=dict(parent_rom_sha256=digest(parent),patches=patches,resident_address=origin,resident_body_bytes=body_size,
        reproduced_compact_source_sha256=source_input_sha,complete_context_indices=1024,old_context_bytes=1024,new_context_data_bytes=0,
        original_bulk_code_and_patch_retained=True,public_RAM_ABI_preserved=True,no102_mapper_round_trips_in_native_body=True,
        mapperless=False,human_test_candidate=False)
    m['bear_native'].update(body_bank=0,body_address=origin,context_encoding='exact nine branch cases')
    for n in list(s):
        if n.startswith('ai_') and n not in q:del s[n]
    s.update({n:v for n,v in q.items() if n.startswith(('ai_','cx_'))});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    filename='frostbite-compact-bear-resident-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-bear-resident-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Resident native bear body and exact sparse context code; full game/cadence proof required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),resident_body_bytes=body_size,remaining_decoder_bytes=end-origin-body_size))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
