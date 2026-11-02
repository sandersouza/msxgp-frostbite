"""Source-domain accounting cannot silently omit or duplicate observations."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class PresentationSourceCasesTests(unittest.TestCase):
    def test_only_the_whole_unique_approved_domain_and_startup_count_are_accepted(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_source_cases'),'complete source-domain loader missing')
        api=importlib.import_module('presentation_source_cases')
        cases=[{'id':f'{family}-{i}','family':family} for family,n in (('fixtures',1690),('cold_route',31),('natural_window',394)) for i in range(n)]
        self.assertEqual(api.validate_domain(cases,7),{'fixtures':1690,'cold_route':31,'natural_window':394})
        for values,startup in ((cases[:-1],7),(cases,0),(cases+[cases[0]],7)):
            with self.assertRaises(ValueError):api.validate_domain(values,startup)
        duplicate=[dict(row) for row in cases];duplicate[-1]['id']=duplicate[0]['id']
        with self.assertRaises(ValueError):api.validate_domain(duplicate,7)
