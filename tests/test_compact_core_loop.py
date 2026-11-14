import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compact_core_loop import row_data,emit_summary,emit_tables


class PackedCoreLoop(unittest.TestCase):
    def test_rows_preserve_partial_writes_and_bounded_stride(self):
        s={'destinations':[4,9],'rows':[{'a':3,'y':8,'writes':{4:3}},{'a':7,'y':9,'writes':{4:3,9:7}}]}
        b=row_data(s)
        self.assertEqual(len(b),32)
        self.assertEqual(b[:5],bytes((1,3,0,3,8)))
        self.assertEqual(b[16:21],bytes((3,3,7,7,9)))

    def test_emitter_keeps_rejected_guard_and_original_exit(self):
        s={'destinations':[4,9],'bound_offset':77,'limit':2,'rows':[{'a':3,'y':8,'writes':{4:3}}]}
        code='\n'.join(emit_summary(s,'fixture','unchanged_exit','unchanged_slow'))
        self.assertIn('jr nz,unchanged_slow',code)
        self.assertIn('jp unchanged_exit',code)
        self.assertIn('unchanged_slow:\npop af',code)
        self.assertIn('fixture_rows:',emit_tables(s,'fixture'))
