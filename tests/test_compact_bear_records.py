import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from compact_bear_records import pack, unpack


def synthetic_records():
    data = bytearray()
    cursor = 0
    for number in range(96):
        columns = 3 if number & 1 else 4
        row = bytearray(64)
        for cell in range(columns*3):
            dense = cursor % 470
            cursor += 1
            raw = dense*17
            predicate = 0x8000 if dense % 3 == 0 else 0
            row[cell*4:cell*4+4] = raw.to_bytes(2, 'little')+(dense|predicate).to_bytes(2, 'little')
        row[48:63] = bytes((columns, 3, columns*6))+bytes((number*11+i) & 255 for i in range(12))
        data.extend(row)
    return bytes(data)


class BearRecords(unittest.TestCase):
    def test_complete_bijection_and_unused_cells_round_trip(self):
        source = synthetic_records()
        result = pack(source)
        self.assertEqual((len(result['records']), len(result['raw'])), (3168, 940))
        self.assertEqual(unpack(result), source)
        # Used raw0 has an empty-left predicate; unused cells retain four zeros.
        self.assertEqual(source[2:4], b'\x00\x80')
        self.assertEqual(source[64+36:64+48], bytes(12))

    def test_conflicting_raw_identity_is_rejected(self):
        source = bytearray(synthetic_records())
        for start in range(0, len(source), 64):
            for at in range(start, start+source[start+48]*12, 4):
                if at and source[at+2:at+4] == b'\x00\x80':
                    source[at] = 1
                    with self.assertRaisesRegex(ValueError, 'one immutable raw key'):
                        pack(bytes(source))
                    return
        self.fail('synthetic repeated identity missing')

    def test_nonzero_unused_original_bytes_are_rejected(self):
        source = bytearray(synthetic_records())
        source[64+36] = 1
        with self.assertRaisesRegex(ValueError, 'unused original cells'):
            pack(bytes(source))


if __name__ == '__main__':
    unittest.main()
