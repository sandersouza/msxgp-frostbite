"""Bind renderer evidence to the exact ROM, principal receipt and raw buffers."""
import hashlib
import json
from pathlib import Path
import re


def sha(data):return hashlib.sha256(data).hexdigest()


def validate_artifacts(directory,artifacts,required):
    if not isinstance(artifacts,dict) or not set(required)<=artifacts.keys():
        raise ValueError('missing required audited artifacts')
    root=Path(directory).resolve()
    for name,expected in artifacts.items():
        path=root/name
        if (not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected)
                or not path.resolve().is_relative_to(root) or not path.is_file()
                or sha(path.read_bytes())!=expected):
            raise ValueError('audited artifact identity changed: '+name)


def validate_scene_receipt(directory,rom,count,kind):
    receipt=json.loads((directory/'check.json').read_text())
    flags=['full_source_pixels_accepted','fixed_role_ownership_accepted',
        'physical_name_pages_accepted','integrated_dirty_states_accepted','dirty_row_list_accepted',
        'prepared_band_ownership_accepted' if kind=='prepared' else 'shared_ice_references_accepted']
    if (receipt.get('complete')is not True or receipt.get('cases')!=count
            or receipt.get('different_frames')!=0 or receipt.get('rom_sha256')!=rom
            or any(receipt.get(k)is not True for k in flags)):
        raise ValueError('scene receipt ROM/count/protections differ')
    validate_artifacts(directory,receipt.get('artifacts'),('captures.bin','cases.bin','timing.tsv',
        'ownership.bin','expected.tms','scenes.bin','band-records.bin' if kind=='prepared' else 'residency.bin'))
    return receipt


def validate_probe(directory,rom,frames):
    probe=json.loads((directory/'check.json').read_text())
    route=json.loads((directory/'route-research.json').read_text())
    if (probe.get('rom_sha256')!=rom or probe.get('frames')!=frames
            or route.get('rom_sha256')!=rom or route.get('frames')!=frames
            or route.get('complete')is not True
            or route.get('probe_receipt_sha256')!=sha((directory/'check.json').read_bytes())
            or route.get('expanded_private_profiler_sha256')!='6ef44410eb45ad5f5aba995dfda913f9336a6354245931b949ca9e83c732b5ed'):
        raise ValueError('principal route/probe receipt differs')
    validate_artifacts(directory,probe.get('artifacts'),('captures.bin','cycles.tsv','phases.tsv',
        'costs.tsv','traffic.tsv','route-cpu.bin'))
    return probe


def owner_binding(directory,rom,frames,kind):
    validate_probe(directory,rom,frames)
    names=('captures.bin','band-records.bin','fill-events.tsv') if kind=='prepared' else ('captures.bin','residency.bin')
    return dict(rom_sha256=rom,probe_receipt_sha256=sha((directory/'check.json').read_bytes()),
        artifacts={name:sha((directory/name).read_bytes()) for name in names})


def validate_owner_receipt(directory,rom,frames,kind):
    receipt=json.loads((directory/(kind+'-check-v2.json')).read_text())
    flags=('physical_owner_audits','active_full_page_protection','direct_fill_io_instrumented') if kind=='prepared' else ('physical_reference_protection',)
    if (receipt.get('complete')is not True or receipt.get('frames')!=frames
            or receipt.get('rom_sha256')!=rom
            or receipt.get('probe_receipt_sha256')!=sha((directory/'check.json').read_bytes())
            or any(receipt.get(k)is not True for k in flags)):
        raise ValueError('physical-owner ROM/probe/protections differ')
    required=('captures.bin','band-records.bin','fill-events.tsv') if kind=='prepared' else ('captures.bin','residency.bin')
    validate_artifacts(directory,receipt.get('artifacts'),required)
    return receipt
