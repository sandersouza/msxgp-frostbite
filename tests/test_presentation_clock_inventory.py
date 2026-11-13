"""Only emitted instructions, with explicit bank provenance, are patchable."""
import importlib
import importlib.util
from collections import Counter
from environment import ROOT
import unittest


def api():
    if importlib.util.find_spec('presentation_clock_inventory') is None:
        return None
    return importlib.import_module('presentation_clock_inventory')


class ClockInventoryTests(unittest.TestCase):
    def test_listing_tracks_nested_sources_banks_and_skips_data_and_inactive_lines(self):
        module = api()
        self.assertIsNotNone(module, 'listing inventory producer is missing')
        listing = '''# file opened: movement.asm
   1  0000                  ORG $4000
   2  4010 32 00 70         LD ($7000),A
   3  4013 32 00 70         DB $32,$00,$70
# file opened: presentation_world.asm
   4+ 4016 3A 64 C0         LD A,($C064)
   5+ 4019 ~                LD A,($C065)
# file closed: presentation_world.asm
   6  8000                  ORG $8000
   7  8000 32 00 70         DB $32,$00,$70
   8  C000                  ORG $8000
# file opened: native_cpu.asm
   1+ 8000 32 00 70         LD ($7000),A
   2+ 8003 3A 64 C0         LD A,($C064)
# file closed: native_cpu.asm
# file closed: movement.asm
'''
        rows = module.parse_listing(listing, layout='f')
        self.assertEqual([(r['bank'], r['address'], r['source']) for r in rows],
                         [(0, 0x4010, 'movement.asm'), (0, 0x4016, 'presentation_world.asm'),
                          (2, 0x8000, 'native_cpu.asm'), (2, 0x8003, 'native_cpu.asm')])
        patches = [module.classify_instruction(r) for r in rows]
        self.assertEqual([p['kind'] if p else None for p in patches], ['mapper', 'snapshot', 'mapper', None])
        self.assertEqual(patches[1]['after'], '3a64f0')

    def test_snapshot_operand_forms_exclude_metadata_and_immediate_colour(self):
        module = api()
        self.assertIsNotNone(module, 'listing inventory producer is missing')
        cases = [('3a00c0', 'LD A,($C000)', '3a00f0'),
                 ('217fc0', 'LD HL,$C07F', '217ff0'),
                 ('ed5b23c0', 'LD DE,($C023)', 'ed5b23f0'),
                 ('dd2123c0', 'LD IX,$C023', 'dd2123f0'),
                 ('fd2a23c0', 'LD IY,($C023)', 'fd2a23f0'),
                 ('26c0', 'LD H,$C0', '26f0'),
                 ('3ec0', 'LD A,$C0', None),
                 ('2180c0', 'LD HL,$C080', None),
                 ('3264c0', 'LD ($C064),A', None)]
        for raw, assembly, after in cases:
            row = dict(bank=0, address=0x4100, offset=0x100, source='presentation_world.asm',
                       line=1, before=raw, assembly=assembly)
            patch = module.classify_instruction(row)
            self.assertEqual(patch['after'] if patch else None, after, assembly)
        row.update(source='presentation_audio.asm', before='3a64c0', assembly='LD A,($C064)')
        self.assertIsNone(module.classify_instruction(row))
        row.update(source='core.inc')
        self.assertIsNone(module.classify_instruction(row))

    def test_later_patch_ownership_excludes_old_instruction_even_when_bytes_coincide(self):
        module = api()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'validate_instructions'), 'final instruction ownership is missing')
        row = dict(bank=0, address=0x4000, offset=0, source='presentation_world.asm',
                   line=1, before='320070', assembly='LD ($7000),A')
        self.assertEqual(module.validate_instructions([row], bytes.fromhex('320070'), [(0, 3)], stage='f'), [])
        self.assertEqual(module.validate_instructions([row], bytes.fromhex('320070'), [], stage='f'), [row])
        with self.assertRaisesRegex(ValueError, 'unexplained f instruction mismatch'):
            module.validate_instructions([row], bytes.fromhex('000070'), [], stage='f')
        # A known later patch does not excuse corruption beyond its exact span.
        with self.assertRaisesRegex(ValueError, 'unexplained f instruction mismatch'):
            module.validate_instructions([row], bytes.fromhex('000000'), [(0, 1)], stage='f')

    def test_exact_q_integration_matches_real_instruction_bytes_and_scope(self):
        module = api()
        self.assertIsNotNone(module)
        base = ROOT / 'outputs/presentation/canonical-chain-s/f-public-b'
        chain = ROOT / 'outputs/presentation/canonical-chain-s/clock-input-a'
        target = chain / 'q/frostbite-direct-enemy-q.rom'
        if not target.exists():
            self.skipTest('local listing reproduction unavailable')
        rom = target.read_bytes()
        patches = module.inventory(base, chain, rom)
        self.assertEqual(Counter(p['kind'] for p in patches), {'mapper': 47, 'snapshot': 123})
        self.assertEqual(len({p['offset'] for p in patches}), len(patches))
        for patch in patches:
            raw = bytes.fromhex(patch['before'])
            self.assertEqual(rom[patch['offset']:patch['offset']+len(raw)], raw)
            if patch['kind'] == 'snapshot':
                self.assertTrue(patch['source'].startswith('presentation'))
                self.assertTrue(patch['source'].endswith('.asm'))
                self.assertFalse(patch['source'].startswith('presentation_audio'))
                changed = bytes.fromhex(patch['after'])
                self.assertEqual(sum(a != b for a, b in zip(raw, changed)), 1)
        corrupted = bytearray(rom)
        corrupted[0] ^= 1
        with self.assertRaisesRegex(ValueError, 'exact canonical F and sealed Q-E'):
            module.inventory(base, chain, bytes(corrupted))

    def test_private_layouts_are_physical_not_cpu_address_inferred(self):
        module = api()
        self.assertIsNotNone(module, 'listing inventory producer is missing')
        listing = '''# file opened: presentation_prepared_ice.asm
   1  0000                  ORG $7E5D
   2  7E5D 32 00 70         LD ($7000),A
   3  7E60                  ORG $A10C
   4  A10C 32 00 70         LD ($7000),A
# file closed: presentation_prepared_ice.asm
'''
        rows = module.parse_listing(listing, layout='q')
        self.assertEqual([(r['bank'], r['offset']) for r in rows],
                         [(0, 0x3E5D), (7, 7*16384+0x210C)])


if __name__ == '__main__':
    unittest.main()
