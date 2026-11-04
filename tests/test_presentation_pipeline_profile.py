import unittest
from presentation_pipeline_profile import add_detail_probes


class PipelineProfileTests(unittest.TestCase):
    def test_missing_frame_scaffold_is_rejected(self):
        with self.assertRaises(ValueError):add_detail_probes('unrelated script',{'routine':0x6000},'/tmp/details.tsv')

    def test_every_new_inclusive_probe_is_reset_and_dumped_per_frame(self):
        text='set ::tracking 1;set ::started $now\nputs -nonewline $::captures "$::ram"'
        result=add_detail_probes(text,{'lookup':0xb011},'/tmp/details.tsv')
        self.assertIn('set ::cost_count(detail-lookup) 0',result)
        self.assertIn('$::cost_count(detail-lookup) $::cost_sum(detail-lookup)',result)
        self.assertIn('begin_probe_cost detail-lookup',result)
        self.assertIn('debug set_bp 45073',result)
