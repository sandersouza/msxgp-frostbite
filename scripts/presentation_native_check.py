"""Validate native lanes with exact representation-dependent dirty unions."""
import json,subprocess,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('scripts').resolve()))
from render_build import symbols
HERE=Path(__file__).resolve().parent
build=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();mode=sys.argv[3];limit=int(sys.argv[4]) if len(sys.argv)>4 else 2115
meta=json.loads((build/'build.json').read_text());code=(build/'world.bin').read_bytes();s=symbols(build/'presentation.sym');original_run=subprocess.run
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args,*a,**kw):
 if isinstance(args,list) and '-script'in args and 'openmsx'in Path(args[0]).name.lower():
  script=Path(args[args.index('-script')+1]);text=script.read_text();fail='fail_matrix' if 'proc guard_matrix'in text else 'fail';guard='guard_matrix' if fail=='fail_matrix' else 'guard'
  needle=f'proc {guard} {{}} {{';assert text.count(needle)==1
  check=''
  rom=(build/meta['rom']['filename']).read_bytes()
  for r in meta['coherent_x']['auxiliary_code']:
   at=r['bank']*16384+r['rom_address']-0x8000;data=rom[at:at+r['size']];assert hashlib.sha256(data).hexdigest()==r['sha256']
   check+=f'\n if {{[debug read_block memory {r["ram_address"]} {len(data)}] ne [binary format H* {data.hex()}]}} {{{fail} auxiliary-code}}\n'
  text=text.replace(needle,needle+check)
  if mode in ('ntsc','pal'):
   text+=f'''
set x_irq_sum 0
set x_irq_open 0
set x_cost [open {{{out/'world-costs.tsv'}}} w]
proc x_irq_done {{}} {{
 if {{!$::x_irq_open || [reg SP]!=$::x_irq_sp}} {{return}}
 incr ::x_irq_sum [expr {{round(([machine_info time]-$::x_irq_time)*3579545)}}]
 set ::x_irq_open 0
 debug remove_bp $::x_irq_bp
}}
debug set_bp {s['t_irq']} {{}} {{
 set ::x_irq_open 1;set ::x_irq_time [machine_info time];set ::x_irq_sp [expr {{[reg SP]+2}}]
 set ::x_irq_bp [debug set_bp [word [reg SP]] {{[reg SP]==$::x_irq_sp}} x_irq_done]
}}
proc x_irq_sync {{}} {{if {{$::x_irq_open && ![debug read memory {s['t_in_irq']}] && [reg SP]==$::x_irq_sp}} {{x_irq_done}}}}
debug set_bp {s['presentation_world_prepare']} {{}} {{x_irq_sync;set ::x_start [machine_info time];set ::x_irq_start $::x_irq_sum}}
debug set_bp {s['p_fast_upload_dirty'] if (build/'hybrid.bin').exists() and 'x_preflight' not in s else s['presentation_hud_prepare']} {{}} {{
 x_irq_sync
 puts $::x_cost "$::committed [expr {{round(([machine_info time]-$::x_start)*3579545)-($::x_irq_sum-$::x_irq_start)}}]"
 flush $::x_cost
}}
'''
  script.write_text(text)
 return original_run(args,*a,**kw)
