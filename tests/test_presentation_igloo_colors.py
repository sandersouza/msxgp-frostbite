"""Color-only publication may never preserve a changed physical pattern."""
import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from presentation_constructors import construct,igloo_key

class IglooColorTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_igloo_colors'),
            'igloo color-only certificate/generator missing')
        return __import__('presentation_igloo_colors')

    def backgrounds(self):
        return {128+i:bytes([255])*8+bytes([17*((i%13)+1)])*8 for i in range(27)}

    def test_color_change_reuses_only_identical_valid_igloo_masks(self):
        a=self.api();b=self.backgrounds();old=igloo_key(252,3,128);new=igloo_key(252,3,129)
        self.assertTrue(a.can_reuse_pattern(old,new,b))
        for bad in (bytes([255])*6,igloo_key(240,3,128),igloo_key(252,0,128),old[:5]+b'\x06',old[:3]+b'\x0f'+old[4:]):
            self.assertFalse(a.can_reuse_pattern(bad,new,b))

    def test_edges_and_gray_background_cannot_reuse_uniform_pattern_certificate(self):
        a=self.api();b=self.backgrounds()
        for tile in (bytes([15])*8+bytes([65])*8,bytes([255])*8+bytes([238])*8,
                     bytes([255])*8+bytes([65])*8):
            b[128]=tile
            self.assertFalse(a.uniform_background(tile))
            self.assertFalse(a.can_reuse_pattern(igloo_key(1,2,128),igloo_key(1,2,129),b))
            self.assertFalse(a.can_reuse_pattern(igloo_key(1,2,129),igloo_key(1,2,128),b))

    def test_precomputed_colors_equal_independent_constructor_for_zero_and_nonzero_halves(self):
        a=self.api();b=self.backgrounds();flags,records=a.compile_colors(b)
        self.assertEqual(len(flags),32);self.assertEqual(len(records),27*32)
        self.assertEqual(flags[:27],bytes([1])*27)
        for identifier in range(128,155):
            for top in (0,3,63,252,255):
                for bottom in (0,3,63,252,255):
                    key=igloo_key(top,bottom,identifier)
                    expected=construct(key,patterns=[],backgrounds=b,header=b'',footer=[])
                    mode=bool(top)+2*bool(bottom);offset=(identifier-128)*32+mode*8
                    self.assertEqual(records[offset:offset+8],expected[8:])
                    # Reusing an equal mask over another certified color keeps PGT exact.
                    other=construct(igloo_key(top,bottom,128),patterns=[],backgrounds=b,header=b'',footer=[])
                    self.assertEqual(other[:8],expected[:8])
        self.assertEqual(records[:8],bytes([17])*8)
        self.assertEqual(records[8:16],bytes([225])*4+bytes([17])*4)

    def test_complete_background_domain_and_whole_keys_required(self):
        a=self.api();b=self.backgrounds()
        with self.assertRaises(ValueError):a.compile_colors({128:b[128]})
        with self.assertRaises(ValueError):a.uniform_background(bytes(15))
        with self.assertRaises(ValueError):a.can_reuse_pattern(bytes(5),bytes(6),b)

if __name__=='__main__':unittest.main()
