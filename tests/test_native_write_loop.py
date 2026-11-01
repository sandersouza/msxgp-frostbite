import importlib
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from native_codegen import decode, ROOTS
from mechanics_probe import execute_slice
from environment import ROOT, verified_tool
import native_fast


def fixture():
    rom = bytearray([0xEA] * 4096)
    rom[0x100:0x110] = bytes((0xBC, 0, 0xFC, 0xBD, 0x20, 0xFC, 0x99, 0xC0, 0,
                             0xE4, 0xCD, 0xB0, 3, 0xE8, 0x10, 0xF0))
    rom[0xC00:0xC05] = bytes((0, 1, 0, 2, 64))
    rom[0xC20:0xC24] = bytes((17, 34, 51, 68))
    instructions = {}; pc = 0xF100
    while pc < 0xF110:
        item = decode(rom, pc); instructions[pc] = item; pc += item['size']
    return bytes(rom), instructions


class NativeWriteLoopTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('native_write_loop'), 'native pure-loop compiler missing')
        return importlib.import_module('native_write_loop')

    def test_prefixes_preserve_unwritten_cells_and_last_duplicate_store(self):
        api = self.api(); rom, instructions = fixture()
        loops = api.find_loops(instructions)
        self.assertEqual(len(loops), 1)
        summary = api.summarize(rom, loops[0])
        self.assertEqual(summary['limit'], 4)
        self.assertEqual(summary['destinations'], [64, 65, 66])
        self.assertEqual(summary['rows'][2], {'a': 51, 'y': 0, 'writes': {64: 51, 65: 34}})
        self.assertEqual(summary['rows'][3]['writes'], {64: 51, 65: 34, 66: 68})

    def test_hardware_wrap_bound_alias_and_changed_control_flow_are_not_fused(self):
        api = self.api(); rom, instructions = fixture(); loop = api.find_loops(instructions)[0]
        self.assertIsNone(api.summarize(rom, {**loop, 'bound': 0xC0}))
        short = api.summarize(rom, {**loop, 'load_a': 0xFFFE})
        self.assertEqual(short['limit'], 2)
        bad = {k: dict(v) for k, v in instructions.items()}; bad[0xF10E]['target'] += 1
        self.assertEqual(api.find_loops(bad), [])

    def test_generated_effect_data_matches_independent_original_instructions_and_flags(self):
        api = self.api(); rom, instructions = fixture(); summary = api.summarize(rom, api.find_loops(instructions)[0])
        for bound in range(4):
            for p in range(0, 256, 17):
                initial = [(i * 37 + p) & 255 for i in range(128)]; initial[0x4D] = bound
                result = execute_slice(rom, {'id': 'synthetic-pure-loop', 'start': 'F100', 'stops': ['F110'],
                    'registers': {'a': p ^ 165, 'x': 0, 'y': p ^ 90, 'p': p, 'sp': 255},
                    'ram': {f'{i + 128:02X}': f'{v:02X}' for i, v in enumerate(initial)},
                    'watch': [f'{i:02X}' for i in range(128, 256)], 'limit': 1000})
                row = summary['rows'][bound]; wanted = list(initial)
                for offset, value in row['writes'].items(): wanted[offset] = value
                self.assertEqual([int(v, 16) for v in result['ram'].values()], wanted)
                self.assertEqual(result['registers'], {'a': row['a'], 'x': bound, 'y': row['y'],
                    'p': (p & 0x7C) | 3, 'sp': 255})

    def test_full_native_output_assembles_with_guard_fallback_and_table_labels(self):
        api = self.api(); rom = bytearray(fixture()[0])
        for root in ROOTS: rom[root - 0xF000:root - 0xF000 + 3] = bytes((0x4C, 0x19, 0xF0))
        rom[0x476:0x479] = bytes((0x4C, 0, 0xF1))
        rom[0x110:0x113] = bytes((0x4C, 0x19, 0xF0))
        # The production generator pins the supplied original. This isolated
        # test authorizes its synthetic fixture hash; all translation is real.
        with patch.object(native_fast, 'SOURCE_SHA256', hashlib.sha256(rom).hexdigest()):
            generated = api.generate(bytes(rom))
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory); (out / 'data.bin').write_bytes(rom[0xC00:])
            asm = out / 'unit.asm'
            asm.write_text('    ORG $8000\n' + f'    INCLUDE "{ROOT / "src/native_cpu.asm"}"\n' + generated
                + '\n    ALIGN 1024\noriginal_data:\n' + f'    INCBIN "{out / "data.bin"}"\n')
            result = subprocess.run([str(verified_tool('sjasmplus')), '--nologo', f'--raw={out / "unit.bin"}', str(asm)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr[-1200:])

