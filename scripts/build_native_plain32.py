"""Package source-defined native RAM/VRAM into a complete Normal32K candidate."""
import argparse
import json
from pathlib import Path
import shutil
import re
import subprocess
from native_flat_asm import assemble
from build_native_flat_image import digest
from environment import ROOT


def overlap_slack(log):
    match=re.search(r'\(delta (\d+)\)',log)
    if not match or int(match[1])>3:raise ValueError('native low decoder requires measured backwards overlap slack <=3 bytes')
    return int(match[1])


def build(cold,out,compressor):
    cold=cold.resolve();out=out.resolve();compressor=compressor.resolve()
    if out.exists():raise ValueError('fresh output required')
    c=json.loads((cold/'cold-image.json').read_bytes());ram=(cold/'cold-ram.bin').read_bytes();video=(cold/'cold-vram.bin').read_bytes()
    if len(ram)!=65536 or len(video)!=16384 or digest(ram)!=c['ram_sha256'] or digest(video)!=c['vram_sha256']:raise ValueError('bound complete source cold images required')
    pin=subprocess.check_output(['git','-C',str(compressor.parent),'rev-parse','HEAD'],text=True).strip()
    if pin!='ecde3a2ae05061fe06469ed46df81a33b7de7d86':raise ValueError('audited Seaquest ZX0 source revision required')
    out.mkdir(parents=True)
    for name,data in (('cold-low',ram[:0xF300]),('cold-gfx-high',video+ram[0xF380:0xFFF4])):
        (out/(name+'.bin')).write_bytes(data)
        result=subprocess.run([str(compressor),'-b','-f',str(out/(name+'.bin')),str(out/(name+'.zx0'))],capture_output=True,text=True)
        (out/(name+'-compress.log')).write_text(result.stdout+result.stderr)
        if result.returncode:raise ValueError('native payload compression failed')
        if name=='cold-low':
            overlap_slack(result.stdout+result.stderr)
    low=(out/'cold-low.zx0').read_bytes();gfx=(out/'cold-gfx-high.zx0').read_bytes()
    (out/'native-loader.inc').write_text(f'MAIN_SIZE EQU {len(low)}\nGFX_SIZE EQU {len(gfx)}\n')
    # Assembler paths are bound and explicit; no globally installed ZX0 needed.
    source=(ROOT/'src/native_plain32.asm').read_text().replace('"native-loader.inc"',f'"{out/"native-loader.inc"}"')
    for name in ('cold-low.zx0','cold-gfx-high.zx0'):source=source.replace('"'+name+'"',f'"{out/name}"')
    rom,s=assemble(out,'frostbite-native-32k',source)
    if len(rom)!=32768 or rom[:2]!=b'AB':raise ValueError('complete Normal32K cartridge required')
    (out/'FROSTBIT.ROM').write_bytes(rom)
    result=dict(complete=False,testable_candidate=False,format='Normal32K',mapper='none',ROM_bytes=len(rom),rom_sha256=digest(rom),
                cold_RAM_sha256=digest(ram),cold_VRAM_sha256=digest(video),compressed_low_bytes=len(low),compressed_gfx_high_bytes=len(gfx),
                payloads_bytes=len(low)+len(gfx),header_bytes=s['rom_header_end']-0x4000,stage2_bytes=s['rom_end']-s['rom_stage2'],
                payload_padding_bytes=0xBEE0-s['gfx_data']-len(gfx),symbols=s,compressor_commit=pin,compressor_sha256=digest(compressor.read_bytes()),
                source_files={n:digest((ROOT/n).read_bytes()) for n in ('scripts/build_native_plain32.py','src/native_plain32.asm','src/native_loader_ram.asm','src/native_loader_reloc.asm','src/third_party/zx0/dzx0_standard_back.asm','src/third_party/zx0/LICENSE')},
                missing=['real Normal cartridge cold boot/whole-game validation','native COM/BIN loaders','accepted cadence recovery','review/release/integration'])
    (out/'native32.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:result[k] for k in ('complete','ROM_bytes','rom_sha256','payloads_bytes','header_bytes','stage2_bytes','payload_padding_bytes')})

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('cold','out','compressor'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.cold,a.out,a.compressor)
