"""Decode the active SCREEN2 page and enforce actual full sprite rectangles."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationCheckTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_check'), 'actual presentation checker missing')
        return importlib.import_module('presentation_check')

    def test_active_name_page_and_transparent_backdrop_are_decoded_from_registers(self):
        api = self.api(); vram = bytearray(16384); vram[0x1B00] = 208
        regs = bytes((2, 0xC2, 6, 255, 3, 0x36, 7, 1))
        self.assertEqual(api.decode_target(vram, regs), bytes([1]) * 49152)
        vram[0x1C00] = 1; vram[8:16] = bytes([255]) * 8; vram[0x2008:0x2010] = bytes([0xF1]) * 8
        self.assertEqual(api.decode_target(vram, regs), bytes([1]) * 49152)
        alternate = bytearray(regs); alternate[2] = 7
        image = api.decode_target(vram, alternate)
        for y in range(8): self.assertEqual(image[y * 256:y * 256 + 8], bytes([15]) * 8)
        self.assertEqual(sum(value == 15 for value in image), 64)

    def test_fifth_blank_sprite_and_unsupported_vdp_registers_cannot_hide_in_pixel_equality(self):
        api = self.api(); vram = bytearray(16384); regs = bytearray((2, 0xC2, 6, 255, 3, 0x36, 7, 1))
        for index in range(5): vram[0x1B00 + index * 4:0x1B04 + index * 4] = bytes((255, index * 24, 0, 0))
        vram[0x1B14] = 208
        with self.assertRaisesRegex(ValueError, 'scanline'): api.decode_target(vram, regs)
        vram[0x1B00] = 208
        for address, value in ((1, 0xC0), (2, 5), (3, 0), (4, 0), (5, 0), (6, 0)):
            bad = bytearray(regs); bad[address] = value
            with self.assertRaises(ValueError): api.decode_target(vram, bad)
