"""Prove compact native footer addressing or all sparse temperature records."""
import argparse
import json
from pathlib import Path
from compact_native_fixture import run,sha
from compact_live_probe import CONTROL_SHA
from compact_temperature_probe import planes
from environment import ROOT
from reference_traces import private_output


def check(build,out,kind):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((build/'build.json').read_bytes())
    if sha(build/m['rom']['filename'])!=m['rom']['sha256']:raise ValueError('bound current input required')
    out.mkdir(parents=True)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',' DS $4100-$,$FF','nt_entry:',' LD A,($C7B4)']
    if kind=='footer':
        data=(build/'fv-directory.bin').read_bytes();values=[int.from_bytes(data[i:i+2],'little') for i in range(0,len(data),2)];runs=[]
        for i,address in enumerate(values):
            if runs and address==runs[-1][2]+(i-runs[-1][0])*8:runs[-1][1]+=1
            else:runs.append([i,1,address])
        if len(runs)!=9 or len(values)!=188:raise ValueError('complete certified footer family required')
        packed=b''.join(bytes((first+count,))+((address-first*8)&65535).to_bytes(2,'little') for first,count,address in runs)
        (out/'runs.bin').write_bytes(packed)
        asm+=[' CALL nr_address',' LD ($C500),DE',' RET',' INCLUDE "native_footer_address.asm"','nt_end:',
              ' ASSERT $ <= $5000',' DS $5000-$,$FF','nr_runs:',f' INCBIN "{out/"runs.bin"}"',' DS $C000-$,$FF']
        inputs=bytes(range(188));expected=data;output=0xC500;stride=2;writes=((0xC500,0xC501),);files=['src/native_footer_address.asm']
    else:
        control=ROOT/'outputs/presentation/credit-reference-at/build-final';cm=json.loads((control/'build.json').read_bytes());r=(control/cm['rom']['filename']).read_bytes()
        if sha(control/cm['rom']['filename'])!=CONTROL_SHA:raise ValueError('complete original burst oracle required')
        tens,units,expected=planes(r);packed=b''.join(tens[i:i+9] for i in range(0,len(tens),16))
        (out/'tens.bin').write_bytes(packed);(out/'units.bin').write_bytes(units)
        asm+=[' INCLUDE "native_temperature.asm"','nt_end:',' ASSERT $ <= $5000',' DS $5000-$,$FF',
              'nt_tens:',f' INCBIN "{out/"tens.bin"}"','nt_units:',f' INCBIN "{out/"units.bin"}"',
              'nt_units_directory:',' DW '+','.join(f'nt_units+{i*32}' for i in range(16)),' DS $C000-$,$FF']
        inputs=bytes(range(256));output=0xC480;stride=32;writes=((0xC480,0xC49F),);files=['src/native_temperature.asm']
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7B4,input_stride=1,
               output_address=output,output_stride=stride,entry_name='nt_entry',end_name='nt_end',writes=writes)
    result.update(kind=kind,input_rom_sha256=m['rom']['sha256'],compact_table_bytes=len(packed),
                  sources={n:sha(ROOT/n) for n in ['scripts/native_small_tables_probe.py']+files},
                  scope='Every frozen footer address or all256 independent accepted temperature bursts, native ABI/bounded writes; component only.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--kind',choices=('footer','temperature'),required=True)
    a=p.parse_args();check(a.build,a.out,a.kind)
