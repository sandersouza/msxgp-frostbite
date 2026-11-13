"""Exact viewport clipping: source movement and positions are never changed."""
from copy import deepcopy
from presentation_open_view import expected_frame as parent,credit_pixels

def expected_frame(meta,original,description,ram,raw,palette):
 from presentation_model import pixels
 from presentation_grid24 import anchor,player_delta
 from presentation_player_palette import player_color
 from graphics_mapping import map_x,map_y,palette_map
 if not meta.get('viewport_edges'):return parent(meta,original,description,ram,raw,palette)
 base=deepcopy(description);base['objects']=[]
 for r in base['player']['rows']:r['pattern']=r['prefix_pattern']=0
 result=bytearray(parent(meta,original,base,ram,raw,palette))
 if description['hud']['blanked']:return bytes(result)
 colors=palette_map(palette)
 def paint(x,y,color,clip=True):
  if not 0<=x<160 or y is None or not 0<=y<192:return
  for tx in range(map_x(x),map_x(x+1)):
   if not clip or 16<=tx<248:result[y*256+tx]=color
 from original_graphics import view
 for obj in description['objects']:
  if obj['x']==0:continue
  image=view(original,obj['address'],8,obj['reflect'])
  for i,bit in enumerate(image['pixels']):
   if bit:paint(obj['x']+i%8,anchor('enemy',obj['row'])+i//8,colors[obj['color']])
 delta=player_delta(ram[100],description['coarse_shift'])
 if description['player']['x']>=8:
  tagged=deepcopy(description)
  for r in tagged['player']['rows']:
   for k in('color','prefix_color','suffix_color'):r[k]|=1
  for at,code in enumerate(pixels(original,tagged)):
   if not code&1:continue
   sy,x=divmod(at,160);y=map_y(sy)
   paint(x,None if y is None else y+delta,player_color(code&254,colors[code&254]),False)
 else:
  person=description['player'];coarse=description['coarse_shift']
  for r in person['rows']:
   for dx in range(8):
    x=person['x']+dx;bit=dx if person['reflect']else 7-dx
    pattern=r['prefix_pattern']if x<r['update_x']else r['pattern']
    code=r['prefix_color']if x<r['color_update_x']else r['color']
    if x>=r['suffix_x']:code=r['suffix_color']
    if pattern&(1<<bit):
     y=map_y(r['y']+int(coarse and r['y']>=57))
     paint(x,None if y is None else y+delta,player_color(code,colors[code]))
    if coarse and r['y']==56 and r['pattern']&(1<<bit):
     paint(x,map_y(57)+delta,player_color(r['color'],colors[r['color']]))
 for i,bit in enumerate(credit_pixels()):
  if bit:result[(184+i//72)*256+120+i%72]=15
 return bytes(result)
