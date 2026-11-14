"""Compact native bear records to64 bytes; derive context codes at lookup."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_bear_tile_probe import assets
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def once(text,old,new):
    if text.count(old)!=1:raise ValueError('unique source transformation required: '+old[:65])
    return text.replace(old,new,1)


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_bear_tile') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound native bear tile integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    control=ROOT/'outputs/presentation/credit-reference-at/build-final';cm=json.loads((control/'build.json').read_bytes());cr=(control/cm['rom']['filename']).read_bytes()
    if digest(cr)!=CONTROL_SHA:raise ValueError('sealed control required')
    data,_,_,codes=assets(control);s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in s.items() if '.' not in n and not n.startswith('ai_'))+'\n')
    source=(ROOT/'src/presentation_bear_native.asm').read_text()
    # Accepted open-view adaptation: left clipping is disabled. This single
    # INC A->NOP differs from the original public native-bear producer.
    source=once(source,'    JR NZ,.clip\n    INC A\n.clip:','    JR NZ,.clip\n    NOP\n.clip:')
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/(name+".bin")}',
            f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes(),symbols(out/(name+'.sym'))
    baseline,q=assemble('br-baseline',source);ram=q['ai_ram_end']-q['ai_entry']
    pieces=((115,0xB800+q['ai_entry']-0xE900,baseline[:ram]),(102,0xB800,baseline[ram:ram+2048]),(112,0xB800,baseline[ram+2048:]))
    for bank,a,b in pieces:
        if cr[bank*16384+a-0x8000:bank*16384+a-0x8000+len(b)]!=b:raise ValueError('audited native module does not reproduce accepted control')
    source=once(source,'    LD DE,20\n    LD C,12\n.ids:','    LD DE,4\n    LD C,12\n.ids:')
    a=source.index('    LD A,(p_tf_cache)\n    LD B,A\n');b=source.index('    LD DE,p_geo_columns\n',a)
    source=source[:a]+'''    LD A,(p_tf_cache)
    LD B,A
    DUP 5
    SRL A
    EDUP
    ADD A,67
    LD (p_tf_column),A
    LD A,B
    AND 31
    LD L,A
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD DE,$B800
    ADD HL,DE
    LD (p_tf_cache),HL
    LD A,L
    ADD A,48
    LD L,A
'''+source[b:]
    source=once(source,'''    ADD HL,HL
    ADD HL,HL
    PUSH HL
    ADD HL,HL
    ADD HL,HL
    POP DE
    ADD HL,DE
    LD DE,(p_tf_cache)
''','''    ADD HL,HL
    ADD HL,HL
    LD DE,(p_tf_cache)
''')
    source=once(source,'    LD BC,20\n    CALL ai_copy','    LD BC,4\n    CALL ai_copy')
    source=once(source,'''    ADD A,A
    ADD A,p_geo_ids+2 & 255
    LD L,A
    LD H,p_geo_ids/256
    LD E,(HL)
    INC HL
    LD D,(HL)
    BIT 7,D
    RET NZ                 ;same empty-left-clip skip as the original driver
''','''    LD C,A                 ;certified context0..8
    LD HL,(p_geo_ids+2)     ;dense mask plus original empty-left predicate
    LD A,(pf_key+3)
    OR A
    JR Z,.unclipped
    BIT 7,H
    RET NZ
.unclipped:
    LD A,H
    AND 1
    LD D,A
    LD E,L
    LD A,C
    ADD A,A
    OR D
    LD D,A
''')
    a=source.index('.miss:\n    POP DE\n',source.index('ai_tile:'));b=source.index('    LD A,(p_w_tile)\n',a)
    source=source[:a]+'.miss:\n    POP DE\n    CALL $4FE3\n'+source[b:]
    code,q=assemble('br-compact',source)
    if q['ai_entry']!=s['ai_entry'] or q['ai_copy']!=s['ai_copy'] or q['ai_bulk_ids']!=s['ai_bulk_ids'] or q['ai_ram_end']-q['ai_entry']!=ram:
        raise ValueError('public RAM helper ABI changed')
    records=bytearray()
    for i in range(m['bear_native']['records']):
        bank=67+i//8;at=bank*16384+0x3800+(i%8)*256;old=parent[at:at+256];record=bytearray(64)
        for cell in range(old[240]*old[241]):
            raw=int.from_bytes(old[cell*20:cell*20+2],'little');dense=codes[(raw,0)]
            mask=data['patterns'][dense*8:dense*8+8];empty=not any(v&15 for v in mask)
            record[cell*4:cell*4+4]=raw.to_bytes(2,'little')+(dense|(0x8000 if empty else 0)).to_bytes(2,'little')
        record[48:64]=old[240:256];records.extend(record)
    if len(records)!=6144:raise ValueError('complete96 compact records required')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    patch(115*16384+0x3800+q['ai_entry']-0xE900,code[:ram],'same-address native RAM helper and compact ID stride')
    patch(102*16384+0x3800,code[ram:ram+2048],'compact native bear record addressing and direct context derivation')
    patch(112*16384+0x3800,code[ram+2048:],'native bulk path relinked to unchanged public RAM ABI')
    for b in range(67,79):
        payload=records[(b-67)*2048:(b-66)*2048] if b<70 else bytes([255])*2048
        patch(b*16384+0x3800,payload,'compact64-byte native bear records' if b<70 else 'retired old256-byte record tail')
        if b>=70:m['compact_retired_graphics']['ranges'].append(dict(bank=b,address=0xB800,size=2048,kind='retired bear expanded records'))
    m['compact_retired_graphics']['retired_physical_bytes']+=9*2048
    fixed=m['fixed_clock'];at=115*16384+0x3800;fixed['ram_code_sha256']=digest(target[at:at+fixed['ram_code_bytes']])
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    for n in ('scripts/build_compact_bear_records.py',):m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_bear_records']=dict(parent_rom_sha256=digest(parent),patches=patches,old_record_bytes=24576,new_record_bytes=6144,
        record_count=96,record_stride=64,logical_id_and_strip_metadata_retained=True,accepted_module_reproduced=True,
        accepted_open_view_nop_retained=True,mapperless=False,human_test_candidate=False)
    s.update({n:v for n,v in q.items() if n.startswith('ai_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    filename='frostbite-compact-bear-records-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-bear-records-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Compact bear64-byte records; full route and cadence qualification required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),record_bytes=6144,non_ff_bytes=sum(v!=255 for v in target)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
