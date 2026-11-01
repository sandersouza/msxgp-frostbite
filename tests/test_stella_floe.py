import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class StellaFloeTests(unittest.TestCase):
    def test_probe_completion_cannot_accept_partial_empty_or_duplicate_markers(self):
        api=importlib.import_module('stella_floe')
        row=bytes(58)+bytes([7])+bytes(19)
        self.assertEqual(api.validate_observation(row*2,'FROSTBITE_PROBE_COMPLETE 2\n',2,True),2)
        for data,log,count in ((b'','FROSTBITE_PROBE_COMPLETE 0\n',0),(row[:-1],'FROSTBITE_PROBE_COMPLETE 1\n',1),
                (row,'FROSTBITE_PROBE_COMPLETE 2\n',1),(row,'',1),(row,'FROSTBITE_PROBE_COMPLETE 1\n'*2,1)):
            with self.assertRaises(ValueError):api.validate_observation(data,log,count,True)
    def test_domain_and_fixture_exclude_undeclared_shape_or_partial_ram(self):
        api=importlib.import_module('stella_floe')
        rom=bytearray(4096);rom[0xde0:0xdf0]=bytes(range(16))
        self.assertEqual(api.control_pairs(rom),[(0,0),(16,0),(32,0),(48,0),(64,0),(80,0),(96,0),(112,0),(128,0),(144,0),(160,0),(176,0),(192,0),(208,0),(224,0),(240,0)])
        ram=api.fixture(bytes(128),159,77,151,(48,64))
        self.assertEqual(len(ram),128);self.assertEqual(ram[0x1c:0x1e],bytes((48,64)))
        self.assertEqual(ram[0x1f:0x23],bytes([151])*4)
        for args in ((bytes(127),0,53,0,(0,0)),(bytes(128),160,53,0,(0,0)),(bytes(128),0,256,0,(0,0))):
            with self.assertRaises(ValueError):api.fixture(*args)
