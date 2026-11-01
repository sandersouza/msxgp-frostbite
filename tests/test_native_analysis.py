import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class NativeAnalysisTests(unittest.TestCase):
    def analyze(self,code,stop):
        from native_codegen import reachable
        rom=bytes(code)+bytes(4096-len(code));flow=reachable(rom,[0xF000],{stop})
        return importlib.import_module('native_analysis').analyze(flow,(0xF000,),{stop})

    def test_signed_countdown_excludes_wrapped_x_from_indexed_body(self):
        result=self.analyze([0xA2,3,0xB5,0x80,0xCA,0x10,0xFB,0xEA],0xF007)
        self.assertEqual(result[0xF002]['x'],frozenset(range(4)))
        self.assertEqual(result[0xF007]['x'],frozenset({255}))

    def test_decimal_mode_flows_through_real_callee_and_return(self):
        # CLD / JSR sub / ADC#1 / JMP exit / sub:SED ADC#2 CLD RTS
        code=[0xD8,0x20,0x09,0xF0,0x69,1,0x4C,0x0E,0xF0,0xF8,0x69,2,0xD8,0x60]
        result=self.analyze(code,0xF00E)
        self.assertEqual(result[0xF004]['decimal'],frozenset({0}))
        self.assertEqual(result[0xF00A]['decimal'],frozenset({1}))
        self.assertFalse(result[0xF00A]['live_out']&4)  # callee V dies at caller ADC
        self.assertTrue(result[0xF004]['live_out']&4)   # final V is observable

    def test_carry_branch_refines_x_comparison(self):
        # LDX mem / CPX#4 / BCS exit / LDA80,X / JMP exit
        result=self.analyze([0xA6,0x90,0xE0,4,0xB0,5,0xB5,0x80,0x4C,0x0B,0xF0],0xF00B)
        self.assertEqual(result[0xF006]['x'],frozenset(range(4)))
        self.assertEqual(result[0xF006]['carry'],frozenset({0}))

    def test_fast_entry_rejects_unproved_decimal_stack_and_internal_entries(self):
        validate=importlib.import_module('native_fast').validate_entries
        validate([{'start':'F476','registers':{}},{'start':'F000','registers':{'p':255}}])
        for case in ({'start':'F476','registers':{'p':0x38}},{'start':'F476','registers':{'sp':254}},
                     {'start':'FFD0','registers':{}},{'start':'F000','stops':['F00C'],'registers':{}}):
            with self.assertRaises(ValueError):validate([case])
