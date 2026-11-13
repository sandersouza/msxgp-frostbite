import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from presentation_player_bands import pack_recipe,cache_delta

def pat(rows):
 b=bytearray(32)
 for y,value in rows.items():b[y]=value>>8;b[y+16]=value&255
 return bytes(b)

def pixels(entries):
 r={}
 for top,color,p in entries:
  for y in range(16):
   mask=p[y]*256+p[y+16]
   for x in range(16):
    if mask&(32768>>x):r.setdefault((top+y,x),color)
 return r

class PlayerBandsTests(unittest.TestCase):
 def test_three_color_rectangles_keep_pixels_and_reduce_scanline_occupancy(self):
  old=[(0,10,pat({14:0xff00,15:0xff00})),(16,10,pat({0:0xff00})),(16,11,pat({1:0x0f00,10:0x0f00})),(16,14,pat({2:0xff00,3:0xff00,4:0xff00}))]
  result=pack_recipe(old,16);new=result['entries']
  self.assertTrue(result['packed']);self.assertEqual(len(new),3);self.assertEqual(pixels(old),pixels(new));self.assertEqual(result['cut'],max(y for y,c,p in new))
  self.assertLessEqual(max(sum(y<=line<y+16 for y,c,p in new)for line in range(-16,64)),2)
 def test_long_color_span_and_overlapping_color_pixels_retain_original_layout(self):
  for old in([ (0,10,pat({0:1})),(16,10,pat({3:1})) ],[(0,10,pat({1:1})),(0,11,pat({1:1}))]):
   result=pack_recipe(old,16);self.assertFalse(result['packed']);self.assertEqual(result['entries'],old);self.assertEqual(result['cut'],16)
 def test_cache_translation_is_bounded_and_rejects_foreign_large_frames(self):
  self.assertEqual(cache_delta(3,55,35),236);self.assertEqual(cache_delta(3,55,55),0)
  self.assertEqual(cache_delta(6,55,39),240);self.assertEqual(cache_delta(4,55,55),0);self.assertEqual(cache_delta(3,128,0),128)
  for args in((3,55,56),(4,55,35),(6,55,40),(0,55,55),(7,55,55),(True,55,55),(3,129,0)):
   with self.assertRaises(ValueError):cache_delta(*args)

if __name__=='__main__':unittest.main()
