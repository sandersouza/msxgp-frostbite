"""Native DOS1 COM and Disk BASIC BINs from the exact same cartridge payload."""
import argparse
import json
from pathlib import Path
import shutil
import struct
from native_flat_asm import assemble
from build_native_flat_image import digest
from environment import ROOT


def shared_payloads(cartridge,m):
    rom=(cartridge/'FROSTBIT.ROM').read_bytes()
    if len(rom)!=32768 or rom[:2]!=b'AB' or digest(rom)!=m['rom_sha256']:
        raise ValueError('bound real native cartridge required')
    result=[]
    for stem,field,label in (('cold-low','compressed_low_bytes','main_data'),('cold-gfx-high','compressed_gfx_high_bytes','gfx_data')):
        data=(cartridge/(stem+'.zx0')).read_bytes();start=m['symbols'][label]-0x4000
        if len(data)!=m[field] or not 0<=start<start+len(data)<=32768 or rom[start:start+len(data)]!=data:
            raise ValueError('complete byte-exact shared native payload required: '+stem)
        result.append(data)
    return tuple(result)


def build(cartridge,out):
    cartridge=cartridge.resolve();out=out.resolve()
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((cartridge/'native32.json').read_bytes())
    low,gfx=shared_payloads(cartridge,m)
    out.mkdir(parents=True)
    for name in ('cold-low.zx0','cold-gfx-high.zx0'):shutil.copyfile(cartridge/name,out/name)
    # Same cold graphics/high initializer and the exact decoder/relocator. The
    # BASIC file cannot occupy BIOS work area, so its companion arrives in VRAM.
    pre=f'MAIN_SIZE EQU {len(low)}\nGFX_SIZE EQU {len(gfx)}\n'
    helper,h=assemble(out,'basic-ram-helper',' ORG $E000\n'+pre+' INCLUDE "native_loader_ram.asm"\n')
    if len(helper)>256:raise ValueError('bounded high helper required')
    decoder,d=assemble(out,'disk-decoder',' ORG $F312\n INCLUDE "third_party/zx0/dzx0_standard_back.asm"\n')
    reloc,z=assemble(out,'disk-relocator',' ORG $F303\n INCLUDE "native_loader_reloc.asm"\n')
    if len(decoder)!=69 or len(reloc)!=14:raise ValueError('exact audited decoder/relocation ABI required')
    include=out/'native-loader.inc';include.write_text(pre+f'BASIC_HELPER_SIZE EQU {len(helper)}\n')
    (out/'basic-low-tail.zx0').write_bytes(low[8192:])
    symbols={}
    for kind,source,target in (('dos','native_dos.asm','FROSTBIT.COM'),('basic','native_basic.asm','FROSTBIT.BIN')):
        text=(ROOT/'src'/source).read_text().replace('"native-loader.inc"',f'"{include}"')
        for name in ('cold-low.zx0','cold-gfx-high.zx0','basic-low-tail.zx0'):text=text.replace('"'+name+'"',f'"{out/name}"')
        data,s=assemble(out,kind,text);symbols[kind]=s
        if kind=='basic':data=struct.pack('<BHHH',254,0x8800,0x8800+len(data)-1,0x8800)+data
        (out/target).write_bytes(data)
    companion=bytearray(0x2E00+len(reloc));companion[:8192]=low[:8192];companion[0x2000:0x2000+len(gfx)]=gfx
    companion[0x2C00:0x2C00+len(helper)]=helper;companion[0x2D00:0x2D00+len(decoder)]=decoder;companion[0x2E00:]=reloc
    (out/'FBGFX.BIN').write_bytes(struct.pack('<BHHH',254,0,len(companion)-1,0)+companion)
    (out/'FROSTBIT.BAS').write_bytes(b'10 CLEAR 200,&H87FF:SCREEN 2\r\n20 BLOAD"FBGFX.BIN",S\r\n30 BLOAD"FROSTBIT.BIN",R\r\n\x1A')
    files={n:dict(size=(out/n).stat().st_size,sha256=digest((out/n).read_bytes())) for n in ('FROSTBIT.COM','FROSTBIT.BIN','FBGFX.BIN','FROSTBIT.BAS')}
    result=dict(complete=False,native_disk_candidates=True,parent_ROM_sha256=m['rom_sha256'],cold_RAM_sha256=m['cold_RAM_sha256'],cold_VRAM_sha256=m['cold_VRAM_sha256'],
                files=files,symbols=symbols,BASIC_companion_required='FBGFX.BIN',DOS_single_file=True,
                no_original_ROM_or_mapper_required=True,OS_return=False,exit_method='machine RESET',
                missing=['real MSX-DOS1 and Disk BASIC boot/source/pixel checks','accepted cadence recovery','review/release/integration'])
    (out/'native-disk.json').write_text(json.dumps(result,indent=2)+'\n');print(dict(complete=False,files=files))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('cartridge','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.cartridge,a.out)
