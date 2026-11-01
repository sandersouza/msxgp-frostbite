"""Original-free lossless fragment and hardware allocation contracts."""
import hashlib
import importlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationAssetsTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_assets'), 'finite presentation compiler missing')
        return importlib.import_module('presentation_assets')

    def test_every_byte_and_phase_expands_to_exact_approved_pixel_intervals(self):
        api = self.api()
        # Independent source-space intervals, including asymmetric 1/2px widths.
        for x in range(32):
            origin = (8 + 3 * x // 2) // 8 * 8
            for mask in range(256):
                row = api.expand(mask, x)
                self.assertEqual(len(row), 3)
                decoded = {origin + bit for bit in range(24) if row[bit // 8] & (128 >> (bit % 8))}
                expected = set()
                for bit in range(8):
                    if mask & (128 >> bit):
                        expected.update(range(8 + 3 * (x + bit) // 2, 8 + 3 * (x + bit + 1) // 2))
                self.assertEqual(decoded, expected)
        self.assertEqual(api.expand(255, 0), bytes((255, 240, 0)))
        for mask, x in ((-1, 0), (256, 0), (0, -1), (0, 160), (True, 0)):
            with self.assertRaises(ValueError): api.expand(mask, x)

    def test_clip_and_reverse_preserve_source_wrap_and_hmove_black_bar(self):
        api = self.api()
        self.assertEqual([api.clip_mask(x) for x in (0, 1, 7, 8, 152, 158, 159)], [0, 1, 127, 255, 255, 192, 128])
        for mask in range(256):
            flipped = api.reverse(mask)
            self.assertEqual(api.reverse(flipped), mask)
            self.assertEqual(flipped.bit_count(), mask.bit_count())
        self.assertEqual(api.reverse(0x81), 0x81); self.assertEqual(api.reverse(0x03), 0xC0)

    def test_scanline_budget_counts_entire_rectangles_and_offscreen_clipping(self):
        api = self.api()
        boxes = [{'x': n * 24, 'y': 10, 'width': 16, 'height': 16} for n in range(4)]
        self.assertEqual(api.check_rectangles(boxes)['max_per_line'], 4)
        # Even a completely blank mask consumes the hardware scanline slot.
        with self.assertRaisesRegex(ValueError, 'scanline'): api.check_rectangles(boxes + [{**boxes[0], 'x': 200, 'mask': bytes(32)}])
        self.assertEqual(api.check_rectangles(boxes + [{**boxes[0], 'y': 26}])['max_per_line'], 4)
        self.assertEqual(api.check_rectangles([{'x': -32, 'y': 191, 'width': 16, 'height': 16}])['max_per_line'], 1)
        with self.assertRaisesRegex(ValueError, '32'): api.check_rectangles([{**boxes[0], 'y': n * 16} for n in range(33)])

    def test_compiler_is_bounded_deterministic_and_preserves_full_glyph_source(self):
        api = self.api(); rom = bytes(range(256)) * 16
        palette = {code: (code, code, code) for code in range(0, 256, 2)}
        with tempfile.TemporaryDirectory() as directory:
            first = api.compile_assets(rom, Path(directory) / 'a', measured_palette=palette)
            second = api.compile_assets(rom, Path(directory) / 'b', measured_palette=palette)
            self.assertEqual(first, second)
            bank = (Path(directory) / 'a' / 'fragments.bin').read_bytes()
            self.assertEqual(len(bank), 16384); self.assertEqual(first['used_bytes'], 13984)
            self.assertEqual(first['source_sha256'], hashlib.sha256(rom).hexdigest())
            self.assertEqual(first['sha256'], hashlib.sha256(bank).hexdigest())
            section = first['sections']['glyphs']
            self.assertEqual(bank[section['offset']:section['offset'] + section['size']], rom[0xC00:])
            self.assertEqual(first['tile_generations'], {'slots_each': 128, 'count': 2, 'banks': 3})
            regions = first['vram_regions']
            for index, a in enumerate(regions):
                self.assertLessEqual(a['end'], 16384)
                for b in regions[index + 1:]: self.assertFalse(a['start'] < b['end'] and b['start'] < a['end'])
            self.assertFalse(first['runtime_qualified'])
            with self.assertRaises(FileExistsError): api.compile_assets(rom, Path(directory) / 'a', measured_palette=palette)
            with self.assertRaisesRegex(ValueError, '128'): api.compile_assets(rom, Path(directory) / 'c', measured_palette={0: (0, 0, 0)})
