import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardObserverTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('stella_hazard'),'complete hazard observer is missing')
        return importlib.import_module('stella_hazard')

    def test_partial_wrong_count_and_duplicate_completion_never_certify_windows(self):
        api=self.api();raw=bytearray(674);raw[570:578]=bytes([7])*8
        self.assertEqual(api.validate_observation(raw,'FROSTBITE_HAZARDS_COMPLETE 1\n',1),1)
        for data,log,count in ((raw[:-1],'FROSTBITE_HAZARDS_COMPLETE 1\n',1),
                               (raw,'FROSTBITE_PROBE_COMPLETE 1\n',1),
                               (raw,'FROSTBITE_HAZARDS_COMPLETE 2\n',1),
                               (raw,'FROSTBITE_HAZARDS_COMPLETE 1\n'*2,1),
                               (raw,'FROSTBITE_HAZARDS_COMPLETE 1\n',0)):
            with self.subTest(count=count,log=log):
                with self.assertRaises(ValueError):api.validate_observation(data,log,count)

    def test_controlled_geometry_keeps_count_zero_as_a_real_copy(self):
        api=self.api();base=bytes([23])*128
        ram=api.fixture(base,159,27,0,64,0,True,bear_x=15)
        self.assertEqual(ram[0x66],159)
        self.assertEqual(ram[0x64],27)
        self.assertEqual(ram[0x54:0x58],bytes(4))
        self.assertEqual(ram[0x58:0x5C],bytes(4))
        self.assertEqual(ram[0x23:0x27],bytes([64])*4)
        self.assertEqual(ram[0x11:0x15],bytes([151])*4)
        self.assertEqual(ram[0x68],15)
        self.assertEqual(ram[0x4C],23)  # reserves are never rewritten by geometry setup
        for args in ((160,27,0,64,0,False),(0,256,0,64,0,False),
                     (0,27,160,64,0,False),(0,27,0,249,0,False),(0,27,0,64,4,False)):
            with self.assertRaises(ValueError):api.fixture(base,*args)


if __name__=='__main__':unittest.main()
