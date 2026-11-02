"""Integrated dirty histories and physical names must agree with the host."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class DirtyAuditTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_dirty_audit'),'integrated dirty audit missing')
        return importlib.import_module('presentation_dirty_audit')

    def test_whole_state_flags_and_page_alternation_are_required(self):
        api=self.api();ram=bytes(128);rng=bytes(256)
        histories=[None,None]
        state=api.scene(ram,rng)
        raw=state+bytes((255,255,255,0,0,0))
        self.assertEqual(api.audit_scene(raw,ram,rng,histories,0),24)
        self.assertEqual(histories,[state,None])
        with self.assertRaises(ValueError):api.audit_scene(raw,ram,rng,histories,1)
        raw=state+bytes((0,0,0,0,0,0))
        self.assertEqual(api.audit_scene(raw,ram,rng,histories,0),0)
        for at in (0,3,52,64,65,66,67,68,69):
            bad=bytearray(raw);bad[at]^=1
            with self.assertRaises(ValueError):api.audit_scene(bad,ram,rng,histories,0)
        with self.assertRaises(ValueError):api.audit_scene(raw[:-1],ram,rng,histories,0)

    def test_boot_only_the_prepared_generation_is_valid(self):
        api=self.api();ram=bytes(128);rng=bytes(256);state=api.scene(ram,rng)
        boot=ram+bytes(64)+state+bytes((1,0,0))
        self.assertEqual(api.boot_histories(boot,rng),[None,state])
        for at in (128,192,256,257):
            bad=bytearray(boot);bad[at]^=1
            with self.assertRaises(ValueError):api.boot_histories(bad,rng)

    def test_both_physical_pages_must_match_intended_names(self):
        api=self.api();vram=bytearray(16384);names=bytes([128])*1536
        vram[0x1800:0x1B00]=names[:768];vram[0x1C00:0x1F00]=names[768:]
        api.audit_physical_names(vram,names)
        for at in (0x1800,0x1AFF,0x1C00,0x1EFF):
            bad=vram.copy();bad[at]^=1
            with self.assertRaises(ValueError):api.audit_physical_names(bad,names)
        with self.assertRaises(ValueError):api.audit_physical_names(vram[:-1],names)
