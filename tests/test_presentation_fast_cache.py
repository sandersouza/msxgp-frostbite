"""Exact key/ref state and independent bucket-graph validation are mandatory."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class PresentationFastCacheTests(unittest.TestCase):
    def test_whole_key_reference_and_bucket_state_is_required(self):
        api=importlib.import_module('presentation_fast_cache_check')
        expected=bytes(392)+bytes([165])*2304
        actual=expected+bytes([255])*1536+bytes([165])*384+bytes(48)+bytes([165])*384
        api.verify_row(actual,expected)
        for at in (0,1,7,8,391,392,2695,2696,4616):
            changed=bytearray(actual);changed[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(changed),expected)
        with self.assertRaises(ValueError):api.verify_row(actual[:-1],expected)
    def test_live_chains_cannot_cycle_lose_keys_or_claim_a_different_hash(self):
        api=importlib.import_module('presentation_fast_cache_check');key=bytes((1,2,3,4,5,6));bucket=api.hash_key(key)
        expected=bytearray(bytes(392)+bytes([165])*2304);expected[2]=1;expected[8]=1;expected[392:398]=key
        actual=bytearray(expected+bytes([255])*1536+bytes([165])*384+bytes(48)+bytes([165])*384)
        actual[2696+bucket]=0;actual[4232]=255;actual[4616]=1;actual[4664]=bucket
        api.verify_row(actual,expected)
        for at,value in ((2696+bucket,255),(4232,0),(4616,0),(4664,bucket^1)):
            changed=bytearray(actual);changed[at]=value
            with self.assertRaises(ValueError):api.verify_row(bytes(changed),expected)
