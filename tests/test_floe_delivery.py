import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
class FloeDeliveryTests(unittest.TestCase):
    def test_unverified_dirty_or_wrong_binary_cannot_be_packaged(self):
        api=importlib.import_module('floe_delivery');sha='a'*64
        good={'complete':True,'exploratory':False,'rom':{'sha256':sha},'cases':1368,'canonical_ram_injections':1368}
        api.validate_positive('geometry',good,sha)
        with self.assertRaises(ValueError):api.validate_positive('geometry',{key:value for key,value in good.items() if key!='complete'},sha)
        for change in ({'complete':False},{'exploratory':True},{'cases':1367},{'rom':{'sha256':'b'*64}}):
            with self.assertRaises(ValueError):api.validate_positive('geometry',{**good,**change},sha)
    def test_paced_gate_requires_real_cadence_pixels_and_no_injections(self):
        api=importlib.import_module('floe_delivery');sha='a'*64
        good={'complete':True,'exploratory':False,'rom':{'sha256':sha},'source_steps':2254,'frames':1886,'pixel_errors':0,
              'canonical_ram_injections':0,'max_busy_cycles':70000,'frame_budget':71364,'min_margin_cycles':1364}
        api.validate_positive('paced-pal',good,sha)
        for change in ({'frames':1885},{'canonical_ram_injections':1},{'pixel_errors':1},{'max_busy_cycles':71364},{'min_margin_cycles':0}):
            with self.assertRaises(ValueError):api.validate_positive('paced-pal',{**good,**change},sha)
