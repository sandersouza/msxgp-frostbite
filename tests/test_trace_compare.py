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
        from test_reference_state import synthetic_state
        from reference_state import decode_state
        steps=[]
        for i in range(2):
            raw=bytearray(synthetic_state());state=decode_state(raw)
            raw[state['_offsets']['cpu']+5:state['_offsets']['cpu']+7]=(0xF019).to_bytes(2,'little')
            offset=state['_offsets']['ram'];raw[offset:offset+128]=bytes([i])*128
            steps.append({**decode_state(raw),'state_bytes':raw.hex(),'index':i,
                          'input':{'swcha':255,'swchb':63,'fire':[False,False]}})
        return {'schema_version': 2, 'source_sha256': 'a' * 64,
                'backend':{'name':'Stella','version':'7.0','source_contract':'d55b1aec0d067a4c901a6dcdf81cb8f579685659','binary_sha256':'c'*64},
                'initial_sha256': 'b' * 64, 'policy': {'host_seed': 42,'boundary':'PCF019'},'steps':steps}

    def test_matching_malformed_raw_or_logical_evidence_is_rejected(self):
        api=self.api()
        for section in ('cpu','tia','input','controllers','riot','host_rng','cycles','tia_bytes','state_bytes'):
            trace=self.fixture();del trace['steps'][0][section]
            with self.subTest(section=section):self.assertTrue(api.compare_traces(trace,copy.deepcopy(trace)))
        for path,value in (('cpu',{'pc':0xF019,'p':32}),('tia',{'placeholder':True}),('input',{'swcha':255})):
            trace=self.fixture();trace['steps'][0][path]=value
            self.assertTrue(api.compare_traces(trace,copy.deepcopy(trace)))
    def test_matching_incomplete_inputs_and_provenance_fail_in_both_modes(self):
        api=self.api()
        for target in ('raw','logical'):
            for field,value in (('input',{'swcha':255}),('input',{'swcha':255,'swchb':63,'fire':[0,1]}),
                                ('backend','unsupported'),('policy','unstructured')):
                trace=self.fixture()
                if target=='logical':trace=api.logical_oracle(trace)
                if field=='input':trace['steps'][0][field]=value
                elif target=='raw':trace[field]=value
                else:trace['oracle']['source_backend' if field=='backend' else field]=value
                compare=api.compare_traces if target=='raw' else api.compare_logical_oracles
                with self.subTest(target=target,field=field,value=value):self.assertTrue(compare(trace,copy.deepcopy(trace)))

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
                elif mutation == 'collision': actual['steps'][0]['tia']['collision_mask'] ^= 1
                elif mutation == 'order': actual['steps'].reverse()
                elif mutation == 'input': actual['steps'][0]['input']['swcha'] = 254
                elif mutation == 'seed': actual['policy']['host_seed'] = 43
                elif mutation == 'short': actual['steps'].pop()
                self.assertTrue(self.api().compare_traces(expected, actual))

    def test_native_logical_projection_preserves_mechanics_without_tia_machine_state(self):
        api=self.api();self.assertTrue(hasattr(api,'logical_oracle'),'target-ready logical oracle missing')
        trace=self.fixture()
        logical=api.logical_oracle(trace)
        self.assertNotIn('tia',logical['steps'][0])
        self.assertEqual(logical['steps'][0]['ram'],[0]*128)
        altered=copy.deepcopy(logical);altered['steps'][0]['collision_inputs']['shore_latch']^=0x80
        self.assertTrue(api.compare_logical_oracles(logical,altered))
        altered=copy.deepcopy(logical);altered['steps'][0]['ram'][0x66]=9
        self.assertTrue(api.compare_logical_oracles(logical,altered))
        self.assertEqual(api.compare_logical_oracles(logical,copy.deepcopy(logical)),[])
        from reference_state import decode_state
        alternate=copy.deepcopy(trace);raw=bytearray.fromhex(alternate['steps'][0]['state_bytes'])
        raw[17:25]=(999).to_bytes(8,'little')
        alternate['steps'][0].update(decode_state(raw),state_bytes=raw.hex())
        self.assertEqual(api.logical_oracle(alternate),logical)
