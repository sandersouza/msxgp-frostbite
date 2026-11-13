"""Owner-requested edge, credit and terminal palette invariants."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from presentation_open_view import credit_patterns,credit_pixels,left_mask,shadow_credit
class OpenView(unittest.TestCase):
 def test_credit_exact_footprint(self):
  p=credit_patterns();self.assertEqual(len(p),72);self.assertTrue(any(p));self.assertEqual(len(credit_pixels()),504)
  self.assertEqual(p[:8],bytes((0,0,0,248,0,0,0,0)))
 def test_full_first_world_tile(self):
  self.assertEqual(left_mask(0),255);self.assertEqual(left_mask(6),65535);self.assertEqual(left_mask(10),65535)
 def test_credit_shadow_is_narrow_and_physical(self):
  raw=bytearray(4110);vram=bytearray(16384)
  for i,p in enumerate(credit_patterns()[j:j+8]for j in range(0,72,8)):
   at=4096+(134+i)*8;vram[at:at+8]=p;vram[8192+at:8192+at+8]=bytes((241,))*8
  at=23*32+15;raw[at]=134;vram[6144+at]=134
  a,b=shadow_credit(raw,vram);self.assertEqual(a[at],128);self.assertEqual(b[6144+at],128)
  raw[at-1]=134
  with self.assertRaises(ValueError):shadow_credit(raw,vram)
if __name__=='__main__':unittest.main()
