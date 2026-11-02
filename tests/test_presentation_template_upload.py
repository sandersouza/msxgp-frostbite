"""Publication evidence checks every byte and retains state across operations."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class TemplateUploadTests(unittest.TestCase):
    def test_strip_domain_covers_every_mask_per_role_and_both_generations(self):
        api=importlib.import_module('presentation_template_upload_check');inputs,expected=api.strip_fixtures(bytes(range(24)))
        seen={};lengths={}
        for at in range(0,len(inputs),32):
            page,row,color,count=inputs[at:at+4]
            if page>=2 or row>=4 or not 1<=color<=15 or not 1<=count<=14:continue
            keys=[int.from_bytes(inputs[pos:pos+2],'little') for pos in range(at+4,at+4+count*2,2)]
            if any(index>=3 for index in keys):continue
            seen.setdefault((page,row),set()).update(keys);lengths.setdefault((page,row),set()).add(count)
        self.assertEqual(len(seen),8)
        for values in seen.values():self.assertEqual(values,set(range(3)))
        for values in lengths.values():self.assertEqual(values,set(range(1,15)))
        self.assertEqual(len(expected),len(inputs)//32*api.ROW_BYTES)

    def test_invalid_strip_bounds_preserve_all_metadata_and_vram(self):
        api=importlib.import_module('presentation_template_upload_check');inputs,expected=api.strip_fixtures(bytes(range(24)))
        for index in range(1,len(inputs)//32):
            page,row,color,count=inputs[index*32:index*32+4]
            if page<2 and row<4 and 1<=color<=15 and 1<=count<=14:continue
            before=expected[(index-1)*api.ROW_BYTES:index*api.ROW_BYTES];after=expected[index*api.ROW_BYTES:(index+1)*api.ROW_BYTES]
            self.assertEqual(after[:2],bytes((1,1)));self.assertEqual(after[2:],before[2:])

    def test_every_mask_and_all_page_bank_foregrounds_are_exercised(self):
        api=importlib.import_module('presentation_template_upload_check');inputs,expected=api.fixtures(bytes(range(24)))
        seen=set();colors={}
        for at in range(0,len(inputs),9):
            page,bank,tile=inputs[at:at+3];key=inputs[at+3:at+9];index=int.from_bytes(key[:2],'little')
            if index<3 and key[2]==(130 if bank==1 else 129) and key[3]==0 and 1<=key[4]<=15 and key[5]==9:
                seen.add(index);colors.setdefault((page,bank),set()).add(key[4])
        self.assertEqual(seen,set(range(3)));self.assertEqual(len(colors),4)
        for values in colors.values():self.assertEqual(values,set(range(1,16)))
        self.assertEqual(len(expected),len(inputs)//9*api.ROW_BYTES)

    def test_first_color_publication_and_later_color_change_define_all_bytes(self):
        api=importlib.import_module('presentation_template_upload_check');inputs,expected=api.fixtures(bytes(range(8)))
        for at in range(0,len(inputs),9):
            page,bank,tile=inputs[at:at+3];key=inputs[at+3:at+9]
            if key[:2]!=bytes(2) or key[2]!=(130 if bank==1 else 129) or key[3] or not 1<=key[4]<=15 or key[5]!=9:continue
            row=expected[(at//9)*api.ROW_BYTES:(at//9+1)*api.ROW_BYTES];base=2+2304+bank*2048+tile*8
            self.assertEqual(row[base:base+8],bytes(range(8)))
            self.assertEqual(row[base+8192:base+8200],bytes([key[4]*16+4])*8)

    def test_whole_payload_rejects_carry_metadata_pgt_cgt_and_other_vram(self):
        api=importlib.import_module('presentation_template_upload_check');row=bytes(api.ROW_BYTES)
        api.verify_row(row,row)
        for at in (0,1,2,2305,2306,4354,12546,api.ROW_BYTES-1):
            bad=bytearray(row);bad[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
