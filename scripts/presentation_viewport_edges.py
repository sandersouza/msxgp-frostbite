"""Exact viewport clipping: source movement and positions are never changed."""
from copy import deepcopy
from presentation_open_view import expected_frame as parent,credit_pixels

def edge_key(x,original):
 return 160+x if x<8 else original

def compile_standing_edges(rom,palette):
 """Finite sourceY27 packets; exact LEFT16 raster, including half source pixels."""
 from itertools import product
 from presentation_model import player
 from presentation_sprites import expand_pair
 from presentation_shore_recipes import pack_record
 if len(rom)!=4096 or len(palette)!=256:raise ValueError('Complete source and palette required')
 pool=[];records=[];directory=[];checks=0;maximum=0
 for x,pose,reflect,coarse in product(range(24),range(6),range(2),range(2)):
  ram=[0]*128;ram[0x64]=27;ram[0x66]=x;ram[0x6e]=pose;ram[0x6c]=reflect*8
  planes={};wanted={}
  def point(y,dx,color):
   planes.setdefault(color,{})[y]=planes.get(color,{}).get(y,0)|(128>>dx)
   for tx in range(8+(x+dx)*3//2,8+(x+dx+1)*3//2):
    if tx>=16:wanted[y,tx-(8+x*3//2)]=color
  for row in player(rom,ram)['rows']:
   for dx in range(8):
    pos=x+dx;bit=dx if reflect else 7-dx
    pattern=row['prefix_pattern']if pos<row['update_x']else row['pattern']
    color=row['prefix_color']if pos<row['color_update_x']else row['color']
    if pos>=row['suffix_x']:color=row['suffix_color']
    if pos>=5 and pattern&(1<<bit):point(row['y']-7+int(coarse and row['y']>=57),dx,palette[color])
    if coarse and row['y']==56 and row['pattern']&(1<<bit):point(50,dx,palette[row['color']])
  entries=[];cut=27+coarse
  if wanted:
   top=min(y for y,tx in wanted);bottom=max(y for y,tx in wanted)
   cut=next(q for q in range(bottom-15,top+17)if all(sum(any(mask for y,mask in p.items()if bt<=y<bt+16)for p in planes.values())<=3 for bt in(q-16,q)))
   mask=65535>>max(0,16-(8+x*3//2))
   for bt in(cut-16,cut):
    for color,p in planes.items():
     pat=bytearray(32)
     for dy in range(16):
      a,b=expand_pair(p.get(bt+dy,0),x&1);pat[dy]=a&(mask>>8);pat[dy+16]=b&(mask&255)
     if any(pat):
      pat=bytes(pat)
      if pat not in pool:pool.append(pat)
      entries.append((bt-27-coarse,color,pool.index(pat)))
  actual={}
  for dy,color,pid in entries:
   for y in range(16):
    for tx in range(16):
     if pool[pid][tx//8*16+y]&(128>>(tx%8)):actual[27+coarse+dy+y,tx]=color
  if actual!=wanted:raise ValueError(('Prepared edge pixels differ',x,pose,reflect,coarse))
  record=pack_record(cut-27-coarse,entries)
  if record not in records:records.append(record)
  directory.append(records.index(record));maximum=max(maximum,len(entries));checks+=1
 if len(pool)>256 or len(records)>256:raise ValueError('Existing shore reservation exceeded')
 return b''.join(i.to_bytes(2,'little')for i in directory),b''.join(records),b''.join(pool),dict(finite_cases=checks,records=len(records),patterns=len(pool),max_entries=maximum,decoded_pixels_exact=True)

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
