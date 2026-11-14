"""Native exact phase0 packet reconstruction; no runtime promotion implied."""
import argparse
import hashlib
import json
from pathlib import Path

from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def packet_data(rom):
    patterns=[];lookup={};indices=bytearray();directory=bytearray();counts=bytearray();expected=bytearray()
    for bank in range(35,45):
        for variant in range(16):
            at=bank*16384+0x3800+variant*128;packet=rom[at:at+128];count=packet[115]
            if not 1<=count<=8:raise ValueError('bounded phase0 PGT count required')
            counts.append(count);directory.extend(len(indices).to_bytes(2,'little'))
            for p in range(count):
                pattern=packet[p*8:p*8+8]
                if pattern not in lookup:lookup[pattern]=len(patterns)*8;patterns.append(pattern)
                indices.extend(lookup[pattern].to_bytes(2,'little'))
            expected.extend(packet[:count*8]+bytes([165])*(64-count*8))
    if len(patterns)!=289 or len(indices)!=1894:raise ValueError('complete phase0 packet domain changed')
    return dict(patterns=b''.join(patterns),indices=bytes(indices),directory=bytes(directory),counts=bytes(counts)),bytes(expected)


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    assets,expected=packet_data(rom);out.mkdir(parents=True)
    for n,b in assets.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF',' INCLUDE "compact_floe_packet.asm"',' ASSERT $ <= $5000',' DS $5000-$,$FF']
    for n in ('directory','counts','indices','patterns'):asm += [f'cp_{n}:',f' INCBIN "{out/(n+".bin")}"']
    asm += [' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',b''.join(i.to_bytes(2,'little') for i in range(160)),expected,
        input_address=0xC7D0,input_stride=2,output_address=0xC480,output_stride=64,entry_name='cp_build',end_name='cp_end',writes=((0xC480,0xC4BF),))
    names=('scripts/compact_floe_packet_probe.py','src/compact_floe_packet.asm')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,prepared_packet_bytes=20480,live_pattern_bytes=7576,
        compact_data_bytes=sum(map(len,assets.values())),original_owner_pointer_records_retained_bytes=640,
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All160 phase0 PGT records, unused output poison and ABI/write guards; component only, no whole-frame cadence claim.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
