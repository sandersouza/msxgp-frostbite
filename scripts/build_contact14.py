"""Repack exact contact indices into28-byte slots, preserving M-C runtime."""
import argparse
import json
from pathlib import Path
import subprocess

from environment import ROOT, verified_tool
from presentation_band_spike import COMPANIONS,PARENT_SHA,apply_patch,sha,verified_bytes
from presentation_contact14 import read_field,repack_bank
from render_build import symbols


def build(out, *, base=None, allocation=None):
    if out.exists():raise ValueError('immutable output already exists')
    historical = base is None
    base=ROOT/'outputs/presentation/playfield-m-c/build' if historical else Path(base)
    metadata=verified_bytes(base/'build.json',COMPANIONS['build.json']) if historical else (base/'build.json').read_bytes()
    symsraw=verified_bytes(base/'presentation.sym',COMPANIONS['presentation.sym']) if historical else (base/'presentation.sym').read_bytes()
    meta=json.loads(metadata)
    parent=verified_bytes(base/meta['rom']['filename'],PARENT_SHA)
    codec=meta['tables']['codec']
    if codec['record_count']>16384 or codec['block_bank']+((codec['block_count']+511)//512)!=codec['tree_bank']:
        raise ValueError('uint14 contiguous block arena precondition failed')
    out.mkdir(parents=True)
    (out/'input-meta.json').write_bytes(metadata);(out/'input.sym').write_bytes(symsraw)
    s=symbols(out/'input.sym')
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in sorted(s.items()) if '.' not in n)+'\n')
    source=ROOT/'src/presentation_contact14.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',
        f'--raw={out/"patch.bin"}',f'--sym={out/"patch.sym"}', f'--lst={out/"patch.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'patch.sym');code=(out/'patch.bin').read_bytes()
    rom=bytearray(parent);patches=[]
    def patch(at,old,new):patches.append(apply_patch(rom,at,old,new))
    def call(address):return bytes((205,address&255,address>>8))
    patch(q['c14_slot']-0x4000,bytes(len(code)),code)
    start,end=s['contact_compact']-0x4000,s['contact_compact.zero']-0x4000
    at=parent.index(call(s['contact_slot']),start,end)
    patch(at,call(s['contact_slot']),call(q['c14_slot']))
    old=bytes.fromhex('3a9ec7875f1600195e2356')
    patch(at+3,old,call(q['c14_read'])+bytes(len(old)-3))
    before,after=bytearray(),bytearray()
    block_banks=(codec['block_count']+511)//512
    arena=[]
    for b in range(block_banks):
        bank=codec['block_bank']+b
        oldbank=parent[bank*16384:(bank+1)*16384]
        local_count=min(512,codec['block_count']-b*512)
        data=repack_bank(oldbank,local_count,codec['record_count'])
        for slot in range(512):
            index=b*512+slot
            if index>=codec['block_count']:break
            at=(codec['block_bank']+b)*16384+slot*32
            raw=parent[at:at+32]
            values=[int.from_bytes(raw[i:i+2],'little') for i in range(0,32,2)]
            if any(v>=codec['record_count'] for v in values):raise ValueError('invalid original record reference')
            packed=data[slot*28:slot*28+28]
            decoded=b''.join(read_field(packed,i).to_bytes(2,'little') for i in range(16))
            if decoded!=raw:raise ValueError('lossy contact packing')
            before.extend(raw);after.extend(decoded)
        rom[bank*16384:(bank+1)*16384]=data
        arena.append(dict(bank=bank,original_sha256=sha(parent[bank*16384:(bank+1)*16384]),packed_sha256=sha(data)))
    allocation=json.loads(verified_bytes(ROOT/'outputs/presentation/direct-playfield-i/tables.json',COMPANIONS['i_allocation'])) if allocation is None else json.loads(Path(allocation).read_text())
    for bank,address,size in allocation['allocations']:
        at=bank*16384+address-0x8000
        if rom[at:at+size]!=parent[at:at+size]:
            raise ValueError('repacking changed a live I packet allocation')
    name='frostbite-contact14-internal.rom';(out/name).write_bytes(rom)
    (out/'expected-blocks.bin').write_bytes(before)
    (out/'presentation.sym').write_text(symsraw.decode()+'\n'+'\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in q.items() if n.startswith('c14_'))+'\n')
    for directory in ('geometry','template-assets'):
        (out/directory).symlink_to((base/directory).resolve(),target_is_directory=True)
    meta['version']='contact14-internal';meta['rom'].update(filename=name,sha256=sha(rom))
    meta['contact14']=dict(parent_rom_sha256=PARENT_SHA,resident_patches=patches,arena=arena,
        block_count=codec['block_count'],indices_verified=codec['block_count']*16,
        decoded_sha256=sha(after),original_indices_sha256=sha(before),
        sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (Path(__file__).resolve(),source,ROOT/'scripts/presentation_contact14.py')},
        scope='Internal lossless storage experiment; not human-testable delivery or gameplay acceptance.')
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),resident_bytes=len(code),indices_verified=codec['block_count']*16,reclaimed_bytes=codec['block_count']*4))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    build(parser.parse_args().out.resolve())