subprocess.run=run
# Preserve original normalized-state check while declaring the additional forced
# world rows needed whenever tile/SAT representation can switch with P0 overlap.
import presentation_matrix_check as mm
from presentation_dirty import scene,dirty_rows
original_audit_scene=mm.audit_scene
hybrid_history=None
hybrid_captured=None
hybrid_case=0
def sat_lanes(vram,page):
 bits=0
 for i in range(0x1B00,0x1B80,4):
  if vram[i]==208:break
  identifier=vram[i+2];base=72+96*page
  if base<=identifier<=base+12 and not (identifier-base)%4:bits|=1<<((identifier-base)//4)
 return bits
def hybrid_audit_scene(raw,ram,rng,histories,page):
 global hybrid_history,hybrid_case,hybrid_captured
 state=scene(ram,rng,layout=raw[68],width=raw[69]);rows=dirty_rows(histories[page],state)
 flags=bytes(sum(1<<(row&7) for row in rows if row//8==bank) for bank in range(3))
 want=bytearray(flags)
 if 'x_force_previous' in s:
  if hybrid_captured is None:hybrid_captured=(out/'captures.bin').read_bytes()
  cap=hybrid_captured
  if hybrid_history is None:
   hybrid_history=[0,0];bootpage=cap[16384+2]-6;hybrid_history[bootpage]=sat_lanes(cap[:16384],bootpage)
  previous=hybrid_history[page]
  mask=previous
  at=(hybrid_case*2+2)*mm.CAPTURE_BYTES
  vram=cap[at:at+16384]
  if 'x_preflight' in s:
   base=[]
   for pos in range(0x1B00,0x1B80,4):
    if vram[pos]==208:break
    ident=vram[pos+2];first=72+96*page
    if first<=ident<=first+12 and not (ident-first)%4:continue
    base.append(vram[pos:pos+4])
   mask=0
   if not ram[63]&128:
    for lane in range(4):
     if not previous&(1<<lane):continue
     mode=ram[88+lane];copies=((0,),(0,16),(0,32),(0,16,32))[mode]
     xs=[((ram[84+lane]+offset)&255)%160 for offset in copies]
     y=153-26*lane+(0 if ram[104]<150 else 1)
     eligible=(len(base)<=19 and len(base)+len(copies)<32 and (mode==0 or all(8<=x<=152 for x in xs)))
     overlaps=sum(abs(((sprite[0]+1)&255)-y)<16 for sprite in base if sprite[2]!=252)
     eligible &= overlaps+1+len(copies)<=4
     if not eligible:mask|=1<<lane
  if 'x_actor_dirty_gate' in s:
   prior=histories[page]
   if prior is not None:
    reduced=bytearray(prior)
    for lane in range(4):
     hidden=('x_hidden_dirty' in s and prior[23+lane*5:25+lane*5]==bytes(2) and state[23+lane*5:25+lane*5]==bytes(2))
     if previous&(1<<lane) and not mask&(1<<lane) or hidden:
      atfield=20+lane*5;reduced[atfield:atfield+5]=state[atfield:atfield+5]
    precise=dirty_rows(bytes(reduced),state)
    want=bytearray(sum(1<<(row&7) for row in precise if row//8==bank) for bank in range(3))
  want[1]|=(128 if mask&2 else 0)|(48 if mask&4 else 0)|(6 if mask&8 else 0)
  want[2]|=(24 if mask&1 else 0)|(1 if mask&2 else 0)
  at=(hybrid_case*2+2)*mm.CAPTURE_BYTES
  current=sat_lanes(cap[at:at+16384],page)
  for lane in range(4):
   if current&(1<<lane) and not ('x_preflight' in s and previous&(1<<lane)):
    y=153-26*lane+(0 if ram[104]<150 else 1)
    if any(not want[row//8]&(1<<(row&7)) for row in {y//8,(y+7)//8}):raise ValueError('new SAT lane retained a clean NAME row')
  hybrid_history[page]=current;hybrid_case+=1
 elif not ram[63]&128:want[1]|=182;want[2]|=25
 if raw[64:67]!=want:raise ValueError('hybrid dirty rows differ from exact declared union')
 original_audit_scene(raw[:64]+flags+raw[67:],ram,rng,histories,page)
 return sum(b.bit_count() for b in want)
if (build/'hybrid.bin').exists():mm.audit_scene=hybrid_audit_scene
try:
 if mode in ('ntsc','pal'):
  import presentation_fixed_clock_probe as p
  result=p.probe(build,out,mode,limit,expanded=(mode=="pal"))
 else:
  import presentation_prepared_check as p
  if mode=='density':
   import runpy
   import presentation_matrix_check as matrix
   source=Path('scripts/presentation_native_density.py').resolve();sys.argv=[str(source),str(build),str(out)];matrix.check=lambda build,out,**kw:p.check(build,out,kw['limit']);runpy.run_path(str(source),run_name='__main__');result=json.loads((out/'check.json').read_text())
  elif mode=='header':
   import presentation_header_reuse_check as h
   result=h.exercise(build,out)
  else:result=p.check(build,out,limit)
finally:subprocess.run=original_run;mm.audit_scene=original_audit_scene
result['native_lanes_auxiliary_ram_code_guarded']=meta['coherent_x']['auxiliary_code']
result['world_x_auxiliary_ram_code_guarded']={'start':0xf400,'length':len(code),'sha256':hashlib.sha256(code).hexdigest()};result['world_x_test_wrapper_sha256']=sha(__file__)
if mode in ('ntsc','pal'):
 from presentation_fixed_clock_probe import CAPTURE_BYTES,active
 raw=(out/'captures.bin').read_bytes();activeidx={i for i in range(len(raw)//CAPTURE_BYTES) if active(raw[i*CAPTURE_BYTES:i*CAPTURE_BYTES+128])}
 costs=[list(map(int,l.split())) for l in (out/'world-costs.tsv').read_text().splitlines()];vals=[v for i,v in costs if i in activeidx]
 if vals:result['world_x_active_world_cycles']={'count':len(vals),'mean':sum(vals)/len(vals),'max':max(vals)}
(out/'check.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k in ['rom_sha256','complete','cases','different_frames','active_pictures_per_second','world_x_active_world_cycles']})
