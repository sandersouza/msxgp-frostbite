import copy
import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class IndependentCPUTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('reference_cpu_check'), 'independent CPU cross-check missing')
        return importlib.import_module('reference_cpu_check')

    def test_controlled_cpu_fixture_preserves_tia_and_sets_complete_ram(self):
        from test_reference_state import synthetic_state
        from reference_state import decode_state
        api = self.api(); raw = synthetic_state()
        case = {'start': 'FB9B', 'ram': {'CA': '01'}, 'registers': {'a': 0x99, 'p': 0x29}}
        state = decode_state(api.prepare_cpu_fixture(raw, case))
        self.assertEqual((state['cpu']['pc'], state['cpu']['a'], state['cpu']['p']), (0xFB9B, 0x99, 0x29))
        self.assertEqual(state['ram'], [1 if i == 0x4A else 0 for i in range(128)])
        self.assertEqual(state['tia_bytes'], decode_state(raw)['tia_bytes'])
        with self.assertRaises(ValueError): api.prepare_cpu_fixture(raw, {**case, 'mmio': {'0000': '80'}})
        with self.assertRaises(ValueError): api.prepare_cpu_fixture(raw, {**case, 'ram': {'7F': '01'}})

    def test_independent_comparison_rejects_flags_and_any_ram_byte(self):
        from test_reference_state import synthetic_state
        from reference_state import decode_state
        state = decode_state(synthetic_state()); state['ram'] = [0] * 128
        expected = {'stop_pc': 'F000', 'registers': {'a': 0x12, 'x': 0x34, 'y': 0x56, 'p': 0x69, 'sp': 0xFD},
                    'ram': {f'{a:02X}': '00' for a in range(0x80, 0x100)}}
        self.assertEqual(self.api().compare_cpu(expected, state), [])
        wrong = copy.deepcopy(state); wrong['cpu']['p'] ^= 1
        self.assertTrue(self.api().compare_cpu(expected, wrong))
        wrong = copy.deepcopy(state); wrong['ram'][0x64] = 0x77
        self.assertTrue(self.api().compare_cpu(expected, wrong))

    def test_arithmetic_vectors_are_bound_to_actual_source_instructions(self):
        api = self.api(); rom = bytearray(4096)
        rom[0xB9B:0xB9D] = bytes([0x65, 0xCA]); rom[0xBC5:0xBC7] = bytes([0xE9, 1])
        cases = api.arithmetic_vectors(bytes(rom))
        self.assertEqual(len(cases), 288)
        self.assertEqual({c['start'] for c in cases}, {'FB9B', 'FBC5'})
        rom[0xB9B] = 0xEA
        with self.assertRaises(ValueError): api.arithmetic_vectors(bytes(rom))
