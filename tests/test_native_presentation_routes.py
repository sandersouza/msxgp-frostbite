import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from native_presentation_routes import adapt_probe


class NativePresentationRoutesTests(unittest.TestCase):
    def test_keeps_guards_and_supports_second_player(self):
        original = Path('scripts/presentation_fixed_clock_probe.py').read_text()
        adapted = adapt_probe(original, Path('/tmp/source route'), 4332)
        compile(adapted, '<adapted>', 'exec')
        for guard in ('audit_active(', 'audit_row(', 'compare(', 'future-snapshot',
                      'partial native checkpoint', 'source step counter differs'):
            self.assertEqual(original.count(guard), adapted.count(guard))
        self.assertIn('set fire $fire1', adapted)
        self.assertNotIn('fail one-player-contract', adapted)
        self.assertIn('2<=steps<=4332', adapted)

    def test_rejects_changed_upstream_instead_of_weakening_checks(self):
        with self.assertRaises(ValueError):
            adapt_probe('different producer', Path('/tmp/source'), 100)

    def test_rejects_unbounded_route(self):
        with self.assertRaises(ValueError):
            adapt_probe('', Path('/tmp/source'), 0)
