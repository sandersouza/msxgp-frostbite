import copy
import importlib
from pathlib import Path
import sys
import struct
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class ProgressionDeliveryTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('progression_delivery'), 'progression evidence sealer missing')
        return importlib.import_module('progression_delivery')

    def test_all_modes_original_hazards_native_and_eight_views_are_required(self):
        api = self.api()
        names = {'progression-v0', 'progression-v1', 'progression-v2', 'progression-v3',
                 'exhaustion-restart-v0', 'exhaustion-restart-v1', 'exhaustion-restart-v2', 'exhaustion-restart-v3',
                 'bear-chase', 'bear-refuge', 'fish-envelope', 'threat-push'}
        views = {f'{f}-layout{l}-width{w}': 'capture/verified.json' for f in ('ntsc', 'pal') for l in (0, 1) for w in (0, 1)}
        routes = {name: {'source': 'source', 'replay': 'replay', 'native': 'native/natural.json', 'paced': dict(views)} for name in names}
        api.validate_matrix(routes)
        for name in names:
            bad = copy.deepcopy(routes); del bad[name]
            with self.assertRaises(ValueError): api.validate_matrix(bad)
        for field in ('source', 'replay', 'native'):
            bad = copy.deepcopy(routes); del bad['progression-v0'][field]
            with self.assertRaises(ValueError): api.validate_matrix(bad)
        bad = copy.deepcopy(routes); del bad['progression-v3']['paced']['pal-layout1-width1']
        with self.assertRaises(ValueError): api.validate_matrix(bad)

    def test_paced_receipts_reject_stale_rom_dirty_source_and_unsafe_or_wrong_views(self):
        api = self.api(); sha = 'a' * 64; route_sha = 'b' * 64
        r = {'complete': True, 'exploratory': False, 'rom': {'sha256': sha}, 'source_steps': 2, 'frames': 1,
             'canonical_ram_injections': 0, 'clock_hz': 3579545, 'ram_bytes': 65536, 'min_spacing': 29,
             'max_sprites_per_line': 4, 'stack_min': 0xF340, 'pal_flag': 0, 'layout': 0, 'width': 0,
             'family': 'ntsc', 'frame_budget': 59736, 'max_busy_cycles': 59000, 'min_margin_cycles': 736,
             'pixel_errors': 0, 'original_route_sha256': route_sha}
        api.validate_paced(r, sha, route_sha, 2, ('ntsc', 0, 0))
        for changes in ({'rom': {'sha256': 'c' * 64}}, {'exploratory': True}, {'source_steps': 1},
                        {'max_busy_cycles': 59736}, {'min_margin_cycles': 735}, {'pixel_errors': 1},
                        {'min_spacing': 28}, {'layout': True}, {'family': 'pal'}, {'frames': 0}):
            with self.assertRaises(ValueError): api.validate_paced({**r, **changes}, sha, route_sha, 2, ('ntsc', 0, 0))

    def test_stress_maximum_is_recomputed_from_actual_raw_cycle_list(self):
        api = self.api()
        r = {'busy_cycles': [30, 10, 20], 'frame_budget': 100, 'max_busy_cycles': 30}
        self.assertEqual(api.observed_maximum(r, {'busy_cycles': [30, 10, 20]}), 30)
        for changes in ({'max_busy_cycles': 29}, {'max_busy_cycles': 31}, {'busy_cycles': []}, {'busy_cycles': [30, 100, 20]}):
            with self.assertRaises(ValueError): api.observed_maximum({**r, **changes}, {'busy_cycles': [30, 10, 20]})
        with self.assertRaises(ValueError): api.observed_maximum(r, {'busy_cycles': [30, 11, 20]})

    def test_native_maximum_requires_complete_actual_rows_and_exact_receipt(self):
        api = self.api(); rows = bytes(133) + struct.pack('<I', 500) + bytes(133) + struct.pack('<I', 700)
        self.assertEqual(api.native_maximum(rows, 2, 700), 700)
        for raw, count, maximum in ((rows[:-1], 2, 700), (rows, 1, 700), (rows, 2, 699), (b'', 0, 0)):
            with self.assertRaises(ValueError): api.native_maximum(raw, count, maximum)

    def test_missing_or_ineffective_negative_witness_never_passes(self):
        api = self.api(); sha = 'a' * 64
        r = {'detected': True, 'rom_sha256': sha, 'harness_dirty': False, 'detail': 'RAM CA differs'}
        api.validate_negative('score', r, sha)
        for changes in ({'detected': False}, {'rom_sha256': 'b' * 64}, {'harness_dirty': True},
                        {'detail': 'intended fault escaped detection'}, {'detail': 'RAM CE differs'}):
            with self.assertRaises(ValueError): api.validate_negative('score', {**r, **changes}, sha)

