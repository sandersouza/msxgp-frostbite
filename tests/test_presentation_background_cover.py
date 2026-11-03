"""Rows may skip their fill only for their own visible source floe."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class BackgroundCoverTests(unittest.TestCase):
    def test_native_domain_distinguishes_every_individual_floe_owner(self):
        api=importlib.import_module('presentation_background_cover_check')
        self.assertEqual(getattr(api,'INPUT_BYTES',None),7,'four independent source colors must be input')
        inputs,expected=api.fixtures();seen=set()
        for at,result in enumerate(expected):
            row,coarse,*tail=inputs[at*7:at*7+7];colors=tail[:4];blank=tail[4]
            visible=[i for i,color in enumerate(colors) if api.PALETTE[color]!=4]
            if not blank and len(visible)==1:seen.add((row,coarse,visible[0],result))
        for coarse in (0,1):
            for owner in range(4):
                y=167-owner*26+coarse
                for row in range(24):self.assertIn((row,coarse,owner,int(y//8<=row<=(y+6)//8)),seen)

    def test_blank_water_and_invalid_selectors_never_claim_coverage(self):
        api=importlib.import_module('presentation_background_cover_check');water=api.PALETTE.index(4);visible=api.PALETTE.index(15)
        self.assertFalse(api.covered(11,0,bytes([water])*4,0))
        self.assertTrue(api.covered(11,0,bytes([visible])*4,0))
        for row,coarse,blank in ((11,0,1),(24,0,0),(255,0,0),(11,2,0),(11,255,0)):
            self.assertFalse(api.covered(row,coarse,bytes([visible])*4,blank))
