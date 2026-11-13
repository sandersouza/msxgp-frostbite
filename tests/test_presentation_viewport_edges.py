"""Regressions for the expanded viewport, independent of original ROM assets."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
 from presentation_viewport_edges import expected_frame
except ModuleNotFoundError:
 from presentation_open_view import expected_frame
from presentation_model import describe,pixels
from presentation_grid24 import anchor,player_delta
from graphics_mapping import map_y,TMS_RGB

class ViewportEdges(unittest.TestCase):
 def test_partial_edge_cache_keys_cannot_alias_old_clip_masks(self):
  from presentation_viewport_edges import edge_key
  keys={edge_key(x,255)for x in range(8)}
  self.assertEqual(len(keys),8)
  self.assertFalse(keys&set(range(24)))
  self.assertFalse(keys&{0,1,3,7,15,31,63,127,128,192,224,240,248,252,254,255})
  for x in range(8,160):self.assertEqual(edge_key(x,255),255)
 def test_prepared_edge_packets_decode_exactly(self):
  from presentation_viewport_edges import compile_standing_edges
  rom=bytearray(4096);rom[0xc00:0xc13]=bytes((255,))*19
  rom[0xc20:0xc33]=bytes((0x24,))*19;rom[0xcb0:0xcb6]=bytes((32,))*6
  palette=bytearray(256);palette[0x24]=10
  directory,records,patterns,proof=compile_standing_edges(bytes(rom),palette)
  self.assertEqual(len(directory),1152);self.assertEqual(proof['finite_cases'],576)
  self.assertLessEqual(len(records),4096);self.assertLessEqual(len(patterns),8192)
 def scene(self):
  rom=bytearray(4096);rom[0xd00:0xd08]=bytes((255,))*8
  ram=[0]*128;ram[0x64]=64
  d=describe(bytes(rom),{'ram':ram});d['objects']=[];d['floes']=[]
  for r in d['player']['rows']:r['pattern']=r['prefix_pattern']=0
  palette={c:(0,0,0)for c in range(256)}
  palette.update({6:(142,142,142),10:(192,192,192),12:(255,255,255),144:TMS_RGB[4]})
  return bytes(rom),ram,d,palette
 def image(self,rom,ram,d,palette):
  return expected_frame({'open_view':{'left':16},'viewport_edges':True},rom,d,ram,pixels(rom,d),palette)
 def test_right_enemy_never_leaks_into_left_edge(self):
  rom,ram,d,palette=self.scene()
  d['objects']=[dict(row=0,x=159,y=160,width=8,height=8,address=0xfd00,reflect=False,color=12)]
  image=self.image(rom,ram,d,palette);y=anchor('enemy',0)
  self.assertEqual(image[y*256+16:y*256+24],bytes((4,))*8)
  self.assertEqual(image[y*256+246:y*256+248],bytes((15,))*2)
 def test_player_is_visible_through_exact_expanded_left_edge(self):
  rom,ram,d,palette=self.scene();d['player']['x']=0;ram[0x66]=0
  r=next(r for r in d['player']['rows']if r['y']==100)
  r.update(pattern=255,prefix_pattern=255,color=0x24,prefix_color=0x24,suffix_color=0x24)
  image=self.image(rom,ram,d,palette);y=map_y(100)+player_delta(ram[0x64],0)
  self.assertEqual(image[y*256+16:y*256+20],bytes((10,))*4)
  self.assertEqual(image[y*256:y*256+16],bytes((1,))*16)
if __name__=='__main__':unittest.main()
