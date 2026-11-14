import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from native_flat_asm import split_functions

class SourceFunctions(unittest.TestCase):
    def test_external_jumps_are_relaxed_but_local_branches_stay_local(self):
        header,rows=split_functions('x EQU 1\na:\n JR NZ,b\n.local:\n JR .local\n RET\nb:\n RET\nend:\n',('a','b'),'end')
        self.assertEqual(header,'x EQU 1\n')
        self.assertIn(' JP NZ,b',rows['a']);self.assertIn(' JR .local',rows['a'])
    def test_required_fallthrough_is_kept_with_its_parent(self):
        _,rows=split_functions('a:\n JR .next\n.next:\nb:\n RET\nend:\n',('a',),'end')
        self.assertIn('b:',rows['a'])
    def test_missing_or_disordered_boundaries_fail(self):
        for entries in (('a','missing'),('b','a')):
            with self.assertRaises(ValueError):split_functions('a:\n RET\nb:\n RET\nend:\n',entries,'end')
