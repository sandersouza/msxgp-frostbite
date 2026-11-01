import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class NativeShiftTests(unittest.TestCase):
    def test_dead_carry_and_direct_ram_shift_avoid_unobservable_flag_work(self):
        api=importlib.import_module('native_shifts')
        self.assertEqual(api.compact_shift({'mnemonic':'ASL','mode':'acc','value':0},{'live_out':3}),['add a,a'])
        self.assertEqual(api.compact_shift({'mnemonic':'LSR','mode':'zpg','value':0x82},{'live_out':3}),['ld hl,$C002','srl (hl)'])
        self.assertEqual(api.compact_shift({'mnemonic':'ROL','mode':'acc','value':0},{'live_out':0}),['srl e','rl a'])

    def test_observed_flags_are_retained_and_hardware_aliases_stay_on_original_path(self):
        api=importlib.import_module('native_shifts');item={'mnemonic':'ASL','mode':'acc','value':0}
        code=api.compact_shift(item,{'live_out':11});self.assertIn('jr nc,$+4',code)
        self.assertEqual(api.compact_shift(item,{'live_out':8})[-2:],['ld e,0','rl e'])
        self.assertIsNone(api.compact_shift({'mnemonic':'ROL','mode':'zpg','value':12},{'live_out':15}))
        self.assertIsNone(api.compact_shift({'mnemonic':'ROR','mode':'zpx','value':0x82},{'live_out':15}))

    def test_dead_transfer_flags_and_dead_compare_carry_keep_the_original_operand_path(self):
        api=importlib.import_module('native_shifts')
        code=['ld b,a','or a','ld l,b','ld h,$C0','push hl','pop iy']
        self.assertEqual(api.compact_flags({'mnemonic':'TAX'},{'live_out':0},code),code[:1]+code[2:])
        self.assertEqual(api.compact_flags({'mnemonic':'TAX'},{'live_out':2},code),code)
        code=['ld h,$05','ld d,a','ld a,b','cp h','ld e,0','jr c,$+4','ld e,1','ld a,d']
        self.assertEqual(api.compact_flags({'mnemonic':'CPX'},{'live_out':2},code),code[:4]+code[7:])
        self.assertEqual(api.compact_flags({'mnemonic':'CPX'},{'live_out':10},code),code)
