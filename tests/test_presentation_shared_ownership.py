import unittest

from presentation_shared_ownership import audit_active_references, audit_pool


class SharedOwnershipTests(unittest.TestCase):
    def test_displayed_other_generation_tile_is_protected(self):
        before = bytearray(16384)
        before[0x1800:0x1b00] = bytes([128]) * 768
        before[0x1800 + 8 * 32 + 2] = 83
        before[0x1b00] = 208
        registers = bytes([0, 0, 6, 0, 0, 0, 0, 0])
        prepared = bytearray(before)
        prepared[2048 + 84 * 8] = 1  # unreferenced tile may be prepared
        audit_active_references(before, prepared, registers)
        for address in (2048 + 83 * 8, 0x2000 + 2048 + 83 * 8,
                        0x1800 + 8 * 32 + 2, 0x1b00):
            bad = bytearray(prepared)
            bad[address] ^= 1
            with self.assertRaises(ValueError):
                audit_active_references(before, bad, registers)

    def test_empty_pool_and_rejects_unowned_or_broken_chains(self):
        pool = bytearray(2624)
        pool[:2048] = b'\xff' * 2048
        pool[2562] = 255
        keys = b'\xff' * 2304
        audit_pool(pool, bytes(512), keys)
        pool[2048 + 128] = 1  # ref with no row or publication
        with self.assertRaises(ValueError):
            audit_pool(pool, bytes(512), keys)
        pool[2048 + 128] = 0
        pool[0] = 0  # nonempty chain cannot point to an unpublished color
        with self.assertRaises(ValueError):
            audit_pool(pool, bytes(512), keys)


if __name__ == '__main__':
    unittest.main()
