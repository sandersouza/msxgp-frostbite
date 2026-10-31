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

    def test_native_logical_projection_preserves_mechanics_without_tia_machine_state(self):
        api=self.api();self.assertTrue(hasattr(api,'logical_oracle'),'target-ready logical oracle missing')
        trace=self.fixture()
        for point in trace['steps']:point['cpu'].update(a=1,x=2,y=3,sp=255)
        logical=api.logical_oracle(trace)
        self.assertNotIn('tia',logical['steps'][0])
        self.assertEqual(logical['steps'][0]['ram'],[0]*128)
        altered=copy.deepcopy(logical);altered['steps'][0]['collision_inputs']['shore_latch']^=0x80
        self.assertTrue(api.compare_logical_oracles(logical,altered))
        altered=copy.deepcopy(logical);altered['steps'][0]['ram'][0x66]=9
        self.assertTrue(api.compare_logical_oracles(logical,altered))
        self.assertEqual(api.compare_logical_oracles(logical,copy.deepcopy(logical)),[])
        alternate=copy.deepcopy(trace);alternate['steps'][0]['cycles']=999
        self.assertEqual(api.logical_oracle(alternate),logical)
