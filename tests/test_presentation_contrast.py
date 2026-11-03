"""Semantic visibility must not use the palette mapper as its own oracle."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class IceContrastTests(unittest.TestCase):
    def test_real_source_blue_pixel_cannot_disappear_into_the_sea(self):
        api=importlib.import_module('presentation_contrast_check')
        source=bytearray([0x90])*(160*210);source[100*160+41]=0x98
        target=bytearray([4])*(256*192)
        with self.assertRaisesRegex(ValueError,'touched-ice'):api.verify_colors(bytes(source),bytes(target))
        y=100-7;left=8+3*41//2;right=8+3*42//2
        target[y*256+left:y*256+right]=bytes([5])*(right-left)
        counts=api.verify_colors(bytes(source),bytes(target));self.assertEqual(counts['touched_ice_source_pixels'],1)
        target[y*256+left-1]=5
        with self.assertRaisesRegex(ValueError,'sea'):api.verify_colors(bytes(source),bytes(target))
        with self.assertRaises(ValueError):api.verify_colors(bytes(source[:-1]),bytes(target))
