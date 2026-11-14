"""Internal size/cadence experiment on sealed v30; not a compact delivery."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def digest(data):return hashlib.sha256(data).hexdigest()


def build(base,out):
    base=Path(base).resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh experiment output required')
    metadata=(base/'build.json').read_bytes();m=json.loads(metadata);parent=(base/m['rom']['filename']).read_bytes()
    if digest(parent)!=CONTROL_SHA or any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):
        raise ValueError('sealed v30 source closure required')
    s=symbols(base/'presentation.sym')
    if s['i_packets_bank']!=252 or s['i_packets']!=0x9CE6:raise ValueError('audited packet arena differs')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    def read(bank,a,n):
        at=bank*16384+a-0x8000;return parent[at:at+n]
    mapping=read(1,s['p_geo_row_map_data'],256);roots={v:k for k,v in enumerate(mapping) if v<33}
    data=dict(original=read(2,s['original_data']+256,256),expansion=read(2,s['p_sprite_expansion_data'],1024),
              reverse=read(2,s['p_sprite_reverse_data'],256),shapes=bytes(roots[i] for i in range(33)))
    for n,b in data.items():(out/('compact-'+n+'.bin')).write_bytes(b)
    asm=[' ORG $9CE6','ct_original EQU $9F00','ct_expansion EQU $A200','ct_reverse EQU $A600','ct_shapes EQU $A700',
         ' INCLUDE "compact_enemy_packet.asm"',' ASSERT $ <= $A000',' DS $A000-$,$FF']
    for n,a in (('original',0xA000),('expansion',0xA200),('reverse',0xA600),('shapes',0xA700)):
        if n in ('expansion','shapes'):asm.append(f' DS ${a:04X}-$,$FF')
        asm.append(f' INCBIN "{out/("compact-"+n+".bin")}"')
    asm+=[' ASSERT $ <= $A946',' DS $A946-$,$FF'];(out/'compact-bank.asm').write_text('\n'.join(asm)+'\n')
    assembler=verified_tool('sjasmplus')
    def assemble(name):
        p=out/name
        r=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={p.with_suffix(".bin")}',f'--sym={p.with_suffix(".sym")}',str(p)],capture_output=True,text=True,timeout=60)
        p.with_suffix('.log').write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('experiment assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return p.with_suffix('.bin').read_bytes()
    bank=assemble('compact-bank.asm');q=symbols(out/'compact-bank.sym')
    wrapper=[f' ORG ${s["i_generate"]:04X}']
    for n in ('p_w_group','p_w_x','p_w_y','i_lines','i_done','t_mapper'):wrapper.append(f'{n} EQU ${s[n]:04X}')
    wrapper += [' LD A,(p_w_group)',' LD ($C7E0),A',' LD A,(p_w_x)',' AND 15',' LD ($C7E1),A',
                ' LD A,(p_w_y)',' AND 7',' LD ($C7E2),A',' LD A,252',' CALL t_mapper',
                f' CALL ${q["ct_build"]:04X}',' LD (i_lines),A',' JP i_done',f' ASSERT $ <= ${s["i_done"]:04X}',f' DS ${s["i_done"]:04X}-$,$FF']
    (out/'compact-wrapper.asm').write_text('\n'.join(wrapper)+'\n');gate=assemble('compact-wrapper.asm')
    rom=bytearray(parent);patches=[]
    def patch(at,blob,reason):
        old=parent[at:at+len(blob)];rom[at:at+len(blob)]=blob
        patches.append(dict(offset=at,size=len(blob),before_sha256=digest(old),after_sha256=digest(blob),reason=reason))
    patch(s['i_generate']-0x4000,gate,'resident constructor gate; original i_done publishes i_valid')
    patch(252*16384+s['i_packets']-0x8000,bank,'replace audited dead-after-gate packet directory only')
    allowed={i for p in patches for i in range(p['offset'],p['offset']+p['size'])}
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(parent,rom))):raise ValueError('unexpected patch')
    for n in ('scripts/build_compact_packet_experiment.py','src/compact_enemy_packet.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    for row in m['contact14']['arena']:
        if row['bank']==252:row['packed_sha256']=digest(rom[252*16384:253*16384])
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='compact-packet-internal-experiment',source_commit=commit,source_dirty=dirty,
             complete_source=dict(commit=commit,working_tree_dirty=dirty,files=m['source_files'],scope='Internal packet-constructor integration experiment; full mapper ROM retained.'))
    m['compact_packet_experiment']=dict(parent_rom_sha256=CONTROL_SHA,patches=patches,constructor_rom_bank=252,
        code_bytes=q['ct_end']-q['ct_build'],scratch='C7E0..C7E2 inputs, C7E5..C7E9 scratch',
        output='existing C180..C1AF',old_packet_payloads_retained=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-packet-internal.rom';(out/filename).write_bytes(rom)
    m['rom'].update(filename=filename,sha256=digest(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    if (base/'build.json').read_bytes()!=metadata:raise ValueError('control metadata changed')
    print(dict(rom_sha256=digest(rom),patches=len(patches),internal_experiment=True));return m


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
