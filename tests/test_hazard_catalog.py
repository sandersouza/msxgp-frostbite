import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardCatalogTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('hazard_catalog'),'bounded hazard catalog is missing')
        return importlib.import_module('hazard_catalog')

    def rom(self):
        rom=bytearray(4096)
        rom[0xD0A:0xD12]=bytes([1,2,16,32,48,64,80,96])
        rom[0xDC2:0xDD2]=bytes([0,1,2,3,4]+[0]*11)
        rom[0xEE7:0xEEF]=bytes([16,16,32,32,48,48,32,32])
        return rom

    def test_component_domains_keep_cold_modes_and_explicit_partial_status(self):
        api=self.api();rom=self.rom()
        expected={'edge':25132800,'ordinary':4954950,'shore':8294400,'aliases':3203200}
        for kind,count in expected.items():
            plan=api.capture_plan(kind,rom)
            self.assertEqual(plan['expected_cases'],count)
            self.assertTrue(plan['complete_component_domain'])
        edge=api.capture_plan('edge',rom)
        self.assertEqual(len(edge['modes']),264)
        self.assertEqual(edge['modes'][263],{'shape':100,'reflection':True,'nusiz':3})
        subset=api.capture_plan('edge',rom,players=[0,8,159])
        self.assertFalse(subset['complete_component_domain'])
        self.assertEqual(subset['expected_cases'],4435200)
        for players in ([],[0,0],[159,0],[25]):
            with self.assertRaises(ValueError):api.capture_plan('edge',rom,players)

    def test_partition_gaps_overlap_and_missing_cases_cannot_complete(self):
        api=self.api();plan=api.capture_plan('edge',self.rom())
        parts=[{'start':0,'stop':4,'cases':5913600},{'start':4,'stop':8,'cases':5913600},
               {'start':8,'stop':12,'cases':5913600},{'start':12,'stop':17,'cases':7392000}]
        self.assertEqual(api.validate_partitions(parts,plan),25132800)
        for bad in (parts[:-1],[{**parts[0],'stop':5},*parts[1:]],
                    [*parts[:-1],{**parts[-1],'cases':7391999}]):
            with self.assertRaises(ValueError):api.validate_partitions(bad,plan)

    def test_original_fixture_coordinates_and_shore_pose_are_not_interchanged(self):
        api=self.api();rom=self.rom();base=bytes(128)
        edge=api.capture_plan('edge',rom);ram=api.make_case(edge,base,0,53,263,159)
        self.assertEqual(ram[0x23:0x27],bytes([100])*4)
        self.assertEqual(ram[0x58:0x5C],bytes([3])*4)
        self.assertEqual(ram[0x54:0x58],bytes([159])*4)
        self.assertEqual(ram[0x11:0x15],bytes([128])*4)
        ordinary=api.capture_plan('ordinary',rom);ram=api.make_case(ordinary,base,64,53,65,-7)
        self.assertEqual(ram[0x54:0x58],bytes([71])*4)
        self.assertEqual(ram[0x58:0x5C],bytes(4))
        shore=api.capture_plan('shore',rom);ram=api.make_case(shore,base,64,27,5,159)
        self.assertEqual((ram[0x68],ram[0x6F],ram[0x6C]),(159,4,16))
