"""Explicit border24 view oracle; original CPU/RAM and active-page guards retained."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

from environment import ROOT
import presentation_direct_enemy as actors
import presentation_fixed_clock_probe as legacy
import presentation_matrix_check as matrix
import presentation_prepared_check as prepared
from presentation_dirty import scene
from presentation_grid24 import anchor,actor_segments,dirty_rows,delta_table
from presentation_border import expected_frame
from presentation_ready_check import ready_contract,verify_admission
from render_build import symbols

def check(build,out,mode,steps=2252):
    build,out=Path(build).resolve(),Path(out).resolve()
    m=verify_admission(build)
    if not m.get('border_clip'):
        from presentation_grid24_check import check as original_check
        return original_check(build,out,mode,steps)
    if m['border_clip']['view']!='border24-v1':raise ValueError('qualified border24 view required')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    rom=(build/m['rom']['filename']).read_bytes();s=symbols(build/'presentation.sym')
    if rom[119*16384+0x3e00:120*16384]!=delta_table():raise ValueError('runtime contact lookup differs')
    producers={str(p.relative_to(ROOT)):sha(p)for p in(Path(__file__).resolve(),ROOT/'scripts/presentation_border.py',ROOT/'scripts/presentation_grid24.py')}
    old_run=subprocess.run;old_frame=legacy.adapted_frame;old_matrix=matrix.adapted_frame;old_roles=actors.segments;old_audit=matrix.audit_scene
    history=None;captured=None;case=0
    def roles(page,lane):
        return[dict(bank=b,tile=t,pgt=0x4000+b*2048+t*8,key=0xd000+(page*3+b)*384+(t%64)*6,water=130 if b==1 else 129)for b,t in actor_segments(page,lane)]
    def sat_lanes(vram,page):
        bits=0
        for at in range(0x1b00,0x1b80,4):
            if vram[at]==208:break
            ident=vram[at+2];base=72+96*page
            if base<=ident<=base+12 and not(ident-base)%4:bits|=1<<((ident-base)//4)
        return bits
    def audit(raw,ram,rng,histories,page):
        nonlocal history,captured,case
        if captured is None:captured=(out/'captures.bin').read_bytes()
        if history is None:
            history=[0,0];bootpage=captured[16384+2]-6;history[bootpage]=sat_lanes(captured[:16384],bootpage)
        state=scene(ram,rng,layout=raw[68],width=raw[69]);previous=history[page]
        at=(case*2+2)*matrix.CAPTURE_BYTES;vram=captured[at:at+16384];base=[]
        for pos in range(0x1b00,0x1b80,4):
            if vram[pos]==208:break
            ident=vram[pos+2];first=72+96*page
            if first<=ident<=first+12 and not(ident-first)%4:continue
            base.append(vram[pos:pos+4])
        invalid=0
        if not ram[63]&128:
            for lane in range(4):
                if not previous&(1<<lane):continue
                mode=ram[88+lane];copies=((0,),(0,16),(0,32),(0,16,32))[mode]
                xs=[((ram[84+lane]+offset)&255)%160 for offset in copies];y=anchor('enemy',lane)
                eligible=len(base)<=19 and len(base)+len(copies)<32 and(mode==0 and xs[0]!=0 or mode!=0 and all(11<=x<=152 for x in xs))
                overlaps=sum(abs(((sp[0]+1)&255)-y)<16 for sp in base if sp[2]!=252)
                if not(eligible and overlaps+len(copies)<=4):invalid|=1<<lane
        prior=histories[page]
        if prior is not None:
            reduced=bytearray(prior)
            for lane in range(4):
                hidden=prior[23+lane*5:25+lane*5]==bytes(2)and state[23+lane*5:25+lane*5]==bytes(2)
                if previous&(1<<lane)and not invalid&(1<<lane)or hidden:
                    x=20+lane*5;reduced[x:x+5]=state[x:x+5]
            prior=bytes(reduced)
        rows=dirty_rows(prior,state)
        if not ram[63]&128:
            rows.update(anchor('enemy',lane)//8 for lane in range(4)if invalid&(1<<lane))
        flags=bytes(sum(1<<(row&7)for row in rows if row//8==bank)for bank in range(3))
        if len(raw)!=70 or raw[:64]!=state or raw[64:67]!=flags or raw[67]!=page:
            raise ValueError(f'grid24 exact dirty union differs at case{case}: actual{raw[64:67].hex()} expected{flags.hex()}')
        current=sat_lanes(vram,page)
        if not ram[63]&128:
            for lane in range(4):
                if current&(1<<lane)and not previous&(1<<lane)and anchor('enemy',lane)//8 not in rows:
                    raise ValueError('new grid SAT lane retained an uncleared tile row')
        histories[page]=state;history[page]=current;case+=1
        return len(rows)
    def run(args,*a,**kw):
        if isinstance(args,list)and'-script'in args and'openmsx'in Path(args[0]).name.lower():
            path=Path(args[args.index('-script')+1]);text=path.read_text()
            fail='fail_matrix'if'proc guard_matrix'in text else'fail';guard='guard_matrix'if fail=='fail_matrix'else'guard'
            needle=f'proc {guard} {{}} {{';assert text.count(needle)==1
            extra=''
            for row in m['coherent_x']['auxiliary_code']:
                at=row['bank']*16384+row['rom_address']-0x8000;data=rom[at:at+row['size']]
                if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('auxiliary code hash differs')
                extra+=f'\n if {{[debug read_block memory {row["ram_address"]} {len(data)}] ne [binary format H* {data.hex()}]}} {{{fail} auxiliary-code}}\n'
            path.write_text(text.replace(needle,needle+extra))
        return old_run(args,*a,**kw)
    legacy.adapted_frame=matrix.adapted_frame=expected_frame;actors.segments=roles;matrix.audit_scene=audit;subprocess.run=run
    try:
        with ready_contract(build):
            if mode in('ntsc','pal'):result=legacy.probe(build,out,mode,steps,expanded=(mode=='pal'))
            elif mode.startswith('boundary-'):
                from presentation_fixed_clock_boundaries import check as boundaries
                f='pal'if mode=='boundary-pal'else'ntsc'
                boundaries(build,out,f,expanded=(f=='pal'),negative_register=(mode=='boundary-negative'))
                result=json.loads((out/('negative-check.json'if mode=='boundary-negative'else'boundary-check.json')).read_text())
            elif mode=='matrix':result=prepared.check(build,out,steps)
            elif mode=='header':
                import presentation_header_reuse_check as header
                result=header.exercise(build,out)
            elif mode=='density':
                previous=matrix.check
                matrix.check=lambda b,o,**kw:prepared.check(b,o,kw['limit'])
                argv=sys.argv
                try:sys.argv=[str(ROOT/'scripts/presentation_native_density.py'),str(build),str(out)];runpy.run_path(sys.argv[0],run_name='__main__')
                finally:sys.argv=argv;matrix.check=previous
                result=json.loads((out/'check.json').read_text())
            else:raise ValueError('unknown grid24 validation mode')
    finally:
        legacy.adapted_frame=old_frame;matrix.adapted_frame=old_matrix;actors.segments=old_roles;matrix.audit_scene=old_audit;subprocess.run=old_run
    if producers!={n:sha(ROOT/n)for n in producers}:raise ValueError('grid oracle changed during run')
    receipt=dict(complete=True,rom_sha256=m['rom']['sha256'],view='border24-v1',mode=mode,producers=producers,
        receipts={p.name:sha(p)for p in out.glob('*check.json')},scope='Declared layout/border adaptation only. Original source-state, physical ownership and active-page checks retained; exact border pixels and dirty union independently checked.')
    (out/'border24-contract.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256']));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('build',type=Path);p.add_argument('out',type=Path);p.add_argument('mode',choices=('ntsc','pal','matrix','density','header','boundary-ntsc','boundary-pal','boundary-negative'));p.add_argument('steps',type=int,nargs='?',default=2252);a=p.parse_args();check(a.build,a.out,a.mode,a.steps)
