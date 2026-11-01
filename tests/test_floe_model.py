import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class FloeModelTests(unittest.TestCase):
    def test_exact_bits_clip_edges_and_vertical_windows(self):
        overlap=importlib.import_module('floe_model').overlap
        rows=[bytes([0x80])+bytes(18)+bytes([1])]
        self.assertTrue(overlap(bytes([0x80]),0,10,rows,10))
        self.assertTrue(overlap(bytes([1]),152,10,rows,10))
        self.assertFalse(overlap(bytes([0x40]),0,10,rows,10))
        self.assertFalse(overlap(bytes([0x80]),-1,10,rows,10))
        self.assertFalse(overlap(bytes([0x80]),160,10,rows,10))
        self.assertFalse(overlap(bytes([0x80]),0,9,rows,10))
        self.assertFalse(overlap(bytes([0]),0,10,rows,10))

    def test_player_rows_use_source_plane_shift_and_reflection(self):
        player=importlib.import_module('floe_model').player_rows
        rom=bytearray(4096);rom[0xCAA]=0x20;rom[0xC20:0xC20+19]=bytes(range(19))
        ram=bytearray(128)
        self.assertEqual(player(rom,ram),bytes(range(19))[::-1])
        ram[0x6C]=8
        self.assertEqual(player(rom,ram),bytes(int(f'{v:08b}'[::-1],2) for v in range(19))[::-1])
        ram[0x6B]=1;ram[0x6C]=0
        self.assertEqual(player(rom,ram),b'\0'+bytes(range(1,19))[::-1])

    def test_visible_effects_preserve_unowned_ram_and_sticky_contact(self):
        visible=importlib.import_module('floe_model').visible_state
        rom=bytearray(4096);rom[0xF88:0xF90]=bytes(range(8))
        ram=bytearray((i*37+11)&255 for i in range(128))
        ram[0x45]=0;ram[0x46]=15;ram[0x4B]=7;ram[0x4D]=15;ram[1]=0;ram[2]=0
        out=visible(rom,ram,{'p':0x34,'sp':255},{'rows':bytes([7,7,7,7,7,7,135,7]),'shore':7})
        self.assertEqual(out['registers'],{'a':0,'x':3,'y':2,'p':0xB5,'sp':255})
        result=out['ram'];self.assertEqual(result[0x30:0x38],bytes([7,7,7,7,7,7,135,7]))
        self.assertEqual(result[0x6D],ram[0x6D])
        self.assertEqual(result[0x3B:0x3F],bytes([128,2,12,56]))
        written=set(range(5,17))|set(range(0x30,0x3F))|{0x78,0x79,0x7A,0x7E,0x7F}
        for i in range(128):
            if i not in written:self.assertEqual(result[i],ram[i],hex(i+128))
        hit=visible(rom,ram,{'p':0x34,'sp':255},{'rows':bytes([7])*8,'shore':135})
        self.assertEqual(hit['ram'][0x6D],135)

    def test_attract_and_illegal_phase_inputs_are_explicit(self):
        visible=importlib.import_module('floe_model').visible_state
        rom=bytearray(4096);ram=bytearray(128);ram[0x45]=128;ram[0x4D]=14;ram[0x1E]=9
        out=visible(rom,ram,{'p':0x30,'sp':255},{'rows':bytes([7])*8,'shore':7})
        self.assertEqual((out['ram'][0x1E],out['ram'][0x53]),(0,14))
        for regs,contacts in [({'p':0x38,'sp':255},{'rows':bytes([7])*8,'shore':7}),
                              ({'p':0x30,'sp':254},{'rows':bytes([7])*8,'shore':7}),
                              ({'p':0x30,'sp':255},{'rows':b'','shore':7})]:
            with self.assertRaises(ValueError):visible(rom,ram,regs,contacts)

    def test_completed_day_door_uses_zero_before_night_flashing(self):
        visible=importlib.import_module('floe_model').visible_state
        ram=bytearray(128);ram[0x4D]=15
        out=visible(bytearray(4096),ram,{'p':0x30,'sp':255},{'rows':bytes([7])*8,'shore':7})
        self.assertEqual(out['ram'][0x3E],0)

    def test_generic_cyclic_mask_is_distinct_from_clipped_actor(self):
        overlap=importlib.import_module('floe_model').overlap
        rows=[bytes([0x80])+bytes(19)]
        self.assertTrue(overlap(bytes([0xFF]),159,10,rows,10,wrap=True))
        self.assertFalse(overlap(bytes([0xFF]),159,10,rows,10,wrap=False))

    def test_actor_pixels_past_159_do_not_wrap_into_next_scanline(self):
        contacts=importlib.import_module('floe_model').floe_contacts
        rom=bytearray(4096);rom[0xCAA]=0x20;rom[0xC20]=255
        ram=bytearray(128);ram[0x64]=50;ram[0x66]=159
        catalog={(0,0,0):(bytes([128])+bytes(19),)*7}
        self.assertEqual(contacts(rom,ram,catalog),bytes([7])*8)

    def test_hidden_mask_recovery_requires_all_positions_and_exact_visible_translation(self):
        recover=importlib.import_module('floe_model').recover_masks
        observed={}
        for x in range(160):
            row=bytearray(20);row[x//8]|=128>>(x%8);row[0]=0
            observed[(0,0,x)]=(bytes(row),)*7
        result=recover(observed)
        self.assertEqual(result[(0,0,0)][0],bytes([128])+bytes(19))
        missing=dict(observed);missing.pop((0,0,159))
        with self.assertRaises(ValueError):recover(missing)
        changed=dict(observed);changed[(0,0,100)]=(bytes(20),)*7
        with self.assertRaises(ValueError):recover(changed)

    def test_phase_fixture_uses_explicit_decimal_values_and_full_ram(self):
        commands=importlib.import_module('floe_probes').ram_commands
        ram=bytes(range(128));self.assertEqual(commands(ram)[30],'ram #158 #30')
        self.assertEqual(len(commands(ram)),128)
        with self.assertRaises(ValueError):commands(b'')
