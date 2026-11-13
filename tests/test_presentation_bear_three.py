import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from presentation_bear_three import triple,full_admissible
from presentation_bear_hybrid import sprite_prefix
from presentation_bear_three_check import freeze_active_extra

class BearThreeTests(unittest.TestCase):
 def test_third_pattern_keeps_exact_prefix_and_moves_only_empty_rows(self):
  pixels=bytearray(320);pixels[1]=1;pixels[4*16+12]=1;pixels[15*16+15]=1
  record=triple(pixels);self.assertEqual(record['dy'],0);self.assertEqual(record['patterns'][:64],sprite_prefix(pixels));self.assertEqual(len(record['patterns']),96)
  self.assertEqual(record['patterns'][64+4],32);self.assertEqual(record['patterns'][64+15],3);self.assertEqual(record['patterns'][80:],bytes(16))
 def test_overheight_thin_strip_and_bad_inputs_are_rejected(self):
  p=bytearray(320);p[12]=1;p[19*16+12]=1
  with self.assertRaises(ValueError):triple(p)
  with self.assertRaises(ValueError):triple(bytes(319))
 def test_thin_start_is_a_required_critical_scanline(self):
  self.assertFalse(full_admissible([45]*3,51,0));self.assertTrue(full_admissible([45]*2,51,0))
  self.assertTrue(full_admissible([35,51,51],51,0));self.assertFalse(full_admissible([35,51,51,51],51,0))
 def test_capacity_counts_all_sprites_even_outside_bear_span(self):
  self.assertTrue(full_admissible([100+i%4*20 for i in range(28)],51,0))
  self.assertFalse(full_admissible([100]*29,51,0))
  self.assertFalse(full_admissible([255]*3,0,-2))


 def test_active_extra_pattern_is_frozen_even_when_not_in_sat(self):
  before=bytearray(16384);before[0x1b00]=208
  for page in range(2):
   registers=bytes((0,0,6+page,0,0,0,0,0));changed=bytearray(before);changed[0x3800+(58+page)*32]=1
   with self.assertRaises(ValueError):freeze_active_extra(before,changed,registers)
   inactive=bytearray(before);inactive[0x3800+(59-page)*32]=1;freeze_active_extra(before,inactive,registers)

if __name__=='__main__':unittest.main()
