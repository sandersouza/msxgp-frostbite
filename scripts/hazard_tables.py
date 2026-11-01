"""Audit actual source contact components before compiling native tables.

The ordinary copy union below is a candidate until its independent alias gate
passes. It consumes original single-copy truth, never rasterized MSX graphics.
"""
import json
from pathlib import Path

from environment import ROOT
from hazard_catalog import HELPERS,capture_plan,make_case,producer,validate_partitions
from reference_inventory import verified_input
from reference_provenance import audit_manifest
from reference_state import decode_state
from stella_hazard import HELPERS as OBSERVER_HELPERS,digest,validate_observation,verified_backend


def validate_layout(manifest,rom):
    if (manifest.get('complete') is not True or manifest.get('exploratory') is not False
            or manifest.get('producer_dirty_at_start') is not False):
        raise ValueError('complete nonexploratory clean-start source component required')
    expected=capture_plan(manifest['kind'],rom)
    if any(manifest.get(key)!=value for key,value in expected.items()):
        raise ValueError('complete exact source component domain required')
    count=validate_partitions(manifest['partitions'],expected)
    if manifest.get('cases')!=count:raise ValueError('complete component count required')
    return count


def profile_record(plan,data,y,mode,coordinate):
    if len(data)!=plan['cases_per_player']*58:raise ValueError('complete original profile required')
    if type(mode) is not int or not 0<=mode<len(plan['modes']):raise ValueError('source mode outside captured domain')
    try:yi=plan['ys'].index(y);xi=plan['coordinates'].index(coordinate)
    except ValueError:raise ValueError('source coordinate outside captured domain') from None
    offset=((yi*len(plan['modes'])+mode)*len(plan['coordinates'])+xi)*58
    return data[offset:offset+58]


def copy_union(px,y,shape,reflection,nusiz,object_x,single):
    if nusiz not in range(4) or not 0<=px<160 or not 0<=object_x<160:
        raise ValueError('complete original copy coordinates required')
    offsets=((0,),(0,16),(0,32),(0,16,32))[nusiz];result=bytearray(58)
    for offset in offsets:
        dx=(px-object_x-offset)%160
        if dx>=153:dx-=160
        if not -7<=dx<=7:continue
        data=single(px,y,shape,reflection,dx)
        for index,value in enumerate(data):result[index]|=value
    return bytes(result)


