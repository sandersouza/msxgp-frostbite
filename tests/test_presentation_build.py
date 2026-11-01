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
