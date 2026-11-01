import importlib
import importlib.util
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class GraphicsMappingTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('graphics_mapping'),'mapping compiler missing')
        return importlib.import_module('graphics_mapping')

    def test_mapping_retains_all_192_active_source_rows_and_right_edge(self):
        api=self.api()
        self.assertEqual([api.map_x(x) for x in (0,1,2,158,159,160)],[8,9,11,245,246,248])
        self.assertEqual([api.map_y(y) for y in (0,6,7,70,134,198,199,209)],[None,None,0,63,127,191,None,None])
        for x in (-1,161):
            with self.assertRaises(ValueError):api.map_x(x)
        source=bytes([0])*(160*210);mapped=api.map_frame(source,{0:(0,0,0)})
        self.assertEqual(mapped,bytes([1])*(256*192))

    def test_two_color_rows_and_three_screen_banks_decode_exactly(self):
        api=self.api();pixels=bytearray([1])*(256*192)
        for y,color in ((0,15),(63,6),(64,7),(127,8),(128,9),(191,10)):
            pixels[y*256:y*256+8]=bytes([color,1])*4
        compiled=api.compile_screen(bytes(pixels))
        self.assertEqual(len(compiled['vram']),16384)
        self.assertEqual(api.decode_screen(compiled['vram']),bytes(pixels))
        self.assertEqual(compiled['changed_pixels'],0)
        self.assertLessEqual(max(compiled['tiles_per_bank']),192)
        self.assertEqual(compiled['vram'][0x1B00],208)

    def test_overcolor_loss_is_explicit_and_deterministic(self):
        api=self.api();pixels=bytearray([1])*(256*192);pixels[:8]=bytes([1,1,1,2,2,2,3,4])
        a=api.compile_screen(bytes(pixels));b=api.compile_screen(bytes(pixels))
        self.assertEqual(a,b);self.assertEqual(a['changed_pixels'],2)
        self.assertEqual(api.decode_screen(a['vram'])[:6],bytes([1,1,1,2,2,2]))

    def test_invalid_pixels_palette_or_vram_are_rejected(self):
        api=self.api()
        for pixels in (b'',bytes([16])*(256*192),bytes(256*192)):
            with self.assertRaises(ValueError):api.compile_screen(pixels)
        with self.assertRaises(ValueError):api.decode_screen(bytes(16383))
        with self.assertRaises(ValueError):api.map_frame(bytes(160*210),{})
        with self.assertRaises(ValueError):api.map_frame(bytes(160*209),{0:(0,0,0)})