def verified_profiles(root,*,exploratory=False):
    root=Path(root);manifest=json.loads((root/'catalog.json').read_text())
    rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    if exploratory:
        expected=capture_plan(manifest['kind'],rom,manifest['player_x'])
        if any(manifest.get(key)!=value for key,value in expected.items()) or manifest.get('complete') is not True:
            raise ValueError('complete explicitly selected exploratory domain required')
        if manifest.get('exploratory') is not True:raise ValueError('explicit exploratory evidence required')
        count=validate_partitions(manifest['partitions'],expected)
        if manifest.get('cases')!=count:raise ValueError('exploratory count mismatch')
    else:count=validate_layout(manifest,rom)
    if manifest['source']!=verified_input(ROOT/'references/roms/frostbite.bin'):
        raise ValueError('source ROM identity mismatch')
    audit_manifest({'tool_source_commit':manifest['producer_commit'],'utility_fingerprints':manifest['helpers']},HELPERS)
    if manifest['helpers']!=producer():raise ValueError('current source reader differs from frozen capture helpers')
    backend=verified_backend(root/'stella')
    if (backend!=manifest['backend_build'] or backend.get('producer_dirty') is not False
            or digest(root/'stella')!=manifest['binary_sha256']
            or digest(root/'frostbite-hazard-observer.json')!=manifest['backend_build_sha256']):
        raise ValueError('frozen original observer identity mismatch')
    audit_manifest({'tool_source_commit':backend['producer_commit'],'utility_fingerprints':backend['helpers']},OBSERVER_HELPERS)
    initial=(root/'initial.state').read_bytes();base=decode_state(initial)['ram']
    if digest(root/'initial.state')!=manifest['initial_sha256']:raise ValueError('source preparation capsule changed')
    profiles={};receipts=0;global_workspaces=set();expected_helpers={key:manifest['helpers'][key] for key in OBSERVER_HELPERS}
    audited_commits=set()
    for part in manifest['partitions']:
        directory=root/f'worker-{part["start"]:03d}-{part["stop"]:03d}'
        if json.loads((directory/'partition.json').read_text())!=part:raise ValueError('partition receipt changed')
        xs=manifest['player_x'][part['start']:part['stop']]
        if set(part['profiles'])!={f'player-{px:03d}.truth' for px in xs}:raise ValueError('complete unique profile set required')
        for px in xs:
            path=directory/f'player-{px:03d}.truth'
            if digest(path)!=part['profiles'][path.name]:raise ValueError('raw source profile changed')
            data=path.read_bytes()
            if len(data)!=manifest['cases_per_player']*58:raise ValueError('partial original profile')
            profiles[px]=path
        expected={}
        entries=[(mode,x) for mode in range(len(manifest['modes'])) for x in manifest['coordinates']]
        for px in xs:
            for yi,y in enumerate(manifest['ys']):
                for offset in range(0,len(entries),8192):
                    name=(directory/f'px-{px:03d}-y-{yi:02d}-batch-{offset:05d}'/'observation.json').relative_to(root).as_posix()
                    expected[name]=(px,yi,offset,len(entries[offset:offset+8192]))
        if len(part['receipts'])!=len(expected) or {r['path'] for r in part['receipts']}!=set(expected):
            raise ValueError('complete unique bounded source observation receipts required')
        loaded_px=None;profile=None
        for receipt in part['receipts']:
            path=root/receipt['path'];px,yi,offset,n=expected[receipt['path']]
            if receipt!={'path':receipt['path'],'sha256':digest(path),'player_x':px,'y_index':yi,'offset':offset,'cases':n}:
                raise ValueError('source receipt identity or ordering changed')
            observed=json.loads(path.read_text());commit=observed['producer_commit']
            if commit not in audited_commits:
                audit_manifest({'tool_source_commit':commit,'utility_fingerprints':manifest['helpers']},HELPERS)
                audited_commits.add(commit)
            global_workspaces.add((commit,observed['producer_dirty']))
            if (observed['helpers']!=expected_helpers or observed['cases']!=n
                    or observed['mode']!=('shore ROI' if manifest['kind']=='shore' else 'top-object ROI')
                    or observed['backend_build']!=backend or observed['backend_build_sha256']!=manifest['backend_build_sha256']
                    or observed['backend']['binary_sha256']!=manifest['binary_sha256']):
                raise ValueError('batch producer/backend differs from frozen source closure')
            if set(observed['files'])!={'initial.state','cases.bin','results.bin','raw/stella.log'}:
                raise ValueError('complete source evidence files required')
            for name,sha in observed['files'].items():
                if digest(path.parent/name)!=sha:raise ValueError('raw source batch changed')
            if (path.parent/'initial.state').read_bytes()!=initial:raise ValueError('batch preparation capsule mismatch')
            raw=(path.parent/'results.bin').read_bytes();cases=(path.parent/'cases.bin').read_bytes()
            validate_observation(raw,(path.parent/'raw/stella.log').read_text(),n,True)
            if len(cases)!=n*128:raise ValueError('partial original geometry fixtures')
            if loaded_px!=px:profile=profiles[px].read_bytes();loaded_px=px
            for index,(mode,x) in enumerate(entries[offset:offset+n]):
                if cases[index*128:(index+1)*128]!=make_case(manifest,base,px,manifest['ys'][yi],mode,x):
                    raise ValueError('source case is not the declared component coordinate')
                start=(yi*len(entries)+offset+index)*58
                if raw[index*78:index*78+58]!=profile[start:start+58]:
                    raise ValueError('profile differs from raw original observation')
            receipts+=1
    report={'cases':count,'receipts':receipts,'manifest_sha256':digest(root/'catalog.json'),
            'observed_workspace_states':[{'commit':commit,'dirty':dirty} for commit,dirty in sorted(global_workspaces)]}
    return manifest,profiles,report
