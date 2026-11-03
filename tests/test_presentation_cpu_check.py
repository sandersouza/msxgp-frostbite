"""Presentation ROM CPU evidence cannot inherit old cartridge acceptance."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PresentationCpuCheckTests(unittest.TestCase):
    def test_only_declared_audio_workspace_is_excluded_from_cpu_guard(self):
        api=importlib.import_module('presentation_cpu_check')
        from presentation_build import profile
        self.assertEqual(api.guard_spans({'profile':profile()}),((0xD000,0x2300),))
        metadata={'profile':profile(audio=True)}
        self.assertEqual(api.guard_spans(metadata),((0xD000,0x1000),(0xE020,0x12E0)))
        metadata['profile']['ram']['regions']=[r for r in metadata['profile']['ram']['regions'] if r['name']!='audio_observation']
        with self.assertRaises(ValueError):api.guard_spans(metadata)

    def test_whole_cpu_ram_capture_and_fatal_logs_are_required(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_cpu_check'))
        api=importlib.import_module('presentation_cpu_check')
        registers=dict(zip(('a','x','y','p','sp'),(0,1,2,32,255)))
        expected=[{'registers':registers,'ram':[0]*128}]
        actual=bytes((0,1,2,32,255))+bytes(128)+(123).to_bytes(4,'little')
        api.verify_capture(actual,expected,'')
        for blob,log in ((actual[:-1],''),(actual,'FLOE_NATIVE_FAIL guard'),(bytes((1,))+actual[1:],'')):
            with self.assertRaises(ValueError):api.verify_capture(blob,expected,log)
