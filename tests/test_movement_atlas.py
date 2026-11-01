from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import render_model as model
from movement_atlas import compile_atlas


class MovementAtlasTests(unittest.TestCase):
    def test_every_lookup_variant_wraps_clips_and_preserves_independent_mask_pixels(self):
        atlas=compile_atlas()
        self.assertLessEqual(atlas['ordinary_tiles'],248)
        self.assertLessEqual(atlas['colored_tiles'][0],256)
        self.assertEqual(len(atlas['rows']),34*160*32)
        for index,(kind,color,count,gap,shift,half,page) in enumerate(atlas['variants']):
            for x in (0,1,7,148,151,158,159):
                bank=half if shift else 0
                patterns=bytearray(atlas['patterns'][bank]);colors=bytearray(atlas['colors'][bank])
                flag=(0 if color==15 else 32)+kind*16+x%16
                if shift and half and atlas['patch_flags'][flag]:
                    at=(248+page*4)*8;patch=(kind*16+x%16)*32
                    patterns[at:at+32]=atlas['patches'][patch:patch+32];colors[at:at+32]=bytes((color*16,))*32
                row=atlas['rows'][(index*160+x)*32:(index*160+x+1)*32]
                actual=bytearray(256*8);expected=bytearray(256*8)
                for y in range(8):
                    for px in range(256):
                        tile=row[px//8];at=tile*8+y
                        actual[y*256+px]=(colors[at]>>4) if patterns[at]&(128>>(px%8)) else colors[at]&15
                for copy in range(count):
                    root=(x+copy*gap)%160
                    for y in range(8):
                        sy=y+half*8-shift
                        for sx in range(16 if kind==0 else 8):
                            if root+sx<160 and model.mask(kind,sx,sy):
                                for px in range(model.display_x(root+sx),model.display_x(root+sx+1)):expected[y*256+px]=color
                self.assertEqual(actual,expected,(index,x))
