"""Bind reference captures to a complete committed local dependency snapshot."""
import hashlib
from pathlib import Path
import re
import subprocess

from reference_inventory import ROOT

COMMON = ('scripts/reference_provenance.py','scripts/reference_inventory.py',
          'scripts/reference_state.py','scripts/source_timing.py',
          'scripts/reference_traces.py','scripts/trace_compare.py','references/manifest.json')
ENTRIES = {'stella':'scripts/reference_traces.py','cpu':'scripts/reference_cpu_check.py',
           'ale':'scripts/reference_ale_check.py','refuge':'scripts/reference_routes.py',
           'console':'scripts/reference_routes.py'}
DEPENDENCIES = {
    'stella':COMMON+('references/trace-scenarios.json',),
    'cpu':COMMON+('scripts/reference_cpu_check.py','scripts/mechanics_probe.py',
                  'references/mechanics-cases.json','references/disassembly-map.json'),
    'ale':COMMON+('scripts/reference_ale_check.py',),
    'refuge':COMMON+('scripts/reference_routes.py','references/refuge-scenario.json'),
    'console':COMMON+('scripts/reference_routes.py','references/refuge-scenario.json')}


def audit_manifest(report, paths, root=ROOT):
    commit=report['tool_source_commit'];manifest=report['utility_fingerprints']
    if not isinstance(commit,str) or not re.fullmatch('[0-9a-f]{40}',commit):
        raise ValueError('exact producer commit required')
    if not isinstance(manifest,dict) or set(manifest)!=set(paths):
        raise ValueError('complete bounded producer dependency manifest required')
    for path in paths:
        digest=manifest[path]
        if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):
            raise ValueError('invalid producer dependency hash')
        blob=subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=root,timeout=30)
        if hashlib.sha256(blob).hexdigest()!=digest:
            raise ValueError(f'producer dependency differs from commit: {path}')


def snapshot_paths(paths, root=ROOT):
    report={'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
            'utility_fingerprints':{path:hashlib.sha256((Path(root)/path).read_bytes()).hexdigest() for path in paths}}
    audit_manifest(report,paths,root)
    return report


def producer_snapshot(component):
    report=snapshot_paths(DEPENDENCIES[component])
    report['utility_sha256']=report['utility_fingerprints'][ENTRIES[component]]
    return report


def verify_snapshot(report, component):
    current=snapshot_paths(DEPENDENCIES[component])
    if any(current[key]!=report[key] for key in current):
        raise ValueError('producer dependencies/revision changed during capture')
