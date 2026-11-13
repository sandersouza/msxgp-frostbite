"""Source-derived open-edge compositor and independently audited static credit."""
from copy import deepcopy
LEFT=16
TEXT='- Retroworks'
FONT={
'-':(0,0,0,31,0,0,0),' ':(0,)*7,
'R':(30,17,17,30,20,18,17),'e':(0,0,14,17,31,16,14),
't':(4,4,31,4,4,4,3),'r':(0,0,22,25,16,16,16),
'o':(0,0,14,17,17,17,14),'w':(0,0,17,17,21,21,10),
'k':(16,16,18,20,24,20,18),'s':(0,0,15,16,14,1,30)}
def credit_pixels():return bytes((FONT[c][y]>>(4-x))&1 if x<5 else 0 for y in range(7)for c in TEXT for x in range(6))
def credit_patterns():
 p=credit_pixels();return bytes(sum((p[y*72+t*8+x]if y<7 else 0)<<(7-x)for x in range(8))for t in range(9)for y in range(8))
def left_mask(x):
 if type(x)is not int or x not in range(11):raise ValueError('source X0..10 required')
 return(1<<min(16,max(0,16-(LEFT-(8+3*(x//2))))))-1

def audit_credit(vram):
 if len(vram)!=16384:raise ValueError('complete VRAM required')
 patterns=credit_patterns()
 for i in range(9):
  at=4096+(134+i)*8
  if vram[at:at+8]!=patterns[i*8:i*8+8]or vram[8192+at:8192+at+8]!=bytes((241,))*8:raise ValueError('immutable Retroworks tile differs')
def shadow_credit(raw,vram):
 audit_credit(vram)
 if len(raw)!=4110:raise ValueError('complete owner snapshot required')
 names=bytearray(raw);video=bytearray(vram)
 for pos,identifier in enumerate(raw[:1536]):
  page,cell=divmod(pos,768);row,col=divmod(cell,32)
  if row<16 or not 134<=identifier<=142:continue
  if row!=23 or not 15<=col<=23 or identifier!=134+col-15:raise ValueError('credit outside exact suffix position')
  at=6144+page*1024+cell
  if video[at]!=identifier:raise ValueError('credit physical NAME differs')
  names[pos]=video[at]=128
 return bytes(names),bytes(video)

def expected_frame(meta,original,description,ram,raw,palette):
 from graphics_mapping import map_frame,map_x,map_y,palette_map
 from original_graphics import view
 from presentation_grid24 import anchor,player_delta
 from presentation_model import pixels
 from presentation_player_palette import player_color
 if meta.get('open_view',{}).get('left')!=LEFT:raise ValueError('declared open view required')
 if description['hud']['blanked']:return bytes((1,))*49152
 colors=palette_map(palette);source=bytearray(33600)
 for y,color in enumerate(description['background']):source[y*160+8:(y+1)*160]=bytes((color,))*152
 def point(x,y,c):
  x%=160
  if 8<=x<160 and 0<=y<210:source[y*160+x]=c
 def draw(c):
  image=view(original,c['address'],c['height'],c.get('reflect',False),c.get('scale',1))
  for i,bit in enumerate(image['pixels']):
   if bit:point(c['x']+i%image['width'],c['y']+i//image['width'],c['color'])
 def solid(c):
  for dy in range(c['height']):
   for dx in range(c['width']):point(c['x']+dx,c['y']+dy,c['color'])
 for c in description['hud']['score']+description['hud']['status']:draw(c)
 for c in description['igloo']:solid(c)
 for c in description['door']:draw(c)
 if description['coarse_shift']:source[57*160:]=source[56*160:209*160]
 footer=description['footer']
 for c in footer['prefix']:draw(c)
 for c in footer['playfield']+footer['ball']:solid(c)
 for c in footer['logo']:draw(c)
 result=bytearray(map_frame(bytes(source),palette))
 for y in range(192):result[y*256:y*256+16]=bytes((1,))*16;result[y*256+16:y*256+20]=bytes((result[y*256+20],))*4
 def put(x,y,c):
  x%=160
  if not 0<=y<192:return
  for tx in range(map_x(x),map_x(x+1)):
   if LEFT<=tx<248:result[y*256+tx]=c
 bear=description['bear'];image=view(original,bear['address'],19,bear['reflect'],2)['pixels'];image+=image[-16:]
 for i,bit in enumerate(image):
  if bit:put(bear['x']+i%16,51+description['coarse_shift']+i//16,colors[bear['color']])
 for obj in description['objects']:
  if obj['x']==0:continue
  image=view(original,obj['address'],8,obj['reflect'])
  for i,bit in enumerate(image['pixels']):
   if bit:put(obj['x']+i%8,anchor('enemy',obj['row'])+i//8,colors[obj['color']])
 for c in description['floes']:
  y=anchor('floe',c['row'])+c['y']-(174-26*c['row'])
  for dx in range(c['width']):put(c['x']+dx,y,colors[c['color']])
 tagged=deepcopy(description)
 for r in tagged['player']['rows']:
  for key in('color','prefix_color','suffix_color'):r[key]|=1
 image=pixels(original,tagged);delta=player_delta(ram[100],description['coarse_shift'])
 for at,code in enumerate(image):
  if not code&1:continue
  sy,x=divmod(at,160);y=map_y(sy)
  if y is None or not 0<=y+delta<192:continue
  color=player_color(code&254,colors[code&254]);first=(y+delta)*256+map_x(x);width=map_x(x+1)-map_x(x)
  result[first:first+width]=bytes((color,))*width
 for i,bit in enumerate(credit_pixels()):
  if bit:result[(184+i//72)*256+120+i%72]=15
 return bytes(result)
