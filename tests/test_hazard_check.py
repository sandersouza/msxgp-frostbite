import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardBoundaryTests(unittest.TestCase):
    def test_boundary_matrix_reaches_every_edge_mode_without_byte_truncation(self):
        api=importlib.import_module('hazard_check');domain=importlib.import_module('hazard_domain')
        rom=bytearray(4096);rom[0xD0A:0xD12]=bytes([1,2,16,32,48,64,80,96]);rom[0xDC2:0xDD2]=bytes([0,1,2,3,4]+[0]*11)
        cases=api.geometry_cases(bytes(128),rom)
        self.assertEqual(len(cases),14828);self.assertTrue(all(len(ram)==128 for ram in cases))
        edges=cases[-4488:];actual=set()
        for i,ram in enumerate(edges):
            row=i%4;actual.add((ram[0x66],ram[0x23+row],bool(ram[0x11+row]&128),ram[0x58+row]))
        expected={(px,*mode) for px in api.EDGE_XS for mode in domain.object_modes(rom)}
        self.assertEqual(actual,expected)
