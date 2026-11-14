"""Execute generated Tcl to catch broken completion/channel boundaries."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import compact_live_probe as probe


class CompletionHookTests(unittest.TestCase):
    def test_observer_runs_after_closing_channels_in_both_harnesses(self):
        instrument = getattr(probe, 'instrument_harness', None)
        self.assertIsNotNone(instrument, 'validated completion injector missing')
        executable = shutil.which('tclsh')
        if not executable:
            self.skipTest('Tcl interpreter unavailable')
        for mode, ending in (('ntsc', '\n  exit;return\n}'),
                             ('matrix', ';exit;return}')):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = ('proc after args {}\nproc dispatch {} {\n' +
                          f'set ::timing [open {{{root / "trace"}}} w]\n'
                          'close $::timing' + ending + '\n'
                          'after time 20 {error watchdog}\ndispatch\n')
                observer = '\nproc compact_finish {} {puts observer-completed}\n'
                script = root / 'probe.tcl'
                script.write_text(instrument(source, observer, mode))
                result = subprocess.run([executable, str(script)], capture_output=True,
                                        text=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), 'observer-completed')

    def test_rejects_unknown_completion_instead_of_partial_instrumentation(self):
        instrument = getattr(probe, 'instrument_harness', None)
        self.assertIsNotNone(instrument, 'validated completion injector missing')
        with self.assertRaises(ValueError):
            instrument('after time 1 {exit}\n', '', 'ntsc')


if __name__ == '__main__':
    unittest.main()
