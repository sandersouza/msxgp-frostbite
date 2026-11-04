import unittest
from presentation_fixed_clock import map_ram_page0,admit_commit


class FixedClockTests(unittest.TestCase):
    def test_takeover_preserves_other_primary_and_secondary_pages(self):
        for primary in range(256):
            for secondary in (0,0x1b,0x6c,0xe4,255):
                p,s=map_ram_page0(primary,True,secondary)
                self.assertEqual(p&252,primary&252)
                self.assertEqual(p&3,primary>>6)
                self.assertEqual(s&252,secondary&252)
                self.assertEqual(s&3,secondary>>6)
                self.assertEqual(map_ram_page0(primary,False,secondary),(p,secondary))

    def test_commit_admission_uses_real_vblanks_and_handles_wrap(self):
        self.assertFalse(admit_commit(False,10,0))
        self.assertFalse(admit_commit(True,1,0))
        self.assertTrue(admit_commit(True,2,0))
        self.assertTrue(admit_commit(True,1,65535))
        self.assertFalse(admit_commit(True,0,65535))

    def test_clock_probe_separates_source_from_slow_pictures_and_rejects_gaps(self):
        from presentation_fixed_clock_probe import clocks
        points=[{'ram':[0]*128} for _ in range(10)]
        irq=[[i+1,i+90,i/60,22000,1,0,0] for i in range(9)]
        pictures=[[i,i*4,0,i/15,i*4+90,90000,193,202] for i in range(3)]
        report=clocks(irq,pictures,points)
        self.assertAlmostEqual(report['source_steps_per_second'],60)
        self.assertAlmostEqual(report['active_pictures_per_second'],15)
        points[2]['ram'][0x46]=1
        self.assertEqual(clocks(irq,pictures,points)['active_picture_intervals'],1)
        irq[3][1]+=1
        with self.assertRaisesRegex(ValueError,'missed hardware'):
            clocks(irq,pictures,points)
