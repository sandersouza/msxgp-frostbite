import shutil
import subprocess
import unittest
from pathlib import Path

import compact_candidate_live_probe as candidate


@unittest.skipUnless(shutil.which('tclsh'), 'Tcl interpreter required')
class CandidateObserverPhaseTests(unittest.TestCase):
    def phase(self,mode,pc):
        syms={'native_reset_done':100,'t_main.frame':200,'contact_compact':300}
        observer=candidate.candidate_observer(Path('/unused'),50,syms,mode)
        script='''array set breakpoints {}
proc debug {kind args} {
 if {$kind eq "set_bp"} {set ::breakpoints([lindex $args 0]) [lindex $args 2]}
 return placeholder
}
'''+observer+f'''
if {{[info exists ::breakpoints({pc})]}} {{eval $::breakpoints({pc})}}
puts $::compact_phase
'''
        result=subprocess.run(['tclsh'],input=script,text=True,capture_output=True,check=True)
        self.assertEqual(result.stderr,'')
        return result.stdout.strip()

    def test_source_reset_is_still_cold(self):
        self.assertEqual(self.phase('ntsc',100),'startup')

    def test_initialized_game_clock_starts_natural_play(self):
        self.assertEqual(self.phase('bear-pal',200),'runtime')

    def test_matrix_direct_call_starts_active_phase_without_clock_loop(self):
        self.assertEqual(self.phase('matrix',0xC760),'runtime')


if __name__=='__main__':unittest.main()
