import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class NativeCodegenTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('native_codegen'),'native translator missing')
        return importlib.import_module('native_codegen')

    def test_relative_cfg_terminates_and_rejects_indirect_or_unsupported_flow(self):
        api=self.api();rom=bytearray(4096);rom[:5]=bytes([0xA9,0,0xD0,0xFC,0x60])
        flow=api.reachable(bytes(rom),[0xF000],set())
        self.assertEqual(set(flow),{0xF000,0xF002,0xF004});self.assertEqual(flow[0xF002]['target'],0xF000)
        for opcode in (0,0x6C,0x40):
            rom[0]=opcode
            with self.assertRaises(ValueError):api.reachable(bytes(rom),[0xF000],set())

    def test_6507_ram_stack_and_mmio_address_decode(self):
        api=self.api()
        self.assertEqual(api.mapped(0x80),'$C000');self.assertEqual(api.mapped(0x1FF),'$C07F')
        self.assertEqual(api.mapped(0x0C),'$C30C');self.assertEqual(api.mapped(0x0C,write=True),'$C70C')
        self.assertEqual(api.mapped(0x280),'$C340');self.assertEqual(api.mapped(0x282),'$C342')
        self.assertEqual(api.mapped(0xFC00),'original_data+$000')
        with self.assertRaises(ValueError):api.mapped(0xF100)

    def test_generation_is_static_and_identity_checked(self):
        with self.assertRaisesRegex(ValueError,'identity'):self.api().generate(bytes(4096))

    def test_source_call_depth_rejects_recursion_before_using_fast_stack_mapping(self):
        api=self.api();rom=bytearray(4096);rom[:8]=bytes([0x20,0x06,0xF0,0x4C,0x09,0xF0,0xEA,0x60])
        flow=api.reachable(bytes(rom),[0xF000],{0xF009})
        self.assertEqual(api.stack_depth(flow,[0xF000],{0xF009}),1)
        rom[:3]=bytes([0x20,0x00,0xF0]);flow=api.reachable(bytes(rom),[0xF000],{0xF009})
        with self.assertRaisesRegex(ValueError,'depth'):api.stack_depth(flow,[0xF000],{0xF009})

    def test_clear_optimization_requires_exact_zero_and_bounded_ascending_loop(self):
        api=self.api();rom=bytearray(4096);rom[:9]=bytes([0xA9,0,0x95,0,0x9A,0xE8,0xD0,0xFA,0x60])
        flow=api.reachable(bytes(rom),[0xF000],set())
        self.assertEqual(api.clear_patterns(flow),{0xF000:0xF008})
        rom[1]=1;flow=api.reachable(bytes(rom),[0xF000],set())
        self.assertEqual(api.clear_patterns(flow),{})
