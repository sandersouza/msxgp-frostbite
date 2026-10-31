#!/usr/bin/env python3
"""Plan/apply only Frostbite issue fields in the existing shared project."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'sandersouza/msxgp-frostbite'
PROJECT = 'PVT_kwHOAJR8nM4Bn8x0'


def complete(response, key):
    values = response[key]
    if not isinstance(values, list) or response['totalCount'] != len(values):
        raise ValueError(f'incomplete {key} response; refusing truncated project data')
    return values


def plan_changes(config, fields, snapshot, issue=None, status=None):
    if (config['repository'] != REPOSITORY or config['id'] != PROJECT
            or config['owner'] != 'sandersouza' or config['number'] != 7):
        raise ValueError('configuration is outside the Frostbite project scope')
    catalog = config['issues']
    if not catalog or any(not key.isdigit() or int(key) <= 0 or str(int(key)) != key for key in catalog):
        raise ValueError('invalid issue catalog')
    if issue is not None and str(issue) not in catalog:
        raise ValueError('requested issue is outside the approved catalog')
    if status is not None and issue is None:
        raise ValueError('status changes require one explicit issue')
    definitions = complete(fields, 'fields')
    items = complete(snapshot, 'items')
    selected = {}
    for name in ('Priority', 'Size', 'Estimate', 'Status'):
        matching = [field for field in definitions if field['name'] == name]
        if len(matching) != 1 or not matching[0].get('id'):
            raise ValueError(f'missing/ambiguous field {name}; no shared fields will be created')
        selected[name] = matching[0]
        if name != 'Estimate' and matching[0].get('type') != 'ProjectV2SingleSelectField':
            raise ValueError(f'wrong field type for {name}')
    def option(name, value):
        options = [o for o in selected[name].get('options', []) if o['name'] == value]
        if len(options) != 1 or not options[0].get('id'):
            raise ValueError(f'missing/ambiguous {name} option {value}')
        return options[0]['id']
    # Validate the entire intended metadata before producing any operation.
    for metadata in catalog.values():
        if set(metadata) != {'Priority', 'Size', 'Estimate'}:
            raise ValueError('catalog must define only Priority/Size/Estimate')
        option('Priority', metadata['Priority']); option('Size', metadata['Size'])
        estimate = metadata['Estimate']
        if type(estimate) not in (int, float) or not math.isfinite(estimate) or estimate <= 0:
            raise ValueError('Estimate must be finite positive hours')
    if status is not None:
        option('Status', status)
    owned = {}
    for item in items:
        content = item.get('content') or {}
        if content.get('repository') != REPOSITORY or content.get('type') != 'Issue':
            continue
        number = content.get('number')
        url = f'https://github.com/{REPOSITORY}/issues/{number}'
        if type(number) is not int or number <= 0 or content.get('url') != url or not item.get('id'):
            raise ValueError('malformed Frostbite project content')
        if str(number) in owned:
            raise ValueError('duplicate Frostbite issue attachment; inspect without automatic deletion')
        owned[str(number)] = item
    operations = []
    for number, metadata in catalog.items():
        if issue is not None and number != str(issue):
            continue
        item = owned.get(number)
        if item is None:
            operations.append({'kind': 'attach', 'issue': int(number),
                               'url': f'https://github.com/{REPOSITORY}/issues/{number}'})
            continue
        desired = dict(metadata)
        if status is not None:
            desired['Status'] = status
        for name, value in desired.items():
            if item.get(name.lower()) == value:
                continue
            operation = {'kind': 'edit', 'issue': int(number), 'item_id': item['id'],
                         'field_id': selected[name]['id'], 'field': name, 'value': value}
            if name != 'Estimate':
                operation['option_id'] = option(name, value)
            operations.append(operation)
    return operations


def gh(*args):
    result = subprocess.run(['gh', *map(str, args)], capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError(f'GH operation failed: {result.stderr.strip()[:800]}')
    return json.loads(result.stdout) if result.stdout.strip() else None


def snapshot(config):
    project = gh('project', 'view', 7, '--owner', 'sandersouza', '--format', 'json')
    if project['id'] != config['id']:
        raise ValueError('live project identity mismatch; no mutations attempted')
    fields = gh('project', 'field-list', 7, '--owner', 'sandersouza', '--format', 'json', '--limit', 10000)
    items = gh('project', 'item-list', 7, '--owner', 'sandersouza', '--format', 'json', '--limit', 10000)
    return fields, items


def mutate(config, operation):
    if operation['kind'] == 'attach':
        gh('project', 'item-add', 7, '--owner', 'sandersouza', '--url', operation['url'], '--format', 'json')
    else:
        command = ['project', 'item-edit', '--id', operation['item_id'], '--project-id', config['id'],
                   '--field-id', operation['field_id']]
        command += (['--number', operation['value']] if operation['field'] == 'Estimate'
                    else ['--single-select-option-id', operation['option_id']])
        gh(*command)


def sync(config, issue=None, status=None, apply=False):
    applied = []
    try:
        while True:
            fields, items = snapshot(config)
            plan = plan_changes(config, fields, items, issue, status)
            if not apply or not plan:
                return {'apply': apply, 'planned': plan, 'applied': applied, 'verified': apply}
            operation = plan[0]
            if operation in applied:
                raise ValueError('previous write not visible on fresh readback; stop and retry after inspection')
            mutate(config, operation)
            applied.append(operation)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        raise ValueError(json.dumps({'error': str(error), 'applied': applied,
                                    'recovery': 'Inspect live state; rerun dry-run, then apply remaining changes.'})) from error


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--issue', type=int)
    parser.add_argument('--status')
    parser.add_argument('--apply', action='store_true', help='default is read-only dry-run')
    args = parser.parse_args()
    try:
        config = json.loads((ROOT / '.github/project.json').read_text())
        print(json.dumps(sync(config, args.issue, args.status, args.apply), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Tracking failed: {error}', file=sys.stderr)
        sys.exit(1)
