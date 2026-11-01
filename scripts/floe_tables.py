"""Losslessly compile a COMPLETE electrical catalog to bank-local pointer trees.

No horizontal class, glyph convolution or vertical interpolation is assumed.
The bit6 channel is retained in every near-actor record. Only the outside-actor
sentinel may be factored after all player positions and228 views agree.
"""
import argparse
import json
from pathlib import Path
import hashlib
import subprocess

from environment import ROOT
from floe_catalog import YS,validate_partitions,producer
from floe_truth import validate_row
from stella_floe import digest,control_pairs,validate_observation
from reference_inventory import verified_input


class BankPacker:
    def __init__(self,first=14):
        self.first=first;self.banks=[bytearray()];self.blobs={}

    def put(self,data):
        data=bytes(data)
        if not data or len(data)>16384:raise ValueError('nonempty bank-local blob required')
        if data in self.blobs:return self.blobs[data]
        if len(self.banks[-1])+len(data)>16384:self.banks.append(bytearray())
        bank=self.first+len(self.banks)-1
        if bank>255:raise ValueError('ASCII16 eight-bit bank range exceeded')
        address=0x8000+len(self.banks[-1]);self.banks[-1].extend(data)
        result=(bank,address);self.blobs[data]=result;return result


def pointer(location):
    bank,address=location
    if not 0<=bank<=255 or not 0x8000<=address<0xC000:raise ValueError('bank-local ASCII16 pointer required')
    return address.to_bytes(2,'little')+bytes([bank])


def shadow_byte(channel):
    if channel==bytes(29):return 0
    if channel==bytes([255])*28+bytes([15]):return 64
    raise ValueError('shadow channel is view-dependent; uniform factorization forbidden')


def verified_profiles(root):
    root=Path(root);manifest=json.loads((root/'catalog.json').read_text())
    controls=manifest['controls'];count=validate_partitions(manifest['partitions'],len(controls))
    if manifest.get('complete') is not True or manifest['cases']!=count or manifest['expected_cases']!=count or manifest['ys']!=list(YS) or manifest['views']!=228:
        raise ValueError('complete exact-domain catalog manifest required')
    if set(manifest['helpers'])!=set(producer()):raise ValueError('complete source helper closure required')
    original=verified_input(ROOT/'references/roms/frostbite.bin')
    if manifest['original']!=original or controls!=[list(pair) for pair in control_pairs((ROOT/'references/roms/frostbite.bin').read_bytes())] or manifest['player_x']!=list(range(160)) or manifest['floe_x']!=list(range(160)):
        raise ValueError('exact source identity and complete legal geometry domain required')
    if digest(root/'initial.state')!=manifest['initial_sha256'] or digest(root/'stella')!=manifest['binary_sha256']:
        raise ValueError('original capsule/backend identity changed')
    for name,sha in manifest['helpers'].items():
        blob=subprocess.check_output(['git','show',f'{manifest["producer_commit"]}:{name}'],cwd=ROOT,timeout=30)
        if hashlib.sha256(blob).hexdigest()!=sha:raise ValueError('catalog helper differs from committed producer')
    profiles={}
    for part in manifest['partitions']:
        directory=root/f'worker-{part["start"]:03d}-{part["stop"]:03d}'
        expected={f'player-{px:03d}.truth' for px in range(part['start'],part['stop'])}
        if set(part['profiles'])!=expected:raise ValueError('missing/extra canonical X profiles')
        for name,sha in part['profiles'].items():
            path=directory/name
            if digest(path)!=sha:raise ValueError('source profile hash mismatch')
            data=path.read_bytes()
            if len(data)!=len(YS)*len(controls)*160*58:raise ValueError('partial original profile')
            profiles[int(name[7:10])]=data
        expected_receipts={(directory/f'px-{px:03d}-y-{offset:02d}'/'observation.json').relative_to(root).as_posix()
                           for px in range(part['start'],part['stop']) for offset in range(0,len(YS),4)}
        if {r['path'] for r in part['receipts']}!=expected_receipts or len(part['receipts'])!=len(expected_receipts):raise ValueError('complete unique batch receipts required')
        for receipt in part['receipts']:
            path=root/receipt['path']
            if digest(path)!=receipt['sha256']:raise ValueError('observation receipt changed')
            observed=json.loads(path.read_text())
            if observed['helpers']!={key:value for key,value in manifest['helpers'].items() if key!='scripts/floe_catalog.py'} or observed['backend']['binary_sha256']!=manifest['binary_sha256']:
                raise ValueError('observation producer differs from catalog')
            px=int(path.parent.name[3:6]);yoffset=int(path.parent.name[9:11]);expected_cases=len(YS[yoffset:yoffset+4])*len(controls)*160
            if observed['cases']!=expected_cases or set(observed['files'])!={'initial.state','cases.bin','results.bin','raw/stella.log'}:
                raise ValueError('exact complete observation batch required')
            for name,sha in observed['files'].items():
                if digest(path.parent/name)!=sha:raise ValueError('raw source evidence changed')
            raw=(path.parent/'results.bin').read_bytes();log=(path.parent/'raw/stella.log').read_text()
            validate_observation(raw,log,expected_cases,True)
            if (path.parent/'initial.state').read_bytes()!=(root/'initial.state').read_bytes() or (path.parent/'cases.bin').stat().st_size!=expected_cases*128:
                raise ValueError('batch capsule/fixture completeness mismatch')
            profile=profiles[px]
            for index in range(expected_cases):
                if raw[index*78:index*78+58]!=profile[(yoffset*len(controls)*160+index)*58:(yoffset*len(controls)*160+index+1)*58]:
                    raise ValueError('profile differs from actual original observation')
    if set(profiles)!=set(range(160)):raise ValueError('all160 player positions required')
    return manifest,profiles


