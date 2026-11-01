import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class NativeContractTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('native_contract'),'native differential contract missing')
        return importlib.import_module('native_contract')

    def test_reference_retains_all_stack_mirror_writes_and_full_cpu_flags(self):
        rom=bytearray(4096);rom[:9]=bytes([0x20,0x06,0xF0,0x4C,0x09,0xF0,0xA9,0x80,0x60])
        case={'id':'stack','start':'F000','stops':['F009'],'ram':{},'registers':{'sp':255,'p':0x31}}
        result=self.api().reference(bytes(rom),case)
        self.assertEqual(result['ram'][126:],[2,240]);self.assertEqual(result['registers'],{'a':128,'x':0,'y':0,'p':177,'sp':255})

    def test_comparison_rejects_flag_stack_and_unwatched_ram_corruption(self):
        api=self.api();expected={'ram':[0]*128,'registers':{'a':0,'x':0,'y':0,'p':32,'sp':255}}
        api.compare(expected,expected)
        for offset in (0,42,127):
            actual={'ram':expected['ram'].copy(),'registers':expected['registers'].copy()};actual['ram'][offset]=1
            with self.assertRaises(ValueError):api.compare(expected,actual)
        actual={'ram':expected['ram'].copy(),'registers':{**expected['registers'],'p':96}}
        with self.assertRaises(ValueError):api.compare(expected,actual)

    def test_fast_native_stack_abi_rejects_unproved_hardware_stack_wrap(self):
        api=self.api()
        api.validate_entry({'sp':0x86});api.validate_entry({'sp':255})
        for sp in (0,127,128,133,256):
            with self.assertRaises(ValueError):api.validate_entry({'sp':sp})

    def test_chain_environment_changes_only_named_source_contact_inputs(self):
        api=self.api();ram=bytearray(range(128));ram[0xE4-128]=53;ram[0xEA-128]=0
        result=api.contact_environment(bytes(ram))
        self.assertEqual(result[0xB6-128],128)
        self.assertEqual(result[0xB8-128:0xBA-128],b'\xff\xff')
        changed={i for i,(a,b) in enumerate(zip(ram,result)) if a!=b}
        self.assertTrue(changed<=set(range(0xB0-128,0xBA-128))|{0xED-128})

    def test_incomplete_or_unsafe_native_receipt_is_rejected(self):
        api=self.api();receipt={'complete':True,'cases':2,'stack_min':0xF370,'heap_guard':True,'clock_hz':3579545,'ram_bytes':65536}
        api.validate_receipt(receipt,2)
        for key,value in [('complete',False),('cases',1),('stack_min',0xF33F),('heap_guard',False),('clock_hz',7000000)]:
            with self.assertRaises(ValueError):api.validate_receipt({**receipt,key:value},2)
