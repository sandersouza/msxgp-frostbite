"""New native presentation profile cannot relabel or overwrite older ROMs."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationBuildTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_build'), 'native presentation builder missing')
        return importlib.import_module('presentation_build')

    def test_flat_water_identity_requires_exact_pattern_and_both_colour_nibbles(self):
        api=self.api();self.assertTrue(hasattr(api,'flat_water_ids'),'finite flat-background identity missing')
        tables={'patterns':[bytes([255])*16]*3,'colors':[bytes([17])*8+bytes([68])*8]*3}
        self.assertEqual(api.flat_water_ids(tables),[129,129,129])
        for field in ('patterns','colors'):
            bad={k:list(v) for k,v in tables.items()};changed=bytearray(bad[field][1]);changed[-1]^=1;bad[field][1]=bytes(changed)
            with self.assertRaises(ValueError):api.flat_water_ids(bad)

    def test_cartridge_identity_is_distinct_and_standard_msx1_requirements_are_explicit(self):
        api = self.api(); profile = api.profile()
        self.assertEqual(profile['version'], '0.0.7-presentation')
        self.assertEqual(profile['signature'], 'FBP0')
        self.assertEqual(profile['ram_bytes'], 65536); self.assertEqual(profile['vram_bytes'], 16384)
        self.assertEqual(profile['clock_hz'], 3579545); self.assertEqual(profile['mapper'], 'ASCII16')
        self.assertFalse(profile['runtime_qualified']); self.assertEqual(profile['source_sha256'],
            'cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834')
        image = bytearray([255]) * 4194304; image[:20] = b'AB' + (0x4014).to_bytes(2, 'little') + bytes(12) + b'FBP0'
        self.assertEqual(api.validate_rom(image), [])
        for marker in (b'FBF0', b'FBM0'):
            image[16:20] = marker; self.assertTrue(api.validate_rom(image))
        self.assertTrue(api.validate_rom(bytes(32768)))

    def test_bank_plan_keeps_frozen_contact_indices_and_reuses_only_free_banks(self):
        api = self.api(); banks = api.bank_layout(239)
        self.assertEqual(banks['resident'], 0); self.assertEqual(banks['fragments'], 1); self.assertEqual(banks['native'], 2)
        self.assertEqual(banks['contacts'], list(range(14, 253)))
        self.assertEqual(banks['available_assets'], list(range(3, 14)) + [253, 254, 255])
        self.assertEqual(len(set([0, 1, 2] + banks['contacts'] + banks['available_assets'])), 256)
        with self.assertRaises(ValueError): api.bank_layout(243)
        with self.assertRaises(ValueError): api.bank_layout(-1)

    def test_live_sprite_work_replaces_unconsumed_proposed_scene_snapshots(self):
        regions={row['name']:(row['start'],row['end']) for row in self.api().profile()['ram']['regions']}
        self.assertNotIn('scene_snapshots',regions)
        self.assertEqual(regions['sprite_pattern_work'],(0xC500,0xC600))
        self.assertEqual(regions['source_abi'],(0xC600,0xC700))

    def test_sparse_profile_cannot_alias_references_with_input_or_graphics_rpc(self):
        profile=self.api().profile(fast=True)
        regions={row['name']:(row['start'],row['end']) for row in profile['ram']['regions']}
        self.assertNotIn('diagnostic_input',regions);self.assertNotIn('tile_bytes',regions)
        self.assertEqual(regions['tile_references'],(0xC080,0xC200))
        self.assertEqual(regions['graphics_rpc'],(0xC760,0xC780))
        self.assertEqual(regions['constructor_keys'],(0xD000,0xD900))
        self.assertEqual(regions['constructor_links'],(0xD900,0xDA80))
        self.assertEqual(regions['constructor_buckets'],(0xDB00,0xE100))
        self.assertEqual(regions['sprite_shadow'],(0xE100,0xE500))
        self.assertEqual(regions['fusion_work'],(0xE500,0xE540))
        self.assertEqual(regions['visual_state_work'],(0xE540,0xE580))
        self.assertEqual(regions['renderer_work'],(0xE580,0xE800))
        self.assertEqual(regions['sprite_pattern_work'],(0xC500,0xC540))
        self.assertEqual(regions['scene_a'],(0xC540,0xC5A0))
        self.assertEqual(regions['scene_b'],(0xC5A0,0xC600))
        self.assertEqual(regions['heap_guard'],(0xE800,0xF300))
        for name,(start,end) in regions.items():
            for other,(a,b) in regions.items():
                if name!=other:self.assertTrue(end<=a or b<=start,f'{name}/{other} alias')
        self.assertEqual(profile['diagnostic_flags'],[0xC2DE,0xC2DF])
