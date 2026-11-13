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
