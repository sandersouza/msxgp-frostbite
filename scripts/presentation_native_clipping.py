"""Exhaustive independent original-glyph to actual SGT/mask finite proof."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'scripts')
from original_graphics import view
from graphics_mapping import map_x
from render_build import symbols
here=Path(__file__).resolve().parent
build=Path(sys.argv[1]).resolve();report_path=Path(sys.argv[2]).resolve();assert not report_path.exists()
meta=json.loads((build/'build.json').read_text());rom=(build/meta['rom']['filename']).read_bytes();original=Path('references/roms/frostbite.bin').read_bytes();s=symbols(build/'presentation.sym')
sha=lambda value:hashlib.sha256(value).hexdigest()
assert sha(rom)==meta['rom']['sha256'] and sha(original)==meta['profile']['source_sha256']
mapping=rom[16384+(s['p_geo_row_map_data']&16383):16384+(s['p_geo_row_map_data']&16383)+256]
selectors={g:[k for k,v in enumerate(mapping) if v==g] for g in range(33)}
assert all(selectors.values())
cases=edge_cases=0;actual_digest=hashlib.sha256();expected_digest=hashlib.sha256()
for group,roots in selectors.items():
 for reflection in (False,True):
  glyph=view(original,0xFD00+roots[0],8,reflection)['pixels']
  assert all(view(original,0xFD00+selector,8,reflection)['pixels']==glyph for selector in roots)
  for x in range(160):
   native_group=group*2+int(reflection);entry=(native_group*2+(x&1))*32
   pattern=bytearray(rom[255*16384+0x1400+entry:255*16384+0x1400+entry+32])
   assert len(pattern)==32
   if x==0:pattern=bytearray(32) # proven mode0 wholly hidden shortcut
   elif x<8 or x>=153:
    table=s['x_left_masks' if x<8 else 'x_right_masks'];at=7*16384+(table&16383)+(x&7)*2
    high,low=rom[at:at+2]
    for y in range(8):pattern[y]&=high;pattern[16+y]&=low
   actual=bytearray(256*16);expected=bytearray(256*16);anchor=8+3*(x//2)
   for y in range(16):
    word=pattern[y]*256+pattern[16+y]
    for bit in range(16):
     if word&(0x8000>>bit):
      assert 0<=anchor+bit<256
      actual[y*256+anchor+bit]=1
   for y in range(8):
    for bit in range(8):
     sx=(x+bit)%160
     if glyph[y*8+bit] and sx>=8:
      for px in range(map_x(sx),map_x(sx+1)):expected[y*256+px]=1
   assert actual==expected,(group,reflection,x,[(i%256,i//256,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b][:20])
   actual_digest.update(actual);expected_digest.update(expected);cases+=1;edge_cases+=int(x<8 or x>=153)
report=dict(complete=True,rom_sha256=sha(rom),original_sha256=sha(original),cases=cases,edge_cases=edge_cases,groups=33,reflections=2,x=list(range(160)),pool_patterns=132,selector_aliases=sum(map(len,selectors.values())),actual_pixels_sha256=actual_digest.hexdigest(),expected_pixels_sha256=expected_digest.hexdigest(),scope='All original glyphs/reflections and mode0 X0..159, sixteen complete SGT rows, source160 wrap and HMOVE X<8 clip. Actual ROM pool/mask tables; independent original ROM glyph expansion and map_x. No runtime timing or owner acceptance claim.',sources={str(p):sha(p.read_bytes()) for p in (Path(__file__),Path('scripts/original_graphics.py'),Path('scripts/graphics_mapping.py'))})
report_path.write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('x','sources')})
