import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class MovementBuildTests(unittest.TestCase):
    def test_scene_reverses_logical_rows_without_changing_canonical_state(self):
        api=importlib.import_module('movement_build');ram=bytearray(128)
        ram[31:35]=bytes((10,20,30,40));ram[84:88]=bytes((11,21,31,41))
        ram[100]=53;ram[102]=159;ram[104]=180
        before=bytes(ram);scene=api.presentation(before,1,0)
        self.assertEqual(scene['floes'],[40,30,20,10]);self.assertEqual(scene['threats'],[41,31,21,11])
        self.assertEqual((scene['player_x'],scene['player_y'],scene['bear_x']),(159,74,151))
        self.assertEqual(bytes(ram),before)

    def test_ascii16_rom_contract_rejects_bad_size_header_and_vectors(self):
        api=importlib.import_module('movement_build');data=bytearray([255])*262144
        data[:20]=b'AB\x14\x40'+bytes(12)+b'FBM0'
        self.assertEqual(api.validate_rom(bytes(data)),[])
        self.assertTrue(api.validate_rom(bytes(data[:32768])))
        data[3]=0x80;self.assertTrue(api.validate_rom(bytes(data)))

    def test_paced_receipt_rejects_skipped_frames_wrong_steps_and_unsafe_work(self):
        api=importlib.import_module('movement_bench');period=59736
        receipt={'complete':True,'cases':240,'frames':list(range(240)),'busy_cycles':[50000]*240,
            'commit_y':[-20]*240,'commit_end_y':[-15]*240,'commit_cycles':[1500]*240,'period_cycles':[period]*240,
            'step_counts':list(range(1,241)),'mode_samples':[0]*240,'pal_flag':0,'source_steps':241,
            'source_cycles':[20000]*241,'min_spacing':29,'max_sprites_per_line':4,'stack_min':0xF370}
        api.validate_receipt(receipt,period,0,0,False)
        for key,value in [('frames',list(range(239))+[240]),('busy_cycles',[60000]*240),('step_counts',[1]*240),
                          ('commit_y',[30]*240),('min_spacing',28),('source_steps',240),('mode_samples',[1]*240)]:
            with self.assertRaises(ValueError,msg=key):api.validate_receipt({**receipt,key:value},period,0,0,False)
