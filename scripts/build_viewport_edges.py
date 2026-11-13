"""Apply the two viewport edge repairs to the exact sealed v27 ROM."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from render_build import symbols
from presentation_viewport_edges import compile_standing_edges
sha=lambda b:hashlib.sha256(b).hexdigest()
PARENT='78090dde8429a5bc6097e02cfaf278539e05ff68b9582d65e16d430d04334c8a'
def build(base,out):
 base,out=Path(base).resolve(),Path(out).resolve()
 if out.exists():raise ValueError('Fresh output required')
 m=json.loads((base/'build.json').read_text());files=dict(m['source_files']);parent=(base/m['rom']['filename']).read_bytes()
 if sha(parent)!=PARENT or len(files)!=220 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('Exact sealed v27 source closure required')
 out.mkdir(parents=True)
 for p in base.iterdir():
  if p.name=='geometry':(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
  elif p.is_file():shutil.copyfile(p,out/p.name)
  elif p.is_dir():shutil.copytree(p,out/p.name)
 s=symbols(base/'presentation.sym');(out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in s.items()if'.'not in n)+'\n')
 source=ROOT/'src/presentation_viewport_edges.asm'
 run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"viewport-edges.bin"}',f'--sym={out/"viewport-edges.sym"}',str(source)],cwd=ROOT,capture_output=True,text=True);(out/'viewport-edges-assembler.log').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError(run.stdout+run.stderr)
 q=symbols(out/'viewport-edges.sym');code=(out/'viewport-edges.bin').read_bytes();rom=bytearray(parent);patches=[]
 ins=lambda op,n:bytes((op,n&255,n>>8))
 def patch(at,data,expected):
  if bytes(rom[at:at+len(data)])!=expected:raise ValueError(f'Guard differs at {at:x}')
  if any(at<r['offset']+r['size']and r['offset']<at+len(data)for r in patches):raise ValueError('Patch overlap')
  rom[at:at+len(data)]=data;patches.append(dict(offset=at,size=len(data),before_sha256=sha(expected),after_sha256=sha(data)))
 def unique(needle,lo,hi):
  if parent.count(needle,lo,hi)!=1:raise ValueError(f'Unique hook required: {needle.hex()}')
  return parent.index(needle,lo,hi)
 if q['ar_pattern']!=0xecc0 or q['ar_padded_end']!=0xed00 or len(code)!=64:raise ValueError('Alignment padding allocation differs')
 patch(115*16384+0x3bc0,code,bytes(64))
 # The caller is bank2; the RAM wrapper leaves that bank selected.
 at=unique(ins(0xcd,s['p_player_sprite_pattern']),s['p_player_emit_all'],s['p_player_sprite_pattern'])
 patch(at,ins(0xcd,q['ar_pattern']),ins(0xcd,s['p_player_sprite_pattern']))
 needle=bytes((0x3e,8))+ins(0xcd,s['p_player_zone'])
 at=unique(needle,s['p_player_init_masks'],s['p_player_zone'])
 patch(at+1,bytes((5,)),bytes((8,)))
 # Keep the prepared path fast while distinguishing every new partial mask.
 if parent[0xb253:0xb259]!=bytes.fromhex('3a66f0fe54d8'):raise ValueError('Inherited cache entry differs')
 at=s['p_player_cache_lookup.horizontal_key'];patch(at,ins(0xcd,q['ar_edge_key']),ins(0x32,s['p_pc_key']+5))
 palette=parent[115*16384+0x3c00:115*16384+0x3d00]
 original=(ROOT/'references/roms/frostbite.bin').read_bytes()
 if sha(original)!=m['profile']['source_sha256']:raise ValueError('Original identity differs')
 directory,records,patterns,finite=compile_standing_edges(original,palette)
 for first,count,data in((120,1,directory),(121,2,records),(123,4,patterns)):
  if len(data)>count*2048:raise ValueError('Prepared shore capacity exceeded')
  data=data.ljust(count*2048,b'\xff')
  for i in range(count):
   at=(first+i)*16384+0x3800;patch(at,data[i*2048:(i+1)*2048],parent[at:at+2048])
 (out/'viewport-shore-finite.json').write_text(json.dumps(finite,indent=2)+'\n')
 # Stop this enemy glyph at column31; the next copy still normalizes normally.
 at=147*16384+0x3800+s['x_actor.nextcell']+7-0xf400
 expected=bytes((0x16,1))+ins(0x2a,s['qe_rowbase'])+bytes((0x23,0x18,1))
 patch(at,ins(0xc3,s['x_actor.nextrow'])+bytes(5),expected)
 def refresh(node):
  if isinstance(node,dict):
   if all(k in node for k in('bank','rom_address','ram_address','size','sha256')):
    at=node['bank']*16384+node['rom_address']-0x8000;node['sha256']=sha(rom[at:at+node['size']])
   for v in node.values():refresh(v)
  elif isinstance(node,list):
   for v in node:refresh(v)
 refresh(m)
 n=m['fixed_clock']['ram_code_bytes'];m['fixed_clock']['ram_code_sha256']=sha(rom[115*16384+0x3800:115*16384+0x3800+n])
 world=bytes(rom[147*16384+0x3800:147*16384+0x3800+1240]);(out/'world.bin').write_bytes(world);m['world_x']['code_sha256']=sha(world)
 for bank in{p['offset']//16384 for p in patches}:
  name=f'assets-{bank:03d}.bin';blob=bytes(rom[bank*16384:(bank+1)*16384])
  for section in('template_assets','static_presentation'):
   if name in m[section]['files']:m[section]['files'][name]=sha(blob);(out/'template-assets'/name).write_bytes(blob)
 for row in m['contact14']['arena']:
  bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
 for p in(Path(__file__),source,ROOT/'scripts/presentation_viewport_edges.py',ROOT/'scripts/presentation_viewport_edges_check.py',ROOT/'tests/test_presentation_viewport_edges.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
 m.update(version='viewport-edges-ar-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Player X16 clipping and no enemy glyph overflow wrap. Source mechanics/coordinates/input/clock/PSG unchanged.'))
 m['viewport_edges']=dict(parent_rom_sha256=PARENT,patches=patches,player_left_target=16,player_source_cut=5,partial_source_pixel_clipped_exactly=True,enemy_glyph_wrap=False,partial_cache_key_range=[160,167],prepared_shore=finite,occupied_alignment_padding_bytes=q['ar_end']-q['ar_pattern'],new_ram_bytes=0,new_vram_bytes=0)
 s.update({n:v for n,v in q.items()if n.startswith('ar_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n')
 name='frostbite-viewport-edges-ar.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),patches=len(patches)));return m
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.base,a.out)
