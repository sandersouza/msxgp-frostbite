"""Original-free lossless fragment and hardware allocation contracts."""
import hashlib
import importlib
import copy
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
            self.assertEqual(first['tile_generations'], {'slots_each': 64, 'count': 2, 'banks': 3})
            regions = first['vram_regions']
            for index, a in enumerate(regions):
                self.assertLessEqual(a['end'], 16384)
                for b in regions[index + 1:]: self.assertFalse(a['start'] < b['end'] and b['start'] < a['end'])
            self.assertFalse(first['runtime_qualified'])
            with self.assertRaises(FileExistsError): api.compile_assets(rom, Path(directory) / 'a', measured_palette=palette)
            with self.assertRaisesRegex(ValueError, '128'): api.compile_assets(rom, Path(directory) / 'c', measured_palette={0: (0, 0, 0)})

    def test_generation_updates_never_touch_live_patterns_names_or_sprite_shapes(self):
        api = self.api(); from graphics_mapping import decode_screen
        image = bytearray([1]) * 49152; image[:8] = bytes((1, 1, 1, 2, 2, 2, 3, 4))
        state = None; last = None
        for step in range(4):
            planned = api.pack_frame(bytes(image), state)
            self.assertEqual(decode_screen(planned['decoded_vram']), bytes(image))
            self.assertEqual(planned['sprite_patterns_bytes'], 64)
            self.assertEqual(planned['sprites_per_line'], 2)
            for upload in planned['uploads']:
                if upload['phase'] == 'prepare' and last:
                    for bank in range(3):
                        active = last['generation'] * 512
                        for base in (bank * 2048, 0x2000 + bank * 2048):
                            self.assertFalse(upload['address'] < base + active + 512 and base + active < upload['address'] + len(upload['data']))
                    for start, end in ((last['names_address'], last['names_address'] + 768),
                                       (0x3800 + last['generation'] * 512, 0x3A00 + last['generation'] * 512)):
                        self.assertFalse(upload['address'] < end and start < upload['address'] + len(upload['data']))
            self.assertTrue(all(upload['address'] == 0x1B00 for upload in planned['uploads'] if upload['phase'] == 'commit'))
            if step >= 2:
                self.assertEqual(planned['new_tiles'], 0)
                self.assertEqual(planned['prepare_bytes'], 0)
            state = planned['cache']; last = planned
        image[0:8] = bytes([15]) * 8
        changed = api.pack_frame(bytes(image), state)
        self.assertGreater(changed['new_tiles'], 0)
        self.assertEqual(decode_screen(changed['decoded_vram']), bytes(image))

    def test_fragment_eviction_is_local_to_inactive_generation_and_capacity_is_enforced(self):
        api = self.api()
        def frame(start, count):
            image = bytearray([1]) * 49152
            for tile in range(count):
                value = (start + tile) % 256
                for bit in range(8):
                    if value & (128 >> bit): image[((tile // 32) * 8) * 256 + (tile % 32) * 8 + bit] = 2
            return bytes(image)
        cache = None
        for start in (1, 65, 129, 193, 65, 1, 193, 129):
            before = copy.deepcopy(cache); result = api.pack_frame(frame(start, 63), cache)
            self.assertEqual(cache, before)
            self.assertTrue(all(len(bank) <= 64 for group in result['cache']['tiles'] for bank in group))
            cache = result['cache']
        with self.assertRaisesRegex(ValueError, '64'): api.pack_frame(frame(1, 64), cache)

    def test_exact_tile_cache_and_two_name_shadows_fit_existing64k_ram(self):
        api = self.api(); layout = api.memory_layout()
        self.assertEqual(layout['ram_bytes'], 65536)
        areas = {area['name']: area for area in layout['regions']}
        self.assertEqual((areas['canonical']['start'], areas['canonical']['end']), (0xC000, 0xC080))
        self.assertEqual(areas['tile_bytes']['end'] - areas['tile_bytes']['start'], 2 * 3 * 64 * 16)
        self.assertEqual((areas['heap_guard']['start'], areas['heap_guard']['end']), (0xE800, 0xF300))
        self.assertEqual((areas['source_abi']['start'], areas['source_abi']['end']), (0xC600, 0xC700))
        for name in ('names_a', 'names_b'): self.assertEqual(areas[name]['end'] - areas[name]['start'], 768)
        for index, a in enumerate(layout['regions']):
            self.assertGreaterEqual(a['start'], 0xC000); self.assertLessEqual(a['end'], 0xF380)
            for b in layout['regions'][index + 1:]:
                self.assertFalse(a['start'] < b['end'] and b['start'] < a['end'])
        self.assertFalse(layout['runtime_qualified'])
