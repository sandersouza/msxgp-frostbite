"""Original-free setup safety tests; no network or tool build required."""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class EnvironmentTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('environment'), 'setup utility missing')
        return importlib.import_module('environment')

    def test_host_limits(self):
        api = self.api()
        api.validate_host('Darwin', 'arm64')
        api.validate_host('Darwin', 'x86_64')
        with self.assertRaisesRegex(ValueError, 'macOS'):
            api.validate_host('Linux', 'x86_64')
        with self.assertRaisesRegex(ValueError, 'arm64'):
            api.validate_host('Darwin', 'ppc')

    def checkout(self, directory):
        def git(*args):
            return subprocess.check_output(['git', '-C', str(directory), *args], stderr=subprocess.DEVNULL, text=True).strip()
        git('init', '-q')
        (directory / 'source.c').write_text('original\n')
        git('add', 'source.c')
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        return git('rev-parse', 'HEAD')

    def test_mismatched_checkout_is_not_reset(self):
        api = self.api()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            commit = self.checkout(directory)
            with self.assertRaisesRegex(ValueError, 'revision'):
                api.validate_checkout(directory, '0' * 40)
            self.assertEqual(subprocess.check_output(['git', '-C', tmp, 'rev-parse', 'HEAD'], text=True).strip(), commit)

    def test_dirty_source_is_preserved_and_rejected(self):
        api = self.api()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            commit = self.checkout(directory)
            (directory / 'source.c').write_text('user change\n')
            with self.assertRaisesRegex(ValueError, 'modified'):
                api.validate_checkout(directory, commit)
            self.assertEqual((directory / 'source.c').read_text(), 'user change\n')

    def test_receipt_detects_changed_binary(self):
        api = self.api()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            binary = directory / 'assembler'
            binary.write_bytes(b'original binary')
            receipt = {'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'commit': 'a' * 40}
            path = directory / 'receipt.json'
            path.write_text(json.dumps(receipt))
            api.validate_receipt(binary, path, 'a' * 40)
            binary.write_bytes(b'changed binary')
            with self.assertRaisesRegex(ValueError, 'binary'):
                api.validate_receipt(binary, path, 'a' * 40)
            self.assertEqual(binary.read_bytes(), b'changed binary')

    def test_untracked_source_is_preserved_before_build(self):
        api = self.api()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = {'commit': 'pending', 'binary': 'assembler', 'build': ['make']}
            directory = api.tool_directory(root, 'fixture', spec)
            directory.mkdir(parents=True)
            spec['commit'] = self.checkout(directory)
            with patch.object(api, 'tool_directory', return_value=directory):
                extra = directory / 'extra.cpp'
                extra.write_text('unexpected source\n')
                with patch.object(api, 'run', wraps=api.run) as run:
                    with self.assertRaisesRegex(ValueError, 'untracked'):
                        api.prepare_tool(root, 'fixture', spec)
                    self.assertFalse(any(call.args[0] == ['make'] for call in run.call_args_list))
                self.assertEqual(extra.read_text(), 'unexpected source\n')
                self.assertFalse((directory / '.frostbite-build.log').exists())

    def test_managed_receipt_and_log_are_allowed(self):
        api = self.api()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            commit = self.checkout(directory)
            (directory / '.frostbite-build.log').write_text('build log\n')
            (directory / '.frostbite-receipt.json').write_text('{}\n')
            api.validate_checkout(directory, commit)

    def test_dry_run_does_not_create_managed_tools(self):
        api = self.api()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = api.describe_plan(root)
            self.assertIn('preserve', result.lower())
            self.assertEqual(list(root.iterdir()), [])

    def test_version_probe_avoids_legacy_long_argv_buffer(self):
        api=self.api()
        self.assertTrue(hasattr(api,'version_output'),'bounded version probe missing')
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/('x'*150)
            directory.mkdir()
            binary=directory/'probe'
            binary.write_text(f'#!{sys.executable}\nimport sys\nassert sum(len(x)+1 for x in sys.argv)<132\nprint("PINNED")\n')
            binary.chmod(0o755)
            self.assertEqual(api.version_output(binary,[]).strip(),'PINNED')


if __name__ == '__main__':
    unittest.main()
