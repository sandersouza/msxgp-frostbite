import copy
import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class ComparatorTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('trace_compare'), 'strict trace comparator missing')
        return importlib.import_module('trace_compare')

    def fixture(self):
        return {'schema_version': 1, 'source_sha256': 'a' * 64, 'backend': 'Stella7-test',
                'initial_sha256': 'b' * 64, 'policy': {'seed': 42},
                'steps': [{'index': i, 'input': {'swcha': 255, 'swchb': 63, 'fire': [False, False]},
                           'cpu': {'p': 0x20, 'pc': 0xF019}, 'ram': [i] * 128,
                           'tia': {'collision': i}, 'state_sha256': str(i) * 64} for i in range(2)]}

    def test_equal_complete_trace_matches(self):
        expected = self.fixture()
        self.assertEqual(self.api().compare_traces(expected, copy.deepcopy(expected)), [])

    def test_matching_empty_or_incomplete_traces_do_not_establish_acceptance(self):
        for invalid in ({}, {**self.fixture(), 'steps': []},
                        {**self.fixture(), 'source_sha256': 'not a hash'}):
            self.assertTrue(self.api().compare_traces(invalid, copy.deepcopy(invalid)))
        invalid = self.fixture(); invalid['steps'][0]['ram'].pop()
        self.assertTrue(self.api().compare_traces(invalid, copy.deepcopy(invalid)))

    def test_coordinate_flag_collision_order_input_and_provenance_fail(self):
        for mutation in ('coordinate', 'flag', 'collision', 'order', 'input', 'seed', 'short'):
            with self.subTest(mutation=mutation):
                expected = self.fixture(); actual = copy.deepcopy(expected)
                if mutation == 'coordinate': actual['steps'][0]['ram'][0x64] = 9
                elif mutation == 'flag': actual['steps'][0]['cpu']['p'] ^= 1
                elif mutation == 'collision': actual['steps'][0]['tia']['collision'] ^= 1
                elif mutation == 'order': actual['steps'].reverse()
                elif mutation == 'input': actual['steps'][0]['input']['swcha'] = 254
                elif mutation == 'seed': actual['policy']['seed'] = 43
                elif mutation == 'short': actual['steps'].pop()
                self.assertTrue(self.api().compare_traces(expected, actual))
