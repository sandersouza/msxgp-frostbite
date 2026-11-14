"""Reconstruct native cold RAM and VRAM from source-declared initializers.

Never consume captured emulator state. This is an initialization candidate;
real cold boot and whole-game qualification remain mandatory.
"""
import argparse
import json
from pathlib import Path
from build_native_flat_image import digest
from native_flat_asm import assemble
from environment import ROOT
from render_build import symbols


def build(base,linked,out):
    base=base.resolve();linked=linked.resolve();out=out.resolve()
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());r=(base/m['rom']['filename']).read_bytes()
    l=json.loads((linked/'native-link.json').read_bytes());source=(linked/'native-image.bin').read_bytes()
    if digest(r)!=m['rom']['sha256'] or digest(source)!=l['image_sha256']:raise ValueError('bound sources required')
    s=symbols(base/'presentation.sym');ram=bytearray(65536);vram=bytearray(16384);recipes=[]
    def read(bank,a,n):return r[bank*16384+a-0x8000:bank*16384+a-0x8000+n]
    def write(a,data,owner):
        if not 0<=a<a+len(data)<=65536:raise ValueError('whole initializer domain required')
        ram[a:a+len(data)]=data;recipes.append(dict(address=a,bytes=len(data),owner=owner,sha256=digest(data)))
    # Exact source defaults, before overlaying source-qualified static objects.
    write(0xC800,bytes([128])*768,'initial NAME generation0')
    write(0xCD00,bytes([128])*768,'initial NAME generation1')
    write(0xD000,bytes([255])*2304,'unpublished physical keys')
    write(0xD900,bytes([255])*264,'unpublished footer keys')
    write(0xE5C0,bytes([255])*32,'unpublished floe tuples')
    write(0xE800,bytes([255])*128,'unpublished native enemy cache/metadata')
    from presentation_fixed import COUNTS
    write(0xCCA0,bytes(COUNTS*2),'unchanged fixed capacities')
    write(s['p_fx_force'],b'\xFF','initial forced fixed generation')
    write(s['p_bg_previous'],b'\xFF\xFF','initial background invalidation')
    write(0xF080,bytes([165])*640,'unused stack redzone bytes, excluding named objects')
    # Original analytic source fields and ROM-qualified preloads; never old
    # expanded render caches. The linked image replaces only their named holes.
    # These final immutable source regions include the later shore directory
    # patch. Historical intermediate cfi-data.bin predates that patch.
    for bank,address,ram_address,size in ((110,0xB800,0x0100,0x800),(111,0xB800,0x0900,0x700),(48,0xB800,0x2700,0x240)):
        write(ram_address,read(bank,address,size),'final analytic data bank'+str(bank))
    for node in ('compact_header_ram','compact_grid_palette','compact_enemy_ram'):
        for item in m[node]['initializers']:
            data=(base/item['file']).read_bytes()
            if len(data)!=item['size'] or digest(data)!=item['sha256']:raise ValueError('qualified initializer changed')
            write(item['ram_address'],data,node+'/'+item['file'])
    for bank,ram_address in ((46,0x3000),(47,0x3800)):
        write(ram_address,read(bank,0xB800,0x800),'final complete source query code bank'+str(bank))
    for item in l['patches']:
        if item['address']<0x4000:
            first=item['address'];write(first,source[first:first+item['size']],'native query interface/'+item['reason'])
    for first,last in ((0x4000,0xC000),(0xE900,0xE900+m['fixed_clock']['ram_code_bytes'])):
        write(first,source[first:last],'source-linked runtime code')
    for item in m['coherent_x']['auxiliary_code']:
        first=item['ram_address'];write(first,source[first:first+item['size']],'source-linked auxiliary code')
    for name,item in l['objects'].items():
        first=item['address'];data=source[first:first+item['size']]
        if digest(data)!=item['sha256']:raise ValueError('linked native object changed')
        write(first,data,'native/'+name)
    # Frozen VRAM storage occupies only its separately certified unused roles.
    for bank,(pgt,cgt,count) in enumerate(((0xB940,0xBA18,216),(0xBAF0,0xBB18,40),(0xBB40,0xBB70,48))):
        vram[0x400+bank*2048:0x400+bank*2048+count]=read(1,pgt,count)
        vram[0x2400+bank*2048:0x2400+bank*2048+count]=read(1,cgt,count)
    atlas=m['ice_atlas'];data=read(atlas['bank'],atlas['patterns_address'],len(atlas['ids'])*8)
    if digest(data)!=atlas['patterns_sha256']:raise ValueError('complete immutable white atlas changed')
    for bank in (1,2):
        for i,identifier in enumerate(atlas['ids']):
            a=bank*2048+identifier*8;vram[a:a+8]=data[i*8:i*8+8];vram[8192+a:8200+a]=bytes([244])*8
    footer=m['compact_footer_vram'];data=(base/footer['footer_tiles_file']).read_bytes()
    if digest(data)!=footer['footer_tiles_sha256']:raise ValueError('complete frozen footer changed')
    for i,item in enumerate(footer['allocation']):
        a,b=item['pattern'],item['color'];vram[a:a+8]=data[i*16:i*16+8];vram[b:b+8]=data[i*16+8:i*16+16]
    from presentation_credit_reference import compile_tiles,tile_colors
    credit,_=compile_tiles(False)
    for identifier,pattern in credit.items():
        a=4096+identifier*8;vram[a:a+8]=pattern;vram[8192+a:8200+a]=tile_colors(identifier)
    vram[0x1800:0x1B00]=vram[0x1C00:0x1F00]=bytes([128])*768
    vram[0x1B00]=208
    # Preserve the original unused HMOVE pattern; it is harmless without SAT
    # references and keeps startup representation complete.
    vram[0x3FE0:0x4000]=bytes([240])*16+bytes(16)
    write(0xC7E3,b'\xA5','exact188-tile VRAM preload validity')
    write(0xDA08,b'\0','accepted initial credit coarse phase')
    write(0x0FA0,b'\xFF'*4,'unpublished exceptional shore cache')
    pre=''.join(f'{n} EQU ${v:04X}\n' for n,v in s.items() if '.' not in n)
    code,z=assemble(out/'assembly','native-cold-boot',pre+(ROOT/'src/native_cold_boot.asm').read_text())
    size=z['nc_end']-z['nc_entry']
    if len(code)!=size+z['nc_clock_end']-z['nc_clock']:raise ValueError('exact transient and resident cold objects required')
    write(z['nc_entry'],code[:size],'source native cold transient')
    write(z['nc_clock'],code[size:],'native clock without BIOS/mapper dependencies')
    out.mkdir(parents=True,exist_ok=True)
    (out/'cold-ram.bin').write_bytes(ram);(out/'cold-vram.bin').write_bytes(vram)
    result=dict(complete=False,cold_initialization_candidate=True,emulator_state_used_as_input=False,
                parent_native_image_sha256=l['image_sha256'],parent_rom_sha256=m['rom']['sha256'],
                ram_sha256=digest(ram),vram_sha256=digest(vram),RAM_initializers=recipes,
                native_symbols={n:v for n,v in z.items() if n.startswith('nc_')},missing=['real native cartridge/DOS/BASIC loaders','cold source/graphics/full-game checks'])
    (out/'cold-image.json').write_text(json.dumps(result,indent=2)+'\n');print({k:result[k] for k in ('complete','ram_sha256','vram_sha256')})

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','linked','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.base,a.linked,a.out)
