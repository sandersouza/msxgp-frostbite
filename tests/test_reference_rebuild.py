"""Original-free integration tests: tool stand-ins exercise the CLI boundary."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reference_inventory import describe


class RebuildTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'outputs').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'outputs')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.data = bytes(4090) + bytes.fromhex('00 f0 00 f0 00 f0')
        self.rom = self.base / 'fixture.bin'
        self.rom.write_bytes(self.data)
        self.manifest = self.base / 'manifest.json'
        self.manifest.write_text(json.dumps({'schema_version': 1,
            'input': {'path': 'unused', **describe(self.data)}}))
        self.marker = self.base / 'invoked'
        self.distella = self.tool('dis assembler',
            f'from pathlib import Path\nPath({str(self.marker)!r}).touch()\nprint("processor 6502")\n')
        self.dasm = self.assembler(self.data)
        self.report = self.base / 'report.json'

    def tool(self, name, source):
        path = self.base / name
        path.write_text(f'#!{sys.executable}\n' + source)
        path.chmod(0o755)
        return path

    def assembler(self, data):
        return self.tool('assembler', 'from pathlib import Path\nimport sys\n'
            f'data = {data!r}\n'
            'for arg in sys.argv[1:]:\n'
            ' if arg.startswith(("-o", "-l", "-s")):\n'
            '  Path(arg[2:]).write_bytes(data if arg.startswith("-o") else b"fixture")\n')

    def run_cli(self):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/reference_rebuild.py'),
            '--rom', str(self.rom), '--manifest', str(self.manifest),
            '--distella', str(self.distella.relative_to(ROOT)),
            '--dasm', str(self.dasm.relative_to(ROOT)), '--output', str(self.report)],
            cwd=ROOT, capture_output=True, text=True)

    def test_identical_rebuild_and_private_artifacts(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(self.report.read_text())
        self.assertTrue(report['byte_identical'])
        self.assertEqual(report['rebuilt']['sha256'], hashlib.sha256(self.data).hexdigest())
        self.assertEqual(report['tools']['distella']['sha256'],
                         hashlib.sha256(self.distella.read_bytes()).hexdigest())
        artifact = ROOT / report['artifacts_directory']
        self.addCleanup(shutil.rmtree, artifact)
        self.assertTrue(artifact.is_relative_to(ROOT / 'outputs/reference-rebuild'))
        self.assertEqual((artifact / 'rebuilt.bin').read_bytes(), self.data)
        ignored = subprocess.run(['git', 'check-ignore', str(artifact / 'reference.asm')],
                                 cwd=ROOT, capture_output=True)
        self.assertEqual(ignored.returncode, 0)
        self.assertNotIn('processor 6502', self.report.read_text())

    def test_changed_bytes_fail_even_when_assembler_succeeds(self):
        self.dasm = self.assembler(bytes([1]) + self.data[1:])
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn('byte mismatch', result.stderr)
        self.assertFalse(self.report.exists())

    def test_short_or_prefixed_binary_fails(self):
        for data in (self.data[:-1], b'\x00\xf0' + self.data):
            self.dasm = self.assembler(data)
            result = self.run_cli()
            self.assertEqual(result.returncode, 1)
            self.assertIn('size mismatch', result.stderr)

    def test_corrupt_rom_never_invokes_backend(self):
        self.rom.write_bytes(bytes([1]) + self.data[1:])
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn('sha256 mismatch', result.stderr)
        self.assertFalse(self.marker.exists())

    def test_missing_rom_never_invokes_backend(self):
        self.rom.unlink()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Reference rebuild failed', result.stderr)
        self.assertFalse(self.marker.exists())

    def test_failed_tool_reports_failure(self):
        self.distella = self.tool('bad tool', 'raise SystemExit(9)\n')
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn('exit 9', result.stderr)
        self.assertFalse(self.report.exists())

    def test_distella_receives_short_private_input_name(self):
        self.distella = self.tool('bounded-path-tool', 'import sys\nfrom pathlib import Path\n'
            'assert len(sys.argv[-1]) < 50\n'
            'assert Path(sys.argv[-1]).read_bytes()[-4:] == bytes.fromhex("00 f0 00 f0")\n'
            'print("processor 6502")\n')
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.addCleanup(shutil.rmtree, ROOT / json.loads(self.report.read_text())['artifacts_directory'])


if __name__ == '__main__':
    unittest.main()
