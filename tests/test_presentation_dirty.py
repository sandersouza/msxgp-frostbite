"""Dirty rows follow visible source dependencies, never timer-byte churn."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PresentationDirtyTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_dirty'),'normalized dirty-row model missing')
        return importlib.import_module('presentation_dirty')

    def ram(self):
        ram=bytearray(128);ram[0x68]=60;ram[0x46]=12
        for i in range(4):ram[0x1F+i]=40+i*7
        return ram

    def test_first_page_blank_and_coarse_transitions_rebuild_all_rows(self):
        api=self.api();ram=self.ram();one=api.scene(ram,bytes(256));self.assertEqual(len(one),64)
        self.assertEqual(api.dirty_rows(None,one),set(range(24)))
        blank=ram.copy();blank[0x3F]=128;b=api.scene(blank,bytes(256))
        self.assertEqual(api.dirty_rows(one,b),set(range(24)));self.assertEqual(api.dirty_rows(b,one),set(range(24)))
        coarse=ram.copy();coarse[0x68]=150
        self.assertEqual(api.dirty_rows(one,api.scene(coarse,bytes(256))),set(range(24)))

    def test_unrelated_source_timers_and_player_sprite_changes_do_not_dirty_background(self):
        api=self.api();ram=self.ram();one=api.scene(ram,bytes(256))
        for address in (0,2,3,0x64,0x66,0x6B,0x6E,0x70):
            changed=ram.copy();changed[address]^=1
            self.assertEqual(api.dirty_rows(one,api.scene(changed,bytes(256))),set())
        changed=ram.copy();changed[1]=1
        self.assertEqual(api.dirty_rows(one,api.scene(changed,bytes(256))),set())

    def test_compensated_floe_motion_preserves_pixels_and_needs_no_background_rebuild(self):
        api=self.api();ram=self.ram();ram[0x1C]=64;ram[0x1D]=0;one=api.scene(ram,bytes(256))
        changed=ram.copy();changed[0x1C]=80;changed[0x1D]=16
        for i in range(4):changed[0x1F+i]+=1
        self.assertEqual(api.scene(changed,bytes(256)),one)
        self.assertEqual(api.dirty_rows(one,api.scene(changed,bytes(256))),set())

    def test_shared_world_rows_are_rebuilt_when_either_contributor_changes(self):
        api=self.api();ram=self.ram();one=api.scene(ram,bytes(256))
        for address,rows in ((0x54,{19,20}),(0x55,{15,16}),(0x56,{12,13}),(0x57,{9,10}),
                             (0x1F,{20,21}),(0x20,{17,18}),(0x21,{14,15}),(0x22,{11})):
            changed=ram.copy();changed[address]+=1
            self.assertEqual(api.dirty_rows(one,api.scene(changed,bytes(256))),rows)

    def test_header_igloo_and_footer_invalidation_is_confined_to_owned_rows(self):
        api=self.api();ram=self.ram();one=api.scene(ram,bytes(256))
        for address,rows in ((0x48,{0,1,2}),(0x44,{3}),(0x43,{4}),(0x42,{4}),(0x41,{5}),(0x40,{5}),(0x46,{22,23})):
            changed=ram.copy();changed[address]+=1
            self.assertEqual(api.dirty_rows(one,api.scene(changed,bytes(256))),rows)
        changed=ram.copy();changed[0x46]=44
        self.assertEqual(api.dirty_rows(one,api.scene(changed,bytes(256))),set())

    def test_night_gradient_and_diagnostic_flags_have_explicit_row_scope(self):
        api=self.api();ram=self.ram();rng=bytes(i%8 for i in range(256));one=api.scene(ram,rng)
        changed=ram.copy();changed[2]=1
        self.assertEqual(api.dirty_rows(one,api.scene(changed,rng)),{3})
        changed=ram.copy();changed[0x45]=128
        self.assertEqual(api.dirty_rows(one,api.scene(changed,rng)),set(range(9)))
        self.assertEqual(api.dirty_rows(one,api.scene(ram,rng,layout=1)),set(range(24)))
