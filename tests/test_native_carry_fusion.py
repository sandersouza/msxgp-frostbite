import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
class CarryFusionTests(unittest.TestCase):
    def graph(self,live=0):
        a=(0xF100,());b=(0xF102,());fall=(0xF104,());taken=(0xF108,())
        ins={a[0]:{'mnemonic':'CMP','size':2},b[0]:{'mnemonic':'BCS','size':2,'target':taken[0]}}
        facts={a:{'successors':[b],'live_out':8,'decimal':frozenset({0})},b:{'successors':[fall,taken],'live_out':live},fall:{'successors':[]},taken:{'successors':[]}}
        return a,b,ins,facts
    def test_dead_carry_can_be_elided_but_observed_carry_is_retained(self):
        api=importlib.import_module('native_fast');a,b,ins,facts=self.graph()
        branches,drops=api.carry_fusions(ins,facts)
        self.assertEqual(branches[b],'nc');self.assertIn(a,drops)
        a,b,ins,facts=self.graph(8);branches,drops=api.carry_fusions(ins,facts)
        self.assertEqual(branches[b],'nc');self.assertNotIn(a,drops)
    def test_alternate_entry_and_decimal_arithmetic_cannot_reuse_raw_carry(self):
        api=importlib.import_module('native_fast');a,b,ins,facts=self.graph()
        facts[(0xF120,())]={'successors':[b]}
        self.assertEqual(api.carry_fusions(ins,facts),({},set()))
        a,b,ins,facts=self.graph();ins[a[0]]['mnemonic']='ADC';facts[a]['decimal']=frozenset({1})
        self.assertEqual(api.carry_fusions(ins,facts),({},set()))
