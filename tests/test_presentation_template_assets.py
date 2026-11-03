"""Repacked descriptors must preserve complete grids and reject bad pointers."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class TemplateAssetTests(unittest.TestCase):
    def test_name_pairs_cover_every_packed_byte_for_all_eight_owners(self):
        api=importlib.import_module('presentation_template_assets')
        data=api.name_pairs()
        self.assertEqual(len(data),4096)
        for owner,(first,water) in enumerate(((25,129),(9,129),(35,130),(19,130),(89,129),(73,129),(99,130),(83,130))):
            for packed in range(256):
                codes=(water,*range(first,first+15))
                self.assertEqual(data[owner*512+packed],codes[packed&15])
                self.assertEqual(data[owner*512+256+packed],codes[packed>>4])

    def test_floe_pool_preserves_whole_masks_with_a_separate_zero_based_id_space(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_template_assets'))
        api=importlib.import_module('presentation_template_assets')
        self.assertTrue(hasattr(api,'floe_pool'))
        patterns=bytes(8)+bytes([17])*8+bytes([34])*8+bytes([51])*8
        compiled={'patterns':4,'template_count':1,'files':{'logical-patterns.bin':patterns,
            'template-index.bin':bytes(2),'template-keys.bin':bytes((0,2,1,0,3,0))}}
        raw,mapping=api.floe_pool(compiled)
        self.assertEqual(raw,bytes([17])*8+bytes([51])*8);self.assertEqual(mapping,{1:0,3:1})
        compiled['files']['template-keys.bin']=bytes((0,2,0,0,3,0))
        with self.assertRaises(ValueError):api.floe_pool(compiled)

    def test_legacy_grid_decoder_keeps_every_pattern_and_checks_indices(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_template_assets'))
        api=importlib.import_module('presentation_template_assets')
        raw=bytearray(16384);raw[256:258]=bytes((1,0))
        meta={'patterns':2,'roots':{'row':[[0,128,3]],'floe':[],'bear':[]},
            'classes':[{'columns':1,'rows':1,'stride':2,'count':1,'offset':256}]}
        records,groups=api.legacy_grids(bytes(raw),meta)
        self.assertEqual(len(records),128);self.assertEqual(records[0],{'columns':1,'rows':1,'patterns':(1,)})
        self.assertEqual(groups['row'][0],list(range(128)));self.assertEqual(groups['floe'],[])
        raw[0:2]=bytes((255,255))
        with self.assertRaises(ValueError):api.legacy_grids(bytes(raw),meta)

    def test_far_root_tail_rejects_collision_and_preserves_root_base_bytes(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_template_assets'))
        api=importlib.import_module('presentation_template_assets')
        payload=bytes([165])*6400
        image=api.seal_shadow(bytes([37])*100,payload)
        self.assertEqual(len(image),229376);self.assertEqual(image[:100],bytes([37])*100)
        self.assertEqual(image[api.SHADOW_OFFSET:],payload)
        with self.assertRaises(ValueError):api.seal_shadow(bytes(api.SHADOW_OFFSET+1),payload)
