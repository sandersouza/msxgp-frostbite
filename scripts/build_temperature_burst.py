"""Replace eligible AL temperature updates with four exact prepared streams."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from render_build import symbols
from presentation_temperature_burst import burst_table
sha=lambda b:hashlib.sha256(b).hexdigest()

def build(base,out):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_text());files=dict(m['source_files']);parent=(base/m['rom']['filename']).read_bytes()
    if sha(parent)!=m['rom']['sha256']or not m.get('border_closure')or m.get('temperature_burst'):raise ValueError('verified closed-edge parent required')
    if any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('parent source closure changed')
    programs=burst_table(b''.join(parent[b*16384+0x3800:(b+1)*16384]for b in range(127,131)))
    if sha(programs)!='58307095f471a9731bb4ed6a6e9ff236be81844faf2b16fc5af3fb91807aef0f':raise ValueError('source-derived burst program identity differs')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
        elif p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    s=symbols(base/'presentation.sym');(out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in s.items()if'.'not in n)+'\n');source=ROOT/'src/presentation_temperature_burst.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"temperature-burst-code.bin"}',f'--sym={out/"temperature-burst.sym"}',str(source)],cwd=ROOT,capture_output=True,text=True);(out/'temperature-burst-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'temperature-burst.sym');code=(out/'temperature-burst-code.bin').read_bytes()
    if q['burst_body']!=s['al_body']or len(code)>2048:raise ValueError('body allocation changed')
    rom=bytearray(parent);patches=[]
    for bank,data in [(127+i,programs[i*2048:(i+1)*2048])for i in range(4)]+[(131,code+bytes([255])*(2048-len(code)))]:
        at=bank*16384+0x3800;old=bytes(rom[at:at+2048]);rom[at:at+2048]=data;patches.append(dict(offset=at,size=2048,before_sha256=sha(old),after_sha256=sha(data)))
        name=f'assets-{bank:03d}.bin';blob=bytes(rom[bank*16384:(bank+1)*16384])
        for section in('template_assets','static_presentation'):
            if name in m[section]['files']:m[section]['files'][name]=sha(blob);(out/'template-assets'/name).write_bytes(blob)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    assert rom[0x69fc-0x4000:0x6a32-0x4000]==parent[0x69fc-0x4000:0x6a32-0x4000]
    assert rom[115*16384:116*16384]==parent[115*16384:116*16384]
    for p in(Path(__file__),source,ROOT/'scripts/presentation_temperature_burst.py',ROOT/'tests/test_presentation_temperature_burst.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='temperature-burst-ao-internal',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Exact four-stream temperature updates, packed P0/full bear and lower-edge closure. Original mechanics/clock/controls/PSG preserved.'))
    m['temperature_burst']=dict(parent_rom_sha256=m['rom']['sha256'],patches=patches,programs_sha256=sha(programs),programs=256,body_bytes=len(code),vdp_stream_lengths=[1,1,1,24],gate54_and_ram14_byte_identical=True,zero_padding_source_constructor_required=True,new_ram_bytes=0,new_vram_bytes=0)
    s.update({n:v for n,v in q.items()if n.startswith('burst_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n');(out/'temperature-burst-programs.bin').write_bytes(programs)
    name='frostbite-temperature-burst-ao.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),body_bytes=len(code)));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.base,a.out)
