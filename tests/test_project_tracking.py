"""Pure project snapshots exercise scope, recovery and idempotence."""
import copy
import importlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
REPO = 'sandersouza/msxgp-frostbite'
URL = f'https://github.com/{REPO}/issues/6'


class TrackingTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('project_tracking'), 'tracking planner missing')
        return importlib.import_module('project_tracking')

    def fixture(self):
        config = {'owner': 'sandersouza', 'number': 7, 'id': 'PVT_kwHOAJR8nM4Bn8x0',
                  'repository': REPO, 'issues': {'6': {'Priority': 'P2', 'Size': 'M', 'Estimate': 5}}}
        fields = {'totalCount': 4, 'fields': [
            {'id': 'status', 'name': 'Status', 'type': 'ProjectV2SingleSelectField',
             'options': [{'name': 'In progress', 'id': 'wip'}, {'name': 'In review', 'id': 'review'}]},
            {'id': 'priority', 'name': 'Priority', 'type': 'ProjectV2SingleSelectField',
             'options': [{'name': 'P2', 'id': 'p2'}]},
            {'id': 'size', 'name': 'Size', 'type': 'ProjectV2SingleSelectField',
             'options': [{'name': 'M', 'id': 'medium'}]},
            {'id': 'estimate', 'name': 'Estimate', 'type': 'ProjectV2Field', 'dataType': 'NUMBER'}]}
        item = {'id': 'frostbite6', 'content': {'type': 'Issue', 'repository': REPO, 'number': 6, 'url': URL},
                'priority': 'P2', 'size': 'M', 'estimate': 5, 'status': 'In progress'}
        unrelated = {'id': 'other6', 'content': {'type': 'Issue', 'repository': 'sandersouza/other',
            'number': 6, 'url': 'https://github.com/sandersouza/other/issues/6'}, 'priority': 'P0'}
        return config, fields, {'totalCount': 2, 'items': [unrelated, item]}

    def test_aligned_snapshot_is_noop_and_inputs_unchanged(self):
        args = self.fixture()
        before = copy.deepcopy(args)
        self.assertEqual(self.api().plan_changes(*args), [])
        self.assertEqual(args, before)

    def test_legitimate_draft_and_same_repo_pull_request_are_preserved(self):
        config, fields, snapshot = self.fixture()
        snapshot['items'] += [
            {'id': 'draft', 'content': {'type': 'DraftIssue', 'title': 'draft'}},
            {'id': 'pr', 'content': {'type': 'PullRequest', 'repository': REPO,
                'number': 25, 'url': f'https://github.com/{REPO}/pull/25'}}]
        snapshot['totalCount'] = 4
        before = copy.deepcopy(snapshot)
        self.assertEqual(self.api().plan_changes(config, fields, snapshot), [])
        self.assertEqual(snapshot, before)

    def test_only_requested_status_changes(self):
        ops = self.api().plan_changes(*self.fixture(), issue=6, status='In review')
        self.assertEqual(ops, [{'kind': 'edit', 'issue': 6, 'item_id': 'frostbite6',
            'field_id': 'status', 'option_id': 'review', 'field': 'Status', 'value': 'In review'}])

    def test_same_number_other_repository_does_not_satisfy_attachment(self):
        config, fields, snapshot = self.fixture()
        snapshot['items'].pop(); snapshot['totalCount'] = 1
        self.assertEqual(self.api().plan_changes(config, fields, snapshot),
                         [{'kind': 'attach', 'issue': 6, 'url': URL}])

    def test_drift_only_edits_owned_field(self):
        config, fields, snapshot = self.fixture()
        snapshot['items'][1]['estimate'] = 2
        self.assertEqual(self.api().plan_changes(config, fields, snapshot),
            [{'kind': 'edit', 'issue': 6, 'item_id': 'frostbite6', 'field_id': 'estimate',
              'field': 'Estimate', 'value': 5}])

    def test_invalid_snapshots_fail_before_any_plan(self):
        for failure in ('duplicate', 'truncated', 'bad_url', 'unknown_option', 'bad_estimate', 'wrong_project'):
            with self.subTest(failure=failure):
                config, fields, snapshot = self.fixture()
                if failure == 'duplicate':
                    snapshot['items'].append(copy.deepcopy(snapshot['items'][1])); snapshot['totalCount'] = 3
                elif failure == 'truncated': snapshot['totalCount'] = 3
                elif failure == 'bad_url': snapshot['items'][1]['content']['url'] = 'https://example.com/6'
                elif failure == 'unknown_option': config['issues']['6']['Size'] = 'XL'
                elif failure == 'bad_estimate': config['issues']['6']['Estimate'] = math.nan
                elif failure == 'wrong_project': config['id'] = 'another-project'
                with self.assertRaises(ValueError):
                    self.api().plan_changes(config, fields, snapshot)

    def test_status_requires_a_known_single_issue(self):
        for kwargs in ({'status': 'In review'}, {'issue': 99}, {'issue': 6, 'status': 'Made up'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.api().plan_changes(*self.fixture(), **kwargs)

    def test_conflicting_or_incomplete_owned_identity_is_rejected(self):
        for change in ({'repository': None}, {'repository': 'sandersouza/other'}, {'type': None}):
            with self.subTest(change=change):
                config, fields, snapshot = self.fixture()
                snapshot['items'][1]['content'].update(change)
                with self.assertRaises(ValueError):
                    self.api().plan_changes(config, fields, snapshot)

    def test_incompatible_estimate_schema_prevents_all_mutations(self):
        api = self.api()
        for kind, data_type in (('ProjectV2SingleSelectField', None), ('ProjectV2Field', 'TEXT')):
            with self.subTest(kind=kind, data_type=data_type):
                config, fields, snapshot = self.fixture()
                fields['fields'][3].update(type=kind, dataType=data_type)
                snapshot['items'][1]['priority'] = None
                before = copy.deepcopy(snapshot)
                with patch.object(api, 'snapshot', return_value=(fields, snapshot)):
                    def forbidden_write(*args):
                        self.fail('invalid schema must be refused before transport mutation')
                    with patch.object(api, 'mutate', side_effect=forbidden_write):
                        with self.assertRaises(ValueError):
                            api.sync(config, issue=6, apply=True)
                self.assertEqual(snapshot, before)

    def test_apply_readback_and_repeat_preserve_unrelated_items(self):
        api = self.api()
        config, fields, snapshot = self.fixture()
        unrelated = copy.deepcopy(snapshot['items'][0])
        def transport(*args):
            if args[:2] == ('project', 'view'): return {'id': config['id']}
            if args[:2] == ('project', 'field-list'): return copy.deepcopy(fields)
            if args[:2] == ('project', 'item-list'): return copy.deepcopy(snapshot)
            if args[:2] == ('api', 'graphql'):
                return {'data': {'node': {'id': 'estimate', 'name': 'Estimate', 'dataType': 'NUMBER'}}}
            if args[:2] == ('project', 'item-edit'):
                if args[args.index('--id') + 1] != 'frostbite6':
                    raise AssertionError('attempt to edit unrelated item')
                if args[args.index('--single-select-option-id') + 1] != 'review':
                    raise AssertionError('unexpected option')
                snapshot['items'][1]['status'] = 'In review'
                return None
            raise AssertionError(f'unexpected external command {args}')
        with patch.object(api, 'gh', side_effect=transport):
            result = api.sync(config, issue=6, status='In review', apply=True)
            self.assertTrue(result['verified'])
            self.assertEqual(snapshot['items'][1]['status'], 'In review')
            self.assertEqual(len(result['applied']), 1)
            self.assertEqual(api.sync(config, issue=6, status='In review', apply=True)['applied'], [])
        self.assertEqual(snapshot['items'][0], unrelated)

    def test_failed_write_is_reported_and_dry_run_does_not_write(self):
        api = self.api()
        config, fields, snapshot = self.fixture()
        def fail_write(*args):
            if args[:2] == ('project', 'view'): return {'id': config['id']}
            if args[:2] == ('project', 'field-list'): return fields
            if args[:2] == ('project', 'item-list'): return snapshot
            if args[:2] == ('api', 'graphql'):
                return {'data': {'node': {'id': 'estimate', 'name': 'Estimate', 'dataType': 'NUMBER'}}}
            raise ValueError('permission denied')
        with patch.object(api, 'gh', side_effect=fail_write):
            dry_run = api.sync(config, issue=6, status='In review')
            self.assertEqual(len(dry_run['planned']), 1)
            with self.assertRaisesRegex(ValueError, 'permission denied.*applied'):
                api.sync(config, issue=6, status='In review', apply=True)

    def test_partial_failure_reports_successful_write_and_replans_remainder(self):
        api = self.api()
        config, fields, snapshot = self.fixture()
        snapshot['items'][1].update(priority=None, estimate=1)
        def write(_config, operation):
            if operation['field'] == 'Priority':
                snapshot['items'][1]['priority'] = 'P2'
            else:
                raise ValueError('network failure')
        with patch.object(api, 'snapshot', side_effect=lambda _: (fields, copy.deepcopy(snapshot))), \
             patch.object(api, 'mutate', side_effect=write):
            with self.assertRaises(ValueError) as caught:
                api.sync(config, issue=6, apply=True)
            result = json.loads(str(caught.exception))
            self.assertEqual([op['field'] for op in result['applied']], ['Priority'])
            remaining = api.sync(config, issue=6)['planned']
            self.assertEqual([op['field'] for op in remaining], ['Estimate'])
