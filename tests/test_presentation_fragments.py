"""Finite mask fragments must preserve every source bit at every phase."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationFragmentsTests(unittest.TestCase):
    def test_bit_masks_at_all_horizontal_and_vertical_phases_decode_exactly(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fragments'), 'finite geometry compiler missing')
        api = importlib.import_module('presentation_fragments')
        for width, height in ((8, 1), (8, 8), (16, 19), (24, 7)):
            bitmap = bytes(int((x * 7 + y * 3) % 11 < 4) for y in range(height) for x in range(width))
            for phase_x in range(16):
                for phase_y in range(8):
                    result = api.mask_tiles(bitmap, width, height, phase_x, phase_y)
                    origin = (8 + phase_x * 3 // 2) & ~7; decoded = set()
                    self.assertEqual(len(result['patterns']), result['columns'] * result['rows'])
                    for tile, pattern in enumerate(result['patterns']):
                        self.assertEqual(len(pattern), 8)
                        for y, row in enumerate(pattern):
                            for x in range(8):
                                if row & (128 >> x): decoded.add((origin + (tile % result['columns']) * 8 + x, (tile // result['columns']) * 8 + y))
                    expected = set()
                    for y in range(height):
                        for x in range(width):
                            if bitmap[y * width + x]:
                                for target in range(8 + (phase_x + x) * 3 // 2, 8 + (phase_x + x + 1) * 3 // 2): expected.add((target, phase_y + y))
                    self.assertEqual(decoded, expected)
        for values in ((bytes(64), 8, 8, -1, 0), (bytes(63), 8, 8, 0, 0), (bytes([2]) * 64, 8, 8, 0, 0)):
            with self.assertRaises(ValueError): api.mask_tiles(*values)

    def test_bank_records_never_cross_mapper_windows_or_mutate_state_after_overflow(self):
        api = importlib.import_module('presentation_fragments'); packed = api.BankImage([3, 253])
        self.assertEqual(packed.store(b'A' * 16383), bytes((0, 128, 3)))
        self.assertEqual(packed.store(b'BC'), bytes((0, 128, 253)))
        images = packed.images()
        self.assertEqual([len(image) for image in images], [16384, 16384])
        self.assertEqual(images[0][-1], 255); self.assertEqual(images[1][:3], b'BC\xff')
        before = packed.images()
        with self.assertRaises(ValueError): packed.store(bytes(16385))
        with self.assertRaises(ValueError): packed.store(bytes(16384))
        self.assertEqual(packed.images(), before)
        for banks in ([3, 3], [], [256], [True]):
            with self.assertRaises(ValueError): api.BankImage(banks)
        stream = api.BankImage([3, 253])
        self.assertEqual(stream.store(bytes(range(256)) * 80, record=False, alignment=8), bytes((0, 128, 3)))
        self.assertEqual(stream.used_bytes, 20480)

    def test_background_profiles_keep_source_borders_and_extra_coarse_scanline(self):
        api = importlib.import_module('presentation_fragments')
        from presentation_check import decode_target
        palette = {code: (84, 85, 237) for code in range(0, 256, 2)}
        palette.update({0: (0, 0, 0), 2: (44, 44, 44), 10: (200, 200, 200), 128: (33, 176, 59), 132: (66, 235, 245)})
        rom = bytearray(4096); rom[0xCB7:0xCC0] = bytes(range(16, 34, 2))
        tables = api.background_tables(bytes(rom), palette)
        self.assertEqual(len(tables['base_rows']), 4 * 72)
        self.assertEqual(tables['rng_index'], bytes(256))
        self.assertTrue(all(count <= 128 for count in tables['tiles_per_bank']))
        for coarse in (0, 1):
            for night in (0, 1):
                vram = bytearray(16384)
                for bank in range(3):
                    data = tables['patterns'][bank]; vram[bank * 2048 + 1024:bank * 2048 + 1024 + len(data)] = data
                    data = tables['colors'][bank]; vram[0x2400 + bank * 2048:0x2400 + bank * 2048 + len(data)] = data
                rows = bytearray(tables['base_rows'][(coarse * 2 + night) * 72:(coarse * 2 + night + 1) * 72])
                rows[3 * 3 + 1:3 * 3 + 3] = tables['gradient_rows'][night * 2:night * 2 + 2]
                for row in range(24):
                    col1, col2, middle = rows[row * 3:row * 3 + 3]
                    vram[0x1800 + row * 32:0x1820 + row * 32] = bytes((128, col1, col2)) + bytes([middle]) * 28 + bytes((128,))
                vram[0x3C00:0x3C20] = tables['black_sprite']
                for index, y in enumerate(range(64, 176, 16)): vram[0x1B00 + index * 4:0x1B04 + index * 4] = bytes((y - 1, 16, 128, 1))
                vram[0x1B1C] = 208
                actual = decode_target(vram, bytes((2, 0xC2, 6, 255, 3, 0x36, 7, 1)))
                expected = bytearray([1]) * 49152
                for y in range(192):
                    source_y = y + (7 if y < 179 else 10)
                    original_y = source_y - int(coarse and source_y >= 57)
                    color = (12 if night else 7) if 7 <= original_y < 33 else 4 if 33 <= original_y < 42 or 78 <= original_y < 185 else (1 if night else 15) if 42 <= original_y < 77 else 1
                    expected[y * 256 + 20:y * 256 + 248] = bytes([color]) * 228
                    if coarse and source_y == 57: expected[y * 256 + 8:y * 256 + 20] = bytes([1 if night else 15]) * 12
                self.assertEqual(actual, expected)
                ram = [0] * 128; ram[0x68] = 150 if coarse else 100; ram[0x4B] = 7 if night else 3
                before = list(ram)
                self.assertEqual(decode_target(api.background_vram(tables, ram), bytes((2, 0xC2, 6, 255, 3, 0x36, 7, 1))), expected)
                self.assertEqual(ram, before)
                ram[0x3F] = 128
                self.assertEqual(decode_target(api.background_vram(tables, ram), bytes((2, 0xC2, 6, 255, 3, 0x36, 7, 1))), bytes([1]) * 49152)

    def test_background_boot_payload_preserves_primitive_prefix_and_fixed_bank_capacity(self):
        api = importlib.import_module('presentation_fragments')
        tables = api.background_tables(bytes(4096), {code: (84, 85, 237) for code in range(0, 256, 2)})
        base = bytes([0xA5]) * 13984 + bytes([255]) * (16384 - 13984)
        packed = api.pack_background(base, 13984, tables)
        self.assertEqual(len(packed['bank']), 16384); self.assertEqual(packed['bank'][:13984], base[:13984])
        self.assertLessEqual(packed['used_bytes'], 16384)
        self.assertEqual(packed['sections']['rng']['offset'] % 256, 0)
        self.assertIn('p_bg_rng_data EQU', packed['assembly'])
        self.assertIn('p_bg_upload_static:', packed['initializers'])
        moved=api.pack_background(base,13984,tables,black_sprite_address=0x3FE0)
        self.assertEqual(moved['bank'],packed['bank'])
        self.assertIn('LD DE,$7FE0',moved['initializers'])
        self.assertNotIn('LD DE,$7C00',moved['initializers'])
        with self.assertRaises(ValueError):api.pack_background(base,13984,tables,black_sprite_address=0x3FF0)
        with self.assertRaises(ValueError): api.pack_background(base, 16380, tables)

    def test_fixed_grid_descriptor_classes_round_trip_every_record_and_split_at4096(self):
        api = importlib.import_module('presentation_fragments')
        records = [{'columns': 2, 'rows': 2, 'patterns': (index, 0, 1, 2)} for index in range(4097)]
        records += [records[0], {'columns': 3, 'rows': 1, 'patterns': (3, 4, 5)}]
        image = api.BankImage(list(range(3, 9))); packed = api.pack_descriptors(records, image)
        self.assertEqual([row['count'] for row in packed['classes']], [4096, 1, 1])
        self.assertEqual(packed['ids'][0], packed['ids'][4097])
        self.assertNotEqual(packed['ids'][4095] >> 12, packed['ids'][4096] >> 12)
        for original, code in zip(records, packed['ids']):
            cls = packed['classes'][code >> 12]; offset = cls['offset'] + (code & 4095) * cls['stride']
            encoded = image.data[offset:offset + cls['stride']]
            self.assertEqual((cls['columns'], cls['rows']), (original['columns'], original['rows']))
            self.assertEqual(tuple(int.from_bytes(encoded[n:n + 2], 'little') for n in range(0, len(encoded), 2)), original['patterns'])

    def test_geometry_metadata_fits_boot_tail_with_relocated_native_roots(self):
        api = importlib.import_module('presentation_fragments')
        geometry = {'roots': {'row': [[0,128,3]] * 66, 'floe': [[2,128,4]] * 9, 'bear': [[4,128,5]] * 16},
                    'classes': [{'columns':2,'rows':2,'stride':8,'count':4096,'offset':0x12340}] * 13,
                    'patterns':12098}
        base = {'bank': bytes([165]) * 15296 + bytes([255]) * 1088, 'used_bytes':15296}
        packed = api.pack_geometry_metadata(base, geometry, bytes(range(256)))
        self.assertEqual(len(packed['bank']),16384)
        self.assertEqual(packed['bank'][:15296],base['bank'][:15296])
        self.assertEqual(packed['sections']['row_map'],15360)
        self.assertEqual(packed['bank'][15360:15616],bytes(range(256)))
        self.assertEqual(packed['used_bytes'],15993)
        self.assertIn('p_geo_row_map_data EQU $BC00',packed['assembly'])
        self.assertIn('p_geo_class_count EQU 13',packed['assembly'])
        at = packed['sections']['classes']
        self.assertEqual(packed['bank'][at:at+8],bytes((2,2,8,0,16,64,35,1)))
        with self.assertRaises(ValueError): api.pack_geometry_metadata({**base,'used_bytes':16130},geometry,bytes(256))
