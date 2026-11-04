import copy
import unittest

from presentation_band_report import validate_sequence


class ReportGuardTests(unittest.TestCase):
    def test_rejects_missing_reordered_or_wrong_identity_evidence(self):
        result = dict(family='ntsc', records=[{'frame': 0}, {'frame': 1}],
                      receipt=dict(complete=True, frames=2, rom_sha256='expected'))
        validate_sequence(result, 'ntsc', 'expected', 2 * 49304)
        for field, value in [('records', [{'frame': 0}]),
                             ('records', [{'frame': 1}, {'frame': 0}]),
                             ('records', []), ('family', 'pal')]:
            bad = copy.deepcopy(result)
            bad[field] = value
            with self.assertRaises(ValueError):
                validate_sequence(bad, 'ntsc', 'expected', 2 * 49304)
        for sha, size in [('wrong', 2 * 49304), ('expected', 49304)]:
            with self.assertRaises(ValueError):
                validate_sequence(result, 'ntsc', sha, size)


if __name__ == '__main__':
    unittest.main()
