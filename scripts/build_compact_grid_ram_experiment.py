"""Add compact prepared-NAME construction to an internal packet experiment."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_grid_fast_probe import prepared_data
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,control,out):
    base=Path(base).resolve();control=Path(control).resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh experiment output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_packet_experiment') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('bound packet integration experiment required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    cm=json.loads((control/'build.json').read_bytes());rom=(control/cm['rom']['filename']).read_bytes()
    if digest(rom)!=CONTROL_SHA:raise ValueError('sealed v30 control required')
    assets,_,_=prepared_data(rom);s=symbols(base/'presentation.sym')
    rows=m['coherent_x']['auxiliary_code']
    owners=[row for row in rows if row['ram_address']<=s['ag_floe']<row['ram_address']+row['size']]
    if len(owners)!=1:raise ValueError('unique copied-code owner required')
    owner=owners[0]
    def location(address):return owner['bank']*16384+owner['rom_address']-0x8000+address-owner['ram_address']
    # ag_floe's former padding is live prefix/credit/atlas code. Reuse only
    # i_shifts, whose sole indirect reader was removed by the packet gate.
    oldstart=s['i_shifts']-0x4000
    if parent[oldstart:oldstart+64]!=rom[oldstart:oldstart+64]:raise ValueError('retired shift arena changed')
    body=parent[location(s['ag_floe']):location(s['ag_floe_end'])]
    needle=bytes((0xC3,s['x_name_row']&255,s['x_name_row']>>8))
    if body.count(needle)!=1:raise ValueError('unique prepared-grid tail call required')
    callsite=location(s['ag_floe'])+body.index(needle)
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for n,b in assets.items():(out/('grid-'+n+'.bin')).write_bytes(b)
    asm=[' ORG $B800',' DEFINE CG_OUTPUT $C480','cg_rows EQU $BA00','cg_directory EQU $BE20','cg_bases EQU $BE00','cg_waters EQU $BE10',
         ' INCLUDE "compact_grid_fast.asm"',' ASSERT $ <= $BA00']
    for n,a in (('rows',0xBA00),('directory',0xBD00),('bases',0xBE00),('waters',0xBE10)):
        asm += [f' DS ${a:04X}-$,$FF',f' INCBIN "{out/("grid-"+n+".bin")}"']
    asm += [' DS $BE20-$,$FF',' DB '+','.join(map(str,range(22))),
            ' DS $BF00-$,$FF','cg_expand:',
            ' LD HL,$BD00',' LD DE,$1000',' LD BC,160',' LDIR',
            ' LD HL,$1000',' LD B,160','cg_directory_loop:',
            ' LD A,(HL)',' ADD A,17',' LD (HL),A',' INC HL',' DJNZ cg_directory_loop',
            ' XOR A',' LD ($C7F0),A',' LD DE,$1100','cg_template_loop:',
            ' XOR A',' LD ($C7F1),A','cg_owner_loop:',
            ' PUSH DE',' CALL $B800',' POP DE',' LD HL,$C480',' LD BC,32',' LDIR',
            ' LD A,($C7F1)',' INC A',' LD ($C7F1),A',' CP 8',' JR C,cg_owner_loop',
            ' LD A,($C7F0)',' INC A',' LD ($C7F0),A',' CP 22',' JR C,cg_template_loop',' RET',
            ' ASSERT $ <= $C000']
    (out/'grid-bank.asm').write_text('\n'.join(asm)+'\n');assembler=verified_tool('sjasmplus')
    def assemble(name):
        p=out/name;r=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={p.with_suffix(".bin")}',f'--sym={p.with_suffix(".sym")}',str(p)],capture_output=True,text=True,timeout=60)
        p.with_suffix('.log').write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('grid assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return p.with_suffix('.bin').read_bytes()
    bank=assemble('grid-bank.asm')
    asm=[f' ORG ${s["i_shifts"]:04X}']
    for n in ('p_tl_delta_index','p_tl_root','PAGE','p_w_row','t_mapper','x_name_row','t_enabled'):asm.append(f'{n} EQU ${s[n]:04X}')
    asm += [' LD A,(t_enabled)',' OR A',' JR Z,cg_cold',' LD A,(p_tl_delta_index)']+[' RLCA']*4
    asm += [' LD B,A',' LD A,(p_tl_root)',' AND 15',' OR B',' LD L,A',' LD H,$10',' LD H,(HL)',
            ' LD A,(PAGE)',' ADD A,A',' ADD A,A',' LD B,A',' LD A,(p_w_row)',' ADD A,B']+[' RLCA']*5
    asm += [' LD L,A',' JP x_name_row','cg_cold:',
            ' PUSH DE',' LD A,(p_tl_delta_index)']+[' RLCA']*4
    asm += [' LD B,A',' LD A,(p_tl_root)',' AND 15',' OR B',' LD ($C7F0),A',
            ' LD A,(PAGE)',' ADD A,A',' ADD A,A',' LD B,A',' LD A,(p_w_row)',' ADD A,B',' LD ($C7F1),A',
            ' LD A,45',' CALL t_mapper',' LD A,($C7F0)',' LD L,A',' LD H,$BD',' LD A,(HL)',' LD ($C7F0),A',' CALL $B800',' POP DE',' LD HL,$C480',' JP x_name_row','cg_boot:',
            ' LD A,45',' CALL t_mapper',' CALL $BF00',' LD A,1',' CALL t_mapper',
            ' LD A,$C3',' LD ($0038),A',' RET',f' ASSERT $ <= ${s["i_shift2"]:04X}']
    (out/'grid-gate.asm').write_text('\n'.join(asm)+'\n');gate=assemble('grid-gate.asm')
    target=bytearray(parent);patches=[]
    gates=symbols(out/'grid-gate.sym')
    kernel_at=115*16384+0x3800
    kernel_size=m['fixed_clock']['ram_code_bytes']
    kernel=parent[kernel_at:kernel_at+kernel_size]
    first=s['t_start_clock']-0xE900;last=s['t_start_clock.fault']-0xE900
    boot_old=bytes.fromhex('3ec3323800')
    if kernel[first:last].count(boot_old)!=1:raise ValueError('unique pre-IRQ RAM takeover hook required')
    boot_at=kernel_at+kernel.index(boot_old,first,last)
    boot_new=bytes((0xCD,gates['cg_boot']&255,gates['cg_boot']>>8,0,0))

    replacement=bytes((0xC3,s['i_shifts']&255,s['i_shifts']>>8))
    for at,b,reason in ((boot_at,boot_new,'expand lower-RAM grid before installing the IRQ vector'),(45*16384+0x3800,bank,'compact grid-name constructor/data'),(oldstart,gate,'resident gate in retired i_shifts arena'),(callsite,replacement,'prepared-grid caller only; atlas keeps existing shared row copier')):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    def refresh(node):
        if isinstance(node,dict):
            if all(k in node for k in ('bank','rom_address','ram_address','size','sha256')):
                at=node['bank']*16384+node['rom_address']-0x8000;node['sha256']=digest(target[at:at+node['size']])
            for value in node.values():refresh(value)
        elif isinstance(node,list):
            for value in node:refresh(value)
    refresh(m)
    m['fixed_clock']['ram_code_sha256']=digest(target[kernel_at:kernel_at+kernel_size])
    world=bytes(target[owner['bank']*16384+owner['rom_address']-0x8000:owner['bank']*16384+owner['rom_address']-0x8000+owner['size']])
    (out/'world.bin').write_bytes(world);m['world_x']['code_sha256']=digest(world)
    for row in m['contact14']['arena']:
        if row['bank'] in (45,owner['bank']):row['packed_sha256']=digest(target[row['bank']*16384:(row['bank']+1)*16384])
    for n in ('scripts/build_compact_grid_ram_experiment.py','scripts/compact_grid_fast_probe.py','src/compact_grid_fast.asm','scripts/compact_grid_name_probe.py'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='compact-packet-grid-internal-experiment',source_commit=commit,source_dirty=dirty,
        complete_source=dict(commit=commit,working_tree_dirty=dirty,files=m['source_files'],scope='Internal compact grid/packet integration; full mapper ROM retained.'))
    m['compact_grid_experiment']=dict(parent_rom_sha256=digest(parent),patches=patches,code_rom_bank=45,
        output='direct immutable lower-RAM row; C480..C49F staging only during bootstrap',
        scratch='C7F0..C7F1 bootstrap only',normalized_data_bytes=864,owner_table_bytes=16,
        expanded_ram_directory=[0x1000,0x10A0],expanded_ram_rows=[0x1100,0x2700],
        expansion='startup only, after page0 RAM takeover and before enabling game IRQ',
        old_name_records_retained=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-grid-internal.rom';(out/filename).write_bytes(target);m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=digest(target),patches=len(patches),internal_experiment=True));return m


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--control',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.control,a.out)
