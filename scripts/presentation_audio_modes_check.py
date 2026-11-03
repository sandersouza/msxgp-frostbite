"""Compile the unchanged pinned Stella oscillator and verify all512 periods.

Only unused serialization interfaces are stubbed. The actual AudioChannel
implementation is compiled directly from its verified upstream Git blobs.
"""
import argparse
import hashlib
import json
from math import isqrt
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from presentation_audio import MODE_CYCLES
from reference_traces import private_output

REVISION='d55b1aec0d067a4c901a6dcdf81cb8f579685659'
FILES=('scripts/presentation_audio_modes_check.py','scripts/presentation_audio.py','scripts/environment.py','scripts/reference_traces.py')
SAMPLES=36864
WARMUP=4096


def validate_mode(data,control,frequency):
    if (not isinstance(data,bytes) or len(data)!=SAMPLES or set(data)-{0,1}
            or type(control)is not int or not 0<=control<16 or type(frequency)is not int or not 0<=frequency<32):
        raise ValueError('whole binary oscillator stream and bounded chip mode required')
    period=1 if control in (0,11) else MODE_CYCLES[control]*(frequency+1);steady=data[WARMUP:]
    if steady[period:]!=steady[:-period]:raise ValueError('actual oscillator differs from the declared repetition period')
    divisors={d for n in range(1,isqrt(period)+1) if period%n==0 for d in (n,period//n)}-{period}
    if any(steady[d:]==steady[:-d] for d in divisors):raise ValueError('declared oscillator period is not the minimum')
    if control in (0,11) and steady!=bytes([1])*len(steady):raise ValueError('DC mode did not retain its high output')
    return period


def check(out,backend):
    sha=lambda data:hashlib.sha256(data).hexdigest();producer={name:sha((ROOT/name).read_bytes()) for name in FILES}
    source=Path(backend).resolve().parent;prefix='src/emucore/tia/';consumed={}
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()!=REVISION:raise ValueError('pinned Stella revision required')
    for name in ('AudioChannel.cxx','AudioChannel.hxx','Audio.hxx'):
        path=source/prefix/name;expected=subprocess.check_output(['git','show',f'{REVISION}:{prefix}{name}'],cwd=source)
        if path.read_bytes()!=expected:raise ValueError('original oscillator source changed')
        consumed[str(path)]=sha(expected)
    compiler=shutil.which('clang++')
    if not compiler:raise ValueError('macOS command-line C++ compiler required')
    compiler=Path(compiler).resolve();consumed[str(compiler)]=sha(compiler.read_bytes())
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);stubs=out/'stubs';stubs.mkdir()
    (stubs/'bspf.hxx').write_text('#pragma once\n#include <cstdint>\n#include <iostream>\nusing uInt8=uint8_t;\nusing std::cerr;\n')
    (stubs/'Serializable.hxx').write_text('#pragma once\nclass Serializer {public:void putByte(uInt8){} void putBool(bool){} uInt8 getByte(){return 0;} bool getBool(){return false;}};\nclass Serializable {public:virtual ~Serializable()=default;virtual bool save(Serializer&)const=0;virtual bool load(Serializer&)=0;};\n')
    (out/'audit.cxx').write_text('''#include "AudioChannel.hxx"
#include <cstdio>
int main(){
 for(int mode=0;mode<16;mode++)for(int frequency=0;frequency<32;frequency++){
  AudioChannel channel;channel.reset();channel.audc(mode);channel.audf(frequency);channel.audv(15);
  for(int tick=0;tick<36864;tick++){channel.phase0();channel.phase1();std::putchar(channel.actualVolume()?1:0);}
 }
}
''')
    command=[str(compiler),'-std=c++20','-O2',f'-I{stubs}',f'-I{source/prefix}',str(out/'audit.cxx'),str(source/prefix/'AudioChannel.cxx'),'-o',str(out/'audit')]
    result=subprocess.run(command,capture_output=True,text=True,timeout=60);(out/'compiler.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise ValueError('original oscillator compiler failed: '+result.stderr[-1500:])
    with (out/'modes.bin').open('wb') as output:
        executed=subprocess.run([str(out/'audit')],stdout=output,stderr=subprocess.PIPE,timeout=60)
    if executed.returncode or executed.stderr:raise ValueError('original oscillator execution failed')
    raw=(out/'modes.bin').read_bytes()
    if len(raw)!=512*SAMPLES:raise ValueError('incomplete oscillator cross product')
    cases=[]
    for control in range(16):
        for frequency in range(32):
            index=control*32+frequency;period=validate_mode(raw[index*SAMPLES:(index+1)*SAMPLES],control,frequency)
            cases.append({'control':control,'frequency':frequency,'phase_pairs_per_repeat':period})
    if (any(sha((ROOT/name).read_bytes())!=value for name,value in producer.items())
            or any(sha(Path(name).read_bytes())!=value for name,value in consumed.items())):raise ValueError('oscillator producers or inputs changed')
    report={'complete':True,'cases':cases,'case_count':512,'source_revision':REVISION,'warmup_phase_pairs':WARMUP,'checked_phase_pairs_per_case':SAMPLES-WARMUP,
        'producer_files':producer,'input_files':consumed,'compiler_command':command,'artifacts':{str(p.relative_to(out)):sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()},
        'native_accepted':False,'frame_deadline_accepted':False,
        'scope':'Actual unchanged pinned Stella oscillator, all16 AUDC modes and32 AUDF values; steady minimum output repetition periods. Serialization stubs are unused by oscillator stepping. Average phase-pair rate3579545/114. No AY timbre/volume/phase/native/combined/human acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','case_count','checked_phase_pairs_per_case')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--backend',type=Path,required=True)
    check(**vars(p.parse_args()))
