"""Full-density renderer cases derived from a verified original source state."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'scripts')
import presentation_matrix_check as matrix
from presentation_model import describe,pixels
from render_build import symbols
p=Path(__file__).parent;build=Path(sys.argv[1]);out=Path(sys.argv[2]);rom=Path('references/roms/frostbite.bin').read_bytes()
control=Path('outputs/presentation/header-palette-w/ntsc-clean')
receipt=json.loads((control/'check.json').read_text())
assert receipt['rom_sha256']=='98904b6bb592f78964158d154545764eda0e986c9c979196d60e9a7ed03f30b4'
assert receipt['source_cpu_all_ram_equal'] and receipt['coherent_picture_pixels_equal']
raw=(control/'captures.bin').read_bytes();assert hashlib.sha256(raw).hexdigest()==receipt['artifacts']['captures.bin']
base=next(raw[i:i+128] for i in range(0,len(raw),49304) if raw[i+0x64]==27 and all(raw[i+k]==0 for k in (0x46,0x67,0x71)))
meta=json.loads((build/'build.json').read_text());s=symbols(build/'presentation.sym');r=(build/meta['rom']['filename']).read_bytes();assert hashlib.sha256(r).hexdigest()==meta['rom']['sha256']
at=16384+(s['p_geo_row_map_data']&16383);inv={}
for k,g in enumerate(r[at:at+256]):
 if g<33:inv.setdefault(g,k)
assert len(inv)==33
xs=[0,1,7,8,15,16,31,32,143,144,151,152,153,159];specs=[]
for group in range(33):
 for reflection in (0,128):
  for coarse in (0,1):
   for mode in range(4):specs.append((group,reflection,coarse,mode,xs[(group+reflection//128+mode)%len(xs)]))
for x in xs:
 for mode in range(4):
  for coarse in (0,1):specs.append((1+x%32,128 if x&1 else 0,coarse,mode,x))
cases=[]
for j,(group,reflection,coarse,mode,x) in enumerate(specs):
 ram=bytearray(base);ram[0x68]=150 if coarse else 0
 for lane in range(4):
  ram[0x23+lane]=inv[(group+lane)%33];ram[0x11+lane]=reflection;ram[0x54+lane]=(x+lane*16)%160;ram[0x58+lane]=mode
 ram=bytes(ram);sample={'ram':ram,'name':f'derived-{j}-g{group}-r{reflection}-c{coarse}-m{mode}-x{x}','family':'derived-density'}
 sample['raster']=pixels(rom,describe(rom,sample))
 for repeat in range(3):cases.append({**sample,'name':sample['name']+f'-repeat{repeat}'})
assert len(cases)==1920
casehash=hashlib.sha256(b''.join(c['ram'] for c in cases)).hexdigest()
bundle={'cases':cases,'files':{},'families':{'derived-density':len(cases)},'unmapped_startup':0,'source_receipt_sha256':casehash};matrix.collect_source=lambda:bundle
report=matrix.check(build,out,all_source=True,limit=len(cases),explore=True)
report['domain']='derived full-density coordinates/copy modes from one original-route state';report['scope']+='; synthetic full-scene actor density/boundaries/cache repeats, NOT original observed high-level gameplay or native source timing.'
report['derivation']={'unique_states':len(specs),'copies_modes':[0,1,2,3],'groups':33,'reflections':[0,128],'coarse':[0,1],'xs':xs,'repeats':3,'base_ram':base.hex(),'base_ram_sha256':hashlib.sha256(base).hexdigest(),'source_capture_sha256':hashlib.sha256(raw).hexdigest(),'cases_sha256':casehash}
(out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print({k:report[k] for k in ('complete','cases','different_frames')})
