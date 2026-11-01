import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import render_model as model


class ProgressionBuildTests(unittest.TestCase):
    def test_custom_banner_leaves_gameplay_rows_and_debug_coordinates_intact(self):
        api = importlib.import_module('hazard_build')
        scene = model.scene(64)
        original = api.diagnostic_names(scene)
        changed = api.diagnostic_names(scene, banner=('PROGRESSION DIAGNOSTIC', 'ALL MODES NO AUDIO'))
        self.assertEqual(changed[96:], original[96:])
        self.assertEqual(changed[32 + 27:32 + 32], original[32 + 27:32 + 32])
        self.assertNotEqual(changed[:64], original[:64])
        self.assertEqual(api.diagnostic_names(scene, banner=None), original)
        for bad in (('A' * 32, 'OK'), ('OK', 'A' * 27), ('lowercase', 'OK'), ('OK',)):
            with self.assertRaises(ValueError): api.diagnostic_names(scene, banner=bad)

    def test_progression_profile_pixels_include_its_real_boot_banner(self):
        self.assertIsNotNone(importlib.util.find_spec('progression_build'), 'progression build profile missing')
        api = importlib.import_module('progression_build')
        hazard = importlib.import_module('hazard_build')
        scene = model.scene(64)
        self.assertEqual(len(api.diagnostic_names(scene)), 768)
        self.assertNotEqual(bytes(api.expected_pixels(scene))[:256 * 16], bytes(hazard.expected_pixels(scene))[:256 * 16])
        self.assertEqual(bytes(api.expected_pixels(scene))[256 * 24:], bytes(hazard.expected_pixels(scene))[256 * 24:])

