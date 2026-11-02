"""Template identities preserve the original row/colour sequence under translation."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PlayerTemplateTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_player_cache'),'safe player-template policy missing')
        return importlib.import_module('presentation_player_cache')

    def test_template_key_rejects_prefix_tail_races_and_vertical_clipping(self):
        api=self.api();holds=bytes(int(y in (80,81,92,93,106,107,118,119,132,133,144,145,158,159,170,171)) for y in range(47,182))
        ram=bytearray(128);ram[0x64]=60;ram[0x66]=32
        self.assertEqual(len(api.template_key(ram,holds)),7)
        for y,x in ((29,32),(134,32),(60,84),(60,159)):
            ram[0x64]=y;ram[0x66]=x;self.assertIsNone(api.template_key(ram,holds))
        ram[0x64]=60;ram[0x66]=32;one=api.template_key(ram,holds)
        for offset,mask in ((0x6E,1),(0x6B,1),(0x70,1),(0x6C,8),(0x66,1)):
            changed=ram.copy();changed[offset]^=mask
            self.assertNotEqual(api.template_key(changed,holds),one)

    def test_matching_keys_have_identical_relative_pixels_in_independent_general_kernel(self):
        api=self.api()
        from presentation_model import player
        from presentation_sprites import tables,expand_pair
        rom=bytearray((i*37+11)&255 for i in range(4096));rom[0xCAA:0xCB6]=bytes((0x10,0x40,0x80,0xA0,0xC0,0xE0))*2
        holds=tables(bytes(rom),{c:(0,0,0) for c in range(0,256,2)})['holds'];seen={}
        for y in range(30,134):
            for x in range(84):
                ram=bytearray(128);ram[0x64]=y;ram[0x66]=x;ram[0x6B]=13;ram[0x70]=24;ram[0x6C]=8
                key=api.template_key(ram,holds);description=player(bytes(rom),bytes(ram));points=[]
                for row in description['rows']:
                    for dx in range(8):
                        if x+dx<8:continue
                        pattern=row['prefix_pattern'] if x+dx<row['update_x'] else row['pattern']
                        color=row['prefix_color'] if x+dx<row['color_update_x'] else row['color']
                        if x+dx>=row['suffix_x']:color=row['suffix_color']
                        if pattern&(1<<dx):
                            mask=expand_pair(128>>dx,x&1)
                            points.append((row['y']-y,mask,color))
                signature=tuple(points)
                if key in seen:self.assertEqual(signature,seen[key])
                else:seen[key]=signature

    def test_ram_manifest_owns_template_cache_outside_source_bus_shadows(self):
        from presentation_build import profile
        regions={row['name']:(row['start'],row['end']) for row in profile()['ram']['regions']}
        self.assertEqual(regions.get('player_templates'),(0xC380,0xC3C0))
        self.assertEqual(regions.get('source_io_read'),(0xC300,0xC348))
