import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    from compact_enemy_ram_check import native_code_size
except ImportError:
    native_code_size=None


class NativeIRQAllocation(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(native_code_size,'explicit IRQ-safe allocation contract is missing')
    def meta(self,size=112,irq=False):
        m={'compact_enemy_ram':{'initializers':[{'ram_address':0xE300,'size':size}]}}
        if irq:m['native_enemy_irq_fix']={'code_bytes':116,'protected_address_latch':True}
        return m
    def test_original_extent_is_preserved(self):self.assertEqual(native_code_size(self.meta()),112)
    def test_four_new_bytes_require_feature_authority(self):
        with self.assertRaises(ValueError):native_code_size(self.meta(116))
        self.assertEqual(native_code_size(self.meta(116,True)),116)
    def test_extent_or_feature_mismatch_is_rejected(self):
        for size in (112,115,117):
            with self.assertRaises(ValueError):native_code_size(self.meta(size,True))

    def test_flat_catalog_keeps_the_claimed_code_suffix_out_of_free_space(self):
        from native_flat_catalog import free_extents
        m=self.meta(116,True)
        m['compact_retired_resident']={'ranges':[]}
        m['compact_grid_palette']={'reclaimed_ranges':[]}
        free={a for first,last in free_extents(m) for a in range(first,last)}
        self.assertFalse(set(range(0xE370,0xE374))&free)
        self.assertIn(0xE374,free)

    def test_flat_catalog_preserves_all_eight_P0_cache_records(self):
        from native_flat_catalog import free_extents
        m=self.meta(116,True)
        m['compact_retired_resident']={'ranges':[]}
        m['compact_grid_palette']={'reclaimed_ranges':[]}
        free={a for first,last in free_extents(m) for a in range(first,last)}
        self.assertFalse(set(range(0xC080,0xC180))&free)

    def test_native_lifetimes_preserve_fixed_key_publishers(self):
        from native_flat_catalog import free_extents
        m=self.meta(116,True)
        m['compact_retired_resident']={'ranges':[]};m['compact_grid_palette']={'reclaimed_ranges':[]}
        free={a for first,last in free_extents(m,native_lifetimes=True) for a in range(first,last)}
        self.assertFalse(set(range(0x4B02,0x4B2F))&free)

    def test_native_lifetimes_preserve_live_header_fragment_inputs(self):
        from native_flat_catalog import free_extents
        m=self.meta(116,True)
        m['compact_retired_resident']={'ranges':[]};m['compact_grid_palette']={'reclaimed_ranges':[]}
        free={a for first,last in free_extents(m,native_lifetimes=True) for a in range(first,last)}
        self.assertFalse(set(range(0xC7B0,0xC7B3))&free)
