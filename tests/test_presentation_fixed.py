"""Fixed primitive roles must fit one64-slot generation of every bank."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class FixedPresentationTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fixed'),'fixed primitive-slot proof missing')
        return importlib.import_module('presentation_fixed')

    def test_world_and_ui_roles_never_alias_within_either_coarse_mode(self):
        api=self.api();self.assertEqual(api.COUNTS,(56,60,50))
        for coarse in (0,1):
            occupied=set()
            def reserve(pair):
                bank,slot=pair
                self.assertTrue(0<=slot<api.COUNTS[bank]);self.assertNotIn(pair,occupied);occupied.add(pair)
            for shape_row in range(3):
                for column in range(4):reserve(api.world_slot('bear',0,shape_row,column,coarse))
            for row in range(4):
                object_rows=((153-row*26+coarse)%8+15)//8
                for shape_row in range(object_rows):
                    for column in range(3):reserve(api.world_slot('object',row,shape_row,column,coarse))
                for index in range(16):reserve(api.floe_slot(row,index))
            for row in range(3):
                for column in range(5,15):reserve(api.header_slot(row,column))
            for row in range(3,6):
                for column in range(22,28):reserve(api.igloo_slot(row,column))
            for row in ((12,) if coarse else (15,20)):
                for copy in range(3):
                    for column in range(3):reserve(api.fused_slot(row,copy,column,coarse))

    def test_footer_codes_have_disjoint_generations_outside_dynamic_and_background_codes(self):
        api=self.api();ids=[]
        for page in (0,1):
            for index in range(22):
                identifier=api.footer_name(page,index)
                self.assertTrue(160<=identifier<=203);ids.append(identifier)
        self.assertEqual(len(set(ids)),44)

    def test_floe_copies_remain_separated_on_each_scanline_for_all_roots_and_signed_motion_deltas(self):
        # The minimum inter-copy gap is five Atari pixels. At3/2 scaling
        # their drawn pixels are at least eight MSX pixels apart on one line.
        # Slanted rows CAN share an8-row tile; the local16-key pool handles it.
        self.api()
        for root in range(160):
            for delta in range(-11,20):
                owners={}
                for copy,offset in enumerate((0,32,64)):
                    for plane in (0,delta):
                        for bit in range(8):
                            x=(root+offset+plane+bit)%160
                            for pixel in range(8+x*3//2,8+(x+1)*3//2):
                                column=pixel//8
                                self.assertIn(owners.get(column,copy),(copy,))
                                owners[column]=copy

    def test_floe_pool_compares_whole_keys_and_rejects_capacity_before_publishing(self):
        api=self.api();pool={}
        for index in range(16):self.assertEqual(api.intern_floe(pool,bytes((index,0,130,0,15,0))),index)
        self.assertEqual(api.intern_floe(pool,bytes((5,0,130,0,15,0))),5)
        before=dict(pool)
        with self.assertRaises(ValueError):api.intern_floe(pool,bytes((5,0,130,0,14,0)))
        self.assertEqual(pool,before)

    def test_role_boundaries_and_inapplicable_fusions_are_rejected(self):
        api=self.api()
        cases=(('object',4,0,0,0,None),('bear',0,3,0,0,None),('bear',0,0,4,0,None),
            ('floe',0,1,0,1,None),('floe',0,0,4,0,1),('object',1,1,0,1,None),
            ('object',0,0,0,2,None),('unknown',0,0,0,0,None))
        for args in cases:
            with self.assertRaises(ValueError):api.world_slot(*args)
        for args in ((20,0,0,1),(12,0,0,0),(15,0,0,1),(15,3,0,0)):
            with self.assertRaises(ValueError):api.fused_slot(*args)
        for args in ((4,0),(0,16)):
            with self.assertRaises(ValueError):api.floe_slot(*args)

    def test_one_physical_slot_cannot_publish_two_different_tiles_in_the_same_frame(self):
        api=self.api();slots={}
        api.retain(slots,(1,5),bytes(16));api.retain(slots,(1,5),bytes(16))
        with self.assertRaises(ValueError):api.retain(slots,(1,5),bytes([1])*16)
