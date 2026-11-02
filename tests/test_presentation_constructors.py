"""Typed exact cache keys retain every visible constructor argument."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class PresentationConstructorTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_constructors'),'typed constructor grammar missing')
        return importlib.import_module('presentation_constructors')
    def test_pattern_palette_background_and_clip_fields_do_not_alias(self):
        api=self.api();keys=set()
        for pattern in (0,1,255,256,12097,16383):
            for background in (128,129,255):
                for color in (1,4,14,15):
                    for clip in (False,True):
                        key=api.mono_key(pattern,background,color,clip)
                        self.assertEqual(len(key),6);self.assertEqual(key[-1],0)
                        self.assertNotIn(key,keys);keys.add(key)
        for bad in (-1,16384):
            with self.assertRaises(ValueError):api.mono_key(bad,128,1,False)
    def test_header_keys_cover_four_glyphs_shared_row_and_all_palette_fields(self):
        api=self.api()
        for glyphs in ((0,0,0,0),(33,32,31,30),(1,2,3,4)):
            key=api.header_key(glyphs,15,14,7,3,1)
            self.assertEqual(api.header_fields(key),(glyphs,15,14,7,3,1))
        base=api.header_key((1,2,3,4),15,14,7,3,1)
        for i in range(4):
            changed=[1,2,3,4];changed[i]+=1
            self.assertNotEqual(api.header_key(changed,15,14,7,3,1),base)
        for args in ((14,14,7,3,1),(15,15,7,3,1),(15,14,6,3,1),(15,14,7,1,1),(15,14,7,3,0)):
            self.assertNotEqual(api.header_key((1,2,3,4),*args),base)
    def test_typed_layers_and_literal_rows_are_exact_and_disjoint(self):
        api=self.api();mono=api.mono_key(1,128,4,False)
        union=api.union_key(1,128,4,False)
        self.assertNotEqual(mono,union)
        for kind,expected in ((1,{0:128,7:64}),(2,{0:128,1:64,7:32}),(3,{0:128,6:64,7:32})):
            masks=(128,64,0) if kind==1 else (128,64,32)
            key=api.literal_key(masks,2,15,kind)
            tile=api.construct(key,patterns=[],backgrounds={},header=b'',footer=[])
            self.assertEqual({i:b for i,b in enumerate(tile[:8]) if b},expected)
        with self.assertRaises(ValueError):api.literal_key((1,2,3),2,15,1)

    def test_shared_header_tile_retains_distinct_score_and_status_colors(self):
        api=self.api();data=bytes((glyph*7+part*11+row*13)&255 for glyph in range(34) for part in range(5) for row in range(8))
        key=api.header_key((1,2,3,4),15,14,7,3,1)
        tile=api.construct(key,patterns=[],backgrounds={},header=data,footer=[])
        self.assertEqual(tile[8:],bytes((247,247,247,119,119,119,119,231)))
        for y in range(3):self.assertEqual(tile[y],data[1*40+4*8+y+5]|data[2*40+y+5])
        self.assertEqual(tile[7],data[3*40+4*8]|data[4*40])
        self.assertEqual(tile[3:7],bytes(4))

    def test_monochrome_constructor_rejects_an_unrepresentable_third_color(self):
        api=self.api();background=bytes((170,))*8+bytes((36,))*8;patterns=[bytes((240,))*8]
        for color in (2,4):api.construct(api.mono_key(0,128,color,False),patterns=patterns,backgrounds={128:background},header=b'',footer=[])
        with self.assertRaises(ValueError):api.construct(api.mono_key(0,128,15,False),patterns=patterns,backgrounds={128:background},header=b'',footer=[])

    def test_flat_water_uses_literal_mask_and_a_constant_colour_pair(self):
        api=self.api();mask=bytes((0,1,15,16,128,240,254,255))
        water=bytes([255])*8+bytes([68])*8
        for color in (1,4,15):
            for clip in (False,True):
                tile=api.construct(api.mono_key(0,128,color,clip),patterns=[mask],backgrounds={128:water},header=b'',footer=[])
                expected=bytes(v&(15 if clip else 255) for v in mask)+bytes([color*16+4])*8
                self.assertEqual(tile,expected)

    def test_water_normalization_preserves_all_pixels_for_every_byte_mask_colour_and_clip(self):
        api=self.api();water=bytes([255])*8+bytes([68])*8
        for mask in range(256):
            for color in range(1,16):
                for clip in (False,True):
                    tile=api.construct(api.mono_key(0,128,color,clip),patterns=[bytes([mask])*8],backgrounds={128:water},header=b'',footer=[])
                    visible=mask&(15 if clip else 255)
                    for y in range(8):
                        actual=tuple(tile[y+8]>>4 if tile[y]&(128>>x) else tile[y+8]&15 for x in range(8))
                        expected=tuple(color if visible&(128>>x) else 4 for x in range(8))
                        self.assertEqual(actual,expected)