def compile_catalog(root,out):
    manifest,profiles=verified_profiles(root);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    controls=manifest['controls'];count=len(controls);packer=BankPacker();roots=bytearray();base=bytearray();records=set();row_nodes=set();profile_nodes=set()
    for control in range(count):
        sentinels=[]
        for fx in range(160):
            offset=(control*160+fx)*58;row=profiles[0][offset:offset+58];validate_row(row)
            if any(row[:29]):raise ValueError('outside-actor sentinel unexpectedly contacts player')
            sentinels.append(shadow_byte(row[29:]))
        base.extend(value|7 for value in sentinels)
        for px in range(160):
            profile=bytearray();data=profiles[px]
            for yi in range(len(YS)):
                pointers=bytearray()
                for dx in range(160):
                    fx=(px+dx)%160;offset=((yi*count+control)*160+fx)*58;row=data[offset:offset+58];validate_row(row)
                    if yi==0 and (any(row[:29]) or shadow_byte(row[29:])!=sentinels[fx]):raise ValueError('outside-actor sentinel depends on player X/view')
                    records.add(row);pointers.extend(pointer(packer.put(row)))
                row_nodes.add(bytes(pointers));profile.extend(pointer(packer.put(pointers)))
            profile_nodes.add(bytes(profile));roots.extend(pointer(packer.put(profile)))
    (out/'roots.bin').write_bytes(roots);(out/'base.bin').write_bytes(base)
    bank_lines=[]
    for index,data in enumerate(packer.banks):
        path=out/f'contacts-{index+14:03d}.bin';path.write_bytes(data+bytes([255])*(16384-len(data)))
        bank_lines.extend(('    ORG $8000',f'    INCBIN "{path.resolve()}"'))
    (out/'contact_banks.inc').write_text('\n'.join(bank_lines)+'\n')
    resident=['floe_roots:',f'    INCBIN "{(out/"roots.bin").resolve()}"','floe_base:',f'    INCBIN "{(out/"base.bin").resolve()}"',
              '    ALIGN 256','floe_control_index:']
    indices=bytearray([255]*256)
    for index,(a,b) in enumerate(controls):indices[a|(b>>4)]=index
    path=out/'controls.bin';path.write_bytes(indices);resident.append(f'    INCBIN "{path.resolve()}"')
    resident+=['floe_control_pointers:']
    for index in range(count):resident.append(f'    DW floe_roots+{index*160*3},floe_base+{index*160}')
    (out/'contact_resident.inc').write_text('\n'.join(resident)+'\n')
    result={'catalog_sha256':digest(Path(root)/'catalog.json'),'catalog_producer':manifest['producer_commit'],
            'cases':manifest['cases'],'controls':controls,'literal_views':228,'shadow_factorization':'outside-actor sentinel only; near-actor records retain both complete228-bit channels',
            'unique_player_records':len(records),'unique_position_rows':len(row_nodes),'unique_profiles':len(profile_nodes),
            'banks':len(packer.banks),'used_bytes':sum(len(data) for data in packer.banks),
            'files':{path.name:digest(path) for path in out.iterdir() if path.is_file()}}
    (out/'tables.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--catalog',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(compile_catalog(args.catalog,args.out),indent=2))
