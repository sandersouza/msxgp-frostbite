"""Finite templates must retain hidden-edge cells until translation/clipping."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class FloeTemplateTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_floe_templates'))
        return importlib.import_module('presentation_floe_templates')

    def test_half_dictionary_roundtrips_all_pattern_bytes_and_rejects_bad_indices(self):
        api=self.api();patterns=[bytes(8),bytes(range(8)),bytes(range(4))+bytes(4)]
        pairs,halves=api.pack_patterns(patterns)
        self.assertEqual(len(pairs),12)
        for index,pattern in enumerate(patterns):self.assertEqual(api.read_pattern(pairs,halves,index),pattern)
        for index in (-1,3):
            with self.assertRaises(ValueError):api.read_pattern(pairs,halves,index)
        with self.assertRaises(ValueError):api.read_pattern(bytes((255,255))+pairs[2:],halves,0)
        with self.assertRaises(ValueError):api.pack_patterns([bytes(7)])

    def test_world_translation_happens_before_left_edge_clipping(self):
        api=self.api();program=bytearray(60);program[0]=1;program[29]=2;program[31]=1
        packed=api.pack_program(program)
        self.assertEqual(len(packed),30)
        self.assertEqual(api.cells(packed,[257,513],0,88),{(11,30):513,(12,2):257})
        self.assertEqual(api.cells(packed,[257,513],16,88),{(11,4):257,(11,3):513,(12,5):257})
        with self.assertRaises(ValueError):api.cells(packed,[257],0,88)
        with self.assertRaises(ValueError):api.cells(packed,[257,513],160,88)
        program[0]=15
        with self.assertRaises(ValueError):api.pack_program(program)
