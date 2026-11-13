"""Reproduction checks use locally generated canonical F inputs, never original assets."""
import importlib.util
import json
import unittest
import uuid

from environment import ROOT
from presentation_band_spike import sha


class NativePipelineBuildTests(unittest.TestCase):
    def test_public_chain_reproduces_sealed_stages_and_preserves_all_live_packets(self):
        spec = importlib.util.find_spec('native_pipeline_build')
        self.assertIsNotNone(spec, 'public source chain is missing')
        from native_pipeline_build import build, EXPECTED
        base = ROOT / 'outputs/presentation/performance-canonical-a'
        if not (base / 'build.json').exists():
            self.skipTest('canonical F local inputs unavailable')
        out = ROOT / 'outputs/presentation/canonical-chain-s' / ('test-' + uuid.uuid4().hex)
        result = build(base, out)
        self.assertEqual(result['rom_sha256'], EXPECTED['q'])
        for stage in ('i', 'j', 'k', 'l', 'm', 'contact14', 'p', 'q'):
            meta = json.loads((out / stage / 'build.json').read_text())
            data = (out / stage / meta['rom']['filename']).read_bytes()
            self.assertEqual(sha(data), EXPECTED[stage], stage)
            self.assertEqual(meta.get('source_commit'), result['complete_source']['commit'])
            self.assertEqual(meta.get('source_files'), result['complete_source']['files'])
            self.assertEqual(meta.get('source_dirty'), result['complete_source']['working_tree_dirty'])
            self.assertIs(meta.get('exploratory'), True)
            self.assertIn('source_commit', meta['ancestry_source'])
            self.assertTrue((out / stage / 'patch.lst').exists() if stage != 'm' else True)
        self.assertEqual(sha((out / 'i/tables.json').read_bytes()),
                         'ddd972e9c543b3136f567bdd5e1263f7d8f37c159dddcc145c98b128ce9e634e')
        allocation = json.loads((out / 'i/tables.json').read_text())
        self.assertTrue(any(bank == 150 and address <= 0xADC0 and address + size > 0xADC0
                            for bank, address, size in allocation['allocations']))
        i_meta = json.loads((out / 'i/build.json').read_text())
        i_rom = (out / 'i' / i_meta['rom']['filename']).read_bytes()
        q_meta = json.loads((out / 'q/build.json').read_text())
        q_rom = (out / 'q' / q_meta['rom']['filename']).read_bytes()
        for bank, address, size in allocation['allocations']:
            at = bank * 16384 + address - 0x8000
            self.assertEqual(q_rom[at:at+size], i_rom[at:at+size])
        # raw0 remains a legal floe packet, with no namespace renumbering.
        self.assertEqual(result['raw_floe_zero_preserved'], True)
        self.assertIn('src/presentation_inherited_i.asm', result['complete_source']['files'])
        self.assertFalse(any('outputs/' in name for name in result['complete_source']['files']))
        with self.assertRaisesRegex(ValueError, 'immutable'):
            build(base, out)


if __name__ == '__main__':
    unittest.main()
