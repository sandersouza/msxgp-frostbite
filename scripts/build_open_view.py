"""Guarded additive open-edge/credit/palette view on the exact v26 control."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from render_build import symbols
from presentation_open_view import credit_patterns,left_mask
sha=lambda b:hashlib.sha256(b).hexdigest()
PARENT='90d07dc661002f93fbaa7a8e93bcb3e74182abdbcb4838f19406d362d0111512'
def build(base,out):
 base,out=Path(base).resolve(),Path(out).resolve()
 if out.exists():raise ValueError('fresh output required')
 m=json.loads((base/'build.json').read_text());files=dict(m['source_files']);parent=(base/m['rom']['filename']).read_bytes()
 if sha(parent)!=PARENT or len(files)!=215 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('exact AP/v26 closure required')
 out.mkdir(parents=True)
 for p in base.iterdir():
  if p.name=='geometry':(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
  elif p.is_file():shutil.copyfile(p,out/p.name)
  elif p.is_dir():shutil.copytree(p,out/p.name)
 s=symbols(base/'presentation.sym');(out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in s.items()if'.'not in n)+'\n');(out/'credit-patterns.bin').write_bytes(credit_patterns())
 source=ROOT/'src/presentation_open_view.asm'
 run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"open-view.bin"}',f'--sym={out/"open-view.sym"}',f'--lst={out/"open-view.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True);(out/'open-view-assembler.log').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError(run.stdout+run.stderr)
 q=symbols(out/'open-view.sym');code=(out/'open-view.bin').read_bytes();rom=bytearray(parent);patches=[]
 def patch(at,new,expected=None):
  old=bytes(rom[at:at+len(new)])
  if expected is not None and old!=expected:raise ValueError(f'guard differs at{at:x}: {old.hex()}')
  if any(at<r['offset']+r['size']and r['offset']<at+len(new)for r in patches):raise ValueError('overlapping patch')
  rom[at:at+len(new)]=new;patches.append(dict(offset=at,size=len(new),before_sha256=sha(old),after_sha256=sha(new)))
 ins=lambda op,n:bytes((op,n&255,n>>8))
 sections=[('aq_names','aq_names_padded_end',147*16384+0x397e),('aq_unmasked_return','aq_visible_credit_padded_end',0x2610),('aq_player_setup','aq_player_setup_end',115*16384+0x3bac),('aq_boot','aq_boot_end',65*16384+0x3ce7),('aq_eligible','aq_eligible_end',7*16384+s['x_eligible']-0x8000)]
 cursor=0
 for lo,hi,at in sections:
  n=q[hi]-q[lo]
  expected=bytes.fromhex('3a6bf0473a70f0b03eb720023eed3266e8c311b0')if lo=='aq_player_setup'else None
  patch(at,code[cursor:cursor+n],expected);cursor+=n
 if cursor!=len(code)or q['aq_names']!=0xf57e or q['aq_enemy_x']!=0xecb4:raise ValueError('allocation differs')
 patch(147*16384+0x3aa2,ins(0xcd,q['aq_enemy_x']),ins(0xcd,s['normalize_x']))
 # General player fallback gets five planes without disturbing recipe scratch,
 # cache keys C4E4..EA, or the existing color->plane lookup C4F0..FF.
 def scoped(old,new,lo,hi,count):
  hits=[i for i in range(lo,hi-len(old)+1)if parent[i:i+len(old)]==old]
  if len(hits)!=count:raise ValueError(f'operand count differs: {old.hex()} {hits}')
  for at in hits:patch(at,new,old)
 off=lambda pc:2*16384+pc-0x8000
 scoped(bytes.fromhex('1181c4'),bytes.fromhex('1181e7'),off(s['p_player_prepare']),off(s['p_player_prepare']+30),1)
 scoped(bytes.fromhex('015f00'),bytes.fromhex('017700'),off(s['p_player_prepare']),off(s['p_player_prepare']+30),1)
 scoped(bytes.fromhex('2180c4'),bytes.fromhex('2180e7'),115*16384+0x3800+s['x_fallback']-0xe900,115*16384+0x3800+s['x_end']-0xe900,1)
 scoped(bytes.fromhex('fe04'),bytes.fromhex('fe05'),off(s['p_player_store']),off(s['p_player_store.plane']),1)
 scoped(bytes.fromhex('26c4'),bytes.fromhex('26e7'),off(s['p_player_store.byte_origin']),off(s['p_player_bandtop']),1)
 scoped(bytes.fromhex('26c4'),bytes.fromhex('26e7'),off(s['p_player_select']),off(s['p_player_nonempty']),1)
 scoped(bytes.fromhex('21e0c4'),bytes.fromhex('21ebc4'),off(s['p_player_store']),off(s['p_player_cache_lookup']),2)
 patch(0x25d4,b'\0',b'\x3c');patch(102*16384+0x3946,b'\0',b'\x3c')
 bootend=65*16384+s['ah_floe']-0x8000
 patch(bootend-4,ins(0xc3,q['aq_boot']),ins(0xcd,s['t_fill']))
 rows=16384+s['p_bg_rows_data']-0x8000;data=bytearray(parent[rows:rows+288])
 for i in range(0,len(data),3):data[i:i+3]=bytes((128,data[i+2],data[i+2]))
 patch(rows,data)
 bear=114*16384+s['an_background_rows']-0x8000;data=bytearray(parent[bear:bear+36])
 for i in range(0,36,3):data[i:i+3]=bytes((128,data[i+2],data[i+2]))
 patch(bear,data)
 grad=16384+s['p_bg_gradient_data']-0x8000;data=bytearray(parent[grad:grad+32])
 for i in range(0,32,2):data[i]=data[i+1]
 patch(grad,data)
 patch(s['ys_mask']-0x4000,b''.join(left_mask(x).to_bytes(2,'big')for x in range(11)))
 world=bytes(rom[147*16384+0x3800:147*16384+0x3800+1240]);(out/'world.bin').write_bytes(world)
 for section in('coherent_x','native_lanes'):
  for row in m[section]['auxiliary_code']:
   at=row['bank']*16384+row['rom_address']-0x8000;row['sha256']=sha(rom[at:at+row['size']])
 m['world_x']['code_sha256']=sha(world)
 # The header code is an independent boot-copied auxiliary range.
 def refresh(node):
  if isinstance(node,dict):
   if all(k in node for k in('bank','rom_address','ram_address','size','sha256')):
    at=node['bank']*16384+node['rom_address']-0x8000;node['sha256']=sha(rom[at:at+node['size']])
   for value in node.values():refresh(value)
  elif isinstance(node,list):
   for value in node:refresh(value)
 refresh(m)
 n=m['fixed_clock']['ram_code_bytes'];m['fixed_clock']['ram_code_sha256']=sha(rom[115*16384+0x3800:115*16384+0x3800+n])
 for bank in{p['offset']//16384 for p in patches}:
  name=f'assets-{bank:03d}.bin';blob=bytes(rom[bank*16384:(bank+1)*16384])
  for section in('template_assets','static_presentation'):
   if name in m[section]['files']:m[section]['files'][name]=sha(blob);(out/'template-assets'/name).write_bytes(blob)
 for row in m['contact14']['arena']:
  bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
 for p in(Path(__file__),source,ROOT/'scripts/presentation_open_view.py',ROOT/'scripts/presentation_open_view_check.py',ROOT/'tests/test_presentation_open_view.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
 m.update(version='open-view-aq-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Owner-authorized expanded edge/credit/terminal palette and AP cache optimization. Source mechanics/input/audio/clock preserved.'))
 m['open_view']=dict(left=16,credit='Activision - Retroworks',credit_ids=list(range(134,143)),credit_position=[120,184],normal_palette_in_terminal_states=True,hidden_enemy_x=0,parent_rom_sha256=PARENT,patches=patches,new_ram_bytes=0,new_vram_bytes=0)
 s.update({n:v for n,v in q.items()if n.startswith('aq_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n')
 name='frostbite-open-view-aq.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),patches=len(patches)));return m
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.base,a.out)
