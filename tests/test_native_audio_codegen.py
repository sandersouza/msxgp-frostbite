"""Only the explicit audio adapter adds observers to source stores."""
import importlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class NativeAudioCodegenTests(unittest.TestCase):
    def test_direct_aliases_and_unproved_indexed_stores_are_observed(self):
        api=importlib.import_module('native_audio_codegen');facts={'x':frozenset((0,1,2))}
        for op in ('STA','STX','STY'):
            for address in (0x15,0x55,0x115):
                self.assertEqual(api.store_observer({'mnemonic':op,'mode':'zpg','value':address},facts),'p_audio_event_15')
            self.assertIsNone(api.store_observer({'mnemonic':op,'mode':'zpg','value':0x95},facts))
            self.assertIsNone(api.store_observer({'mnemonic':op,'mode':'zpx','value':0x95},facts))
            self.assertEqual(api.store_observer({'mnemonic':op,'mode':'zpx','value':0},facts),'p_audio_event_indexed')
        with self.assertRaises(ValueError):api.store_observer({'mnemonic':'INC','mode':'zpg','value':0x15},facts)

    def test_original_clear_audio_effects_keep_both_alias_passes_and_partial_entries(self):
        api=importlib.import_module('native_audio_codegen')
        self.assertEqual(api.clear_events(0),tuple((reg,0) for _ in range(2) for reg in range(21,27)))
        self.assertEqual(api.clear_events(86),tuple((reg,0) for reg in range(22,27)))
        self.assertEqual(api.clear_events(128),())
        for start in range(256):self.assertEqual(len(api.clear_events(start)),sum(start<=alias+reg for alias in (0,64) for reg in range(21,27)))

    def test_shared_generator_function_is_restored_on_success_and_failure(self):
        api=importlib.import_module('native_audio_codegen');previous=api.native_fast.translate_fast
        with patch.object(api.native_write_loop,'generate',return_value='    call core_clear\n'):
            code=api.generate(bytes(4096))
        self.assertEqual(code,'    call p_audio_core_clear\n');self.assertIs(api.native_fast.translate_fast,previous)
        with patch.object(api.native_write_loop,'generate',side_effect=ValueError('witness')):
            with self.assertRaisesRegex(ValueError,'witness'):api.generate(bytes(4096))
        self.assertIs(api.native_fast.translate_fast,previous)

    def test_clear_effects_match_original_6502_execution_for_every_entry_x(self):
        api=importlib.import_module('native_audio_codegen')
        from py65.devices.mpu6502 import MPU
        class Memory(list):
            def __setitem__(self,address,value):
                super().__setitem__(address,value)
                if getattr(self,'record',False) and type(address)is int and address<128 and 21<=address%64<=26:self.audio.append((address%64,value))
        for start in range(256):
            memory=Memory([0]*65536);memory[512:520]=bytes((0xA9,0,0x95,0,0x9A,0xE8,0xD0,0xFA));memory.audio=[];memory.record=True
            cpu=MPU(memory=memory,pc=512);cpu.x=start;cpu.y=93
            for _ in range(1300):
                cpu.step()
                if cpu.pc==520:break
            else:self.fail('bounded original clear did not terminate')
            self.assertEqual(tuple(memory.audio),api.clear_events(start));self.assertEqual((cpu.a,cpu.x,cpu.y,cpu.sp),(0,0,93,255))
