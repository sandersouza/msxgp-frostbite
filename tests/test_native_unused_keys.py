import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from native_unused_keys import extents,audit_and_shadow

class UnusedKeys(unittest.TestCase):
    def test_exactly_1296_bytes_without_any_active_role(self):
        domain={a for x,y in extents() for a in range(x,y)}
        self.assertEqual(len(domain),1296)
        for page in range(2):
            for bank,count in ((0,56),(1,19),(2,9)):
                for a in range(0xD000+(page*3+bank)*384,0xD000+(page*3+bank)*384+count*6):self.assertNotIn(a,domain)
    def test_only_verified_owners_are_shadowed(self):
        data=bytearray([255]*65536);a=extents()[1][0];data[a:a+4]=b'TEST'
        row=dict(address=a,size=4,sha256=hashlib.sha256(b'TEST').hexdigest())
        self.assertEqual(audit_and_shadow(data,[row]),bytes([255])*65536)
        data[a]=0
        with self.assertRaises(ValueError):audit_and_shadow(data,[row])
    def test_out_of_role_duplicate_and_unregistered_bytes_fail(self):
        data=bytearray([255]*65536);a=extents()[0][0]
        row=dict(address=a,size=4,sha256=hashlib.sha256(data[a:a+4]).hexdigest())
        for rows in ((row,row),({**row,'address':0xD000},),({**row,'size':0},)):
            with self.assertRaises(ValueError):audit_and_shadow(data,rows)
        data[a+5]=0
        with self.assertRaises(ValueError):audit_and_shadow(data,[row])
