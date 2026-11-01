import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardMechanicsTests(unittest.TestCase):
    def test_effect_gate_requires_real_contact_and_one_fish_segment(self):
        api=importlib.import_module('hazard_mechanics');before=bytearray(128);before[0x5F]=7
        after=bytearray(before);after[0x5F]=6;after[0x77]=1;after[0x74]=91;after[0x67]=16
        contacts={'rows':bytes([7]*7+[135]),'shore':7}
        api.validate_effect('fish',before,after,contacts,3)
        for bad in (bytearray(before),bytearray(after)):
            bad[0x5F]=1
            with self.assertRaises(ValueError):api.validate_effect('fish',before,bad,contacts,3)
        with self.assertRaises(ValueError):api.validate_effect('fish',before,after,{'rows':bytes([7]*8),'shore':7},3)

    def test_airborne_contact_must_not_attach_or_collect(self):
        api=importlib.import_module('hazard_mechanics');before=bytearray(128);before[0x72]=255;before[0x6A]=1
        after=bytearray(before);contacts={'rows':bytes([7]*7+[135]),'shore':7}
        api.validate_effect('airborne',before,after,contacts,3)
        after[0x72]=3
        with self.assertRaises(ValueError):api.validate_effect('airborne',before,after,contacts,3)

    def test_threat_gate_requires_attachment_to_the_actual_contact_row(self):
        api=importlib.import_module('hazard_mechanics');before=bytearray(128);after=bytearray(before);after[0x72]=2
        contacts={'rows':bytes([7]*5+[135,7,7]),'shore':7}
        api.validate_effect('threat',before,after,contacts,2)
        with self.assertRaises(ValueError):api.validate_effect('threat',before,after,contacts,3)

    def test_water_and_temperature_boundary_gates_keep_distinct_causes(self):
        api=importlib.import_module('hazard_mechanics');before=bytearray(128);before[0x64]=79;before[0x65]=1
        water=bytearray(before);water[0x71]=128;temp=bytearray(before);temp[0x65]=0;temp[0x71]=16
        contacts={'rows':bytes([7]*8),'shore':7}
        api.validate_effect('water',before,water,contacts,3)
        api.validate_effect('temperature',before,temp,contacts,3)
        with self.assertRaises(ValueError):api.validate_effect('temperature',before,water,contacts,3)
        with self.assertRaises(ValueError):api.validate_effect('water',before,temp,contacts,3)
