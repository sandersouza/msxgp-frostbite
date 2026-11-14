"""Execute the source-linked flat overlay after genuine old cold init.

This diagnostic explicitly uses legacy ROM startup. It does not qualify a
Normal cartridge, COM or BIN loader. Original source/graphics/physical/IRQ
oracles run on actual all-RAM code, with exact immutable overlay guards.
"""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import subprocess
import re
import compact_game_probe
import presentation_fixed_clock_probe as clock
import presentation_prepared_check as prepared
import presentation_prepared_ownership as ownership
import presentation_ice_atlas_check as atlas
import native_bear_keys
from native_unused_keys import extents,audit_and_shadow
from presentation_fast_model import prepare
from presentation_palette import audit_palette
from render_build import symbols
from environment import ROOT
from build_native_flat_image import digest


def check(base,linked,out,mode,cold=None,cartridge=None,profile=False):
    producer=digest(Path(__file__).read_bytes())
    base,linked,out=base.resolve(),linked.resolve(),out.resolve()
    m=json.loads((base/'build.json').read_bytes());l=json.loads((linked/'native-link.json').read_bytes())
    image=(linked/'native-image.bin').read_bytes()
    if digest(image)!=l['image_sha256'] or l['input_rom_sha256']!=m['rom']['sha256'] or l['remaining_interfaces']:
        raise ValueError('complete source-bound diagnostic interfaces required')
    s=symbols(base/'presentation.sym');rom=(base/m['rom']['filename']).read_bytes()
    cold_meta=None
    native_cart_bytes=None
    if cartridge:
        cartridge=cartridge.resolve();native_cart_bytes=cartridge.read_bytes()
        if not cold or len(native_cart_bytes)!=32768 or native_cart_bytes[:2]!=b'AB':raise ValueError('real Normal32K and matching cold manifest required')
    if cold:
        cold=cold.resolve();cold_meta=json.loads((cold/'cold-image.json').read_bytes())
        image=(cold/'cold-ram.bin').read_bytes();video=(cold/'cold-vram.bin').read_bytes()
        if digest(image)!=cold_meta['ram_sha256'] or digest(video)!=cold_meta['vram_sha256'] or cold_meta['parent_native_image_sha256']!=l['image_sha256']:
            raise ValueError('source-declared complete cold images required')
    # Only explicit source-linked overlays are installed. Existing lower/upper
    # startup products remain untouched unless a named object/patch owns them.
    ranges=[(0x4000,0xC000),(0x3000,0x3300)]
    ranges += [(r['address'],r['address']+r['size']) for r in l['objects'].values()]
    ranges += [(r['address'],r['address']+r['size']) for r in l['patches'] if r['address']>=0xC000]
    from native_flat_catalog import merged
    ranges=[(0,65536)] if cold else merged(ranges)
    permitted={a for first,last in extents() for a in range(first,last)}
    keyobjects=[r for r in l['objects'].values() if r['address'] in permitted]
    original=(ROOT/'references/roms/frostbite.bin').read_bytes();cfg=json.loads((ROOT/'references/presentation-assets-config.json').read_bytes())
    tables=prepare(original,audit_palette(ROOT/cfg['palette']),base/'geometry')
    backgrounds=[{128+i:tables['background']['patterns'][bank][i*8:i*8+8]+tables['background']['colors'][bank][i*8:i*8+8]
                  for i in range(tables['background']['tiles_per_bank'][bank])} for bank in range(3)]
    @lru_cache(None)
    def native(bank,key):return native_bear_keys.construct(original,bank,key,backgrounds[bank])
    old_owner=atlas.audit_row;old_decorate=ownership.decorate_owners
    count=dict(keys=0,rows=0)
    def decorate(raw,*args,**kw):
        memory=bytearray([255]*65536);memory[0xD000:0xD900]=raw[1536:3840]
        shadow=audit_and_shadow(memory,keyobjects)
        data=bytearray(raw);data[1536:3840]=shadow[0xD000:0xD900]
        return old_decorate(bytes(data),*args,**kw)
    def owners(raw,vram,tile,**kw):
        count['rows']+=1
        for page in range(2):
            for bank in range(3):
                for slot in range(64):
                    at=1536+((page*3+bank)*64+slot)*6;key=raw[at:at+6]
                    if key[5]==10:
                        native_bear_keys.validate_role(bank,page*64+slot,key);count['keys']+=1
        extended=lambda bank,key:native(bank,key) if key[5]==10 else tile(bank,key)
        try:return old_owner(raw,vram,extended,native_bear=True,**kw)
        except ValueError as error:
            match=re.search(r'bank(\d+) id(\d+)',str(error))
            if match:
                bank,identifier=map(int,match.groups());page,slot=divmod(identifier,64)
                at=1536+((page*3+bank)*64+slot)*6;key=raw[at:at+6]
                pgt=bank*2048+identifier*8
                (out/'owner-diff.json').write_text(json.dumps(dict(row=count['rows'],bank=bank,identifier=identifier,key=key.hex(),
                    expected=extended(bank,key).hex(),actual=(vram[pgt:pgt+8]+vram[8192+pgt:8200+pgt]).hex()),indent=2))
            raise
    atlas.audit_row=owners
    old_decorators=(ownership.decorate_owners,clock.decorate_owners,prepared.decorate_owners)
    ownership.decorate_owners=clock.decorate_owners=prepared.decorate_owners=decorate
    old_run=subprocess.run
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p=Path(args[args.index('-script')+1]);text=p.read_text()

            # Replace historical whole-code comparisons with the exact source-
            # linked bytes, retaining their original ranges and fault checks.
            for first,last in [(0xE900,0xE900+m['fixed_clock']['ram_code_bytes'])]+[(r['ram_address'],r['ram_address']+r['size']) for r in m['coherent_x']['auxiliary_code']]:
                if first==0xE900:old=rom[115*16384+0x3800:115*16384+0x3800+last-first]
                else:
                    r=next(r for r in m['coherent_x']['auxiliary_code'] if r['ram_address']==first)
                    off=r['bank']*16384+r['rom_address']-0x8000;old=rom[off:off+last-first]
                text=text.replace(old.hex(),image[first:last].hex())
            zone=bytearray([165]*640)
            for first,last in ranges:
                a1,b1=max(first,0xF080),min(last,0xF300)
                if a1<b1:zone[a1-0xF080:b1-0xF080]=image[a1:b1]
            if cold and mode!='matrix':
                needle=f"debug set_bp {s['native_reset_done']} "
                if text.count(needle)!=1:raise ValueError('unique original source-reset checkpoint required')
                text=text.replace(needle,f"debug set_bp {cold_meta['native_symbols']['nc_source_ready']} ")
                text=text.replace(' debug write_block memory 0xF080 [string repeat [binary format c 165] 640]\n','')
            if mode=='matrix':
                crc_pattern=r'if \{\[debug read_block memory 0xE100 256\] ne \[binary format H\* \{[0-9a-f]+\}\]\} \{fail_matrix crc-shadow\}'
                matches=list(re.finditer(crc_pattern,text))
                if len(matches)!=2:raise ValueError('exact boot and runtime CRC guards required')
                replacement='if {[debug read_block memory 0xE100 256] ne [binary format H* '+image[0xE100:0xE200].hex()+']} {fail_matrix native-former-CRC-owner}'
                # Warm experiment reaches the old boot guard before takeover.
                # A real cold cartridge owns this area from its first entry.
                for match in reversed(matches if cold else matches[:1]):
                    text=text[:match.start()]+replacement+text[match.end():]
                needle='[string repeat [binary format c 165] 0x280]} {fail_matrix heap-redzone}'
                if text.count(needle)!=1:raise ValueError('unique native matrix redzone guard required')
                text=text.replace(needle,'[binary format H* '+zone.hex()+']} {fail_matrix native-allocation-redzone}')
            else:
                needle='[string repeat [binary format c 165] 640]} {fail redzone}'
                if text.count(needle)!=1:raise ValueError('unique historical redzone guard required')
                text=text.replace(needle,'[binary format H* '+zone.hex()+']} {fail native-allocation-redzone}')
            installs='\n'.join(f' debug write_block {{Main RAM}} {first} [binary format H* {image[first:last].hex()}]' for first,last in ranges)
            fail='fail_matrix' if mode=='matrix' else 'fail'
            guards='\n'.join(f'debug set_watchpoint write_mem {{{r["address"]} {r["address"]+r["size"]-1}}} {{$::native_flat_ready}} {{{fail} "native-immutable-owner-write-{name} address=$::wp_last_address value=$::wp_last_value"}}' for name,r in l['objects'].items())
            takeover=f'''
{installs}
 set primary [debug read ioports 168]
 set ram [expr {{($primary>>6)&3}}]
 set final [expr {{($primary&0xC3)|($ram<<2)|($ram<<4)}}]
 if {{[debug read memory {s['t_slot_expanded']}]}} {{
  set secondary [debug read memory {s['t_slot_secondary']}]
  set sub [expr {{($secondary>>6)&3}}]
  set secondary [expr {{($secondary&0xC3)|($sub<<2)|($sub<<4)}}]
  debug write memory 65535 $secondary
  debug write memory {s['t_slot_secondary']} $secondary
 }}
 debug write ioports 168 $final
 debug write memory {s['t_slot_primary']} $final
 set ::native_flat_ready 1
 set f [open {{{out/'native-takeover.txt'}}} w];puts $f "actual all-RAM linked source, legacy cold init";close $f
'''
            if cartridge:
                if mode=='matrix':
                    needle=f"set boot [debug set_bp {s['paced_frame_start']} "
                    if text.count(needle)!=1:raise ValueError('unique controlled matrix boot entry required')
                    # First real prepare creates exactly one generation, as
                    # expected by the historical independent boot-history audit.
                    text=text.replace(needle+'{} ',f"set boot [debug set_bp {s['t_main.frame']} {{[debug read memory {s['t_commits']}]!=0}} ")
                    # Real source IRQ advances during the first preparation.
                    # Its history belongs to the coherent F000 picture, not
                    # to the newer canonical C000 state at prepare completion.
                    old_boot=f'puts -nonewline $bootfile "[debug read_block memory 0xC000 128]'
                    if text.count(old_boot)!=1:raise ValueError('unique coherent matrix boot-state capture required')
                    text=text.replace(old_boot,f'puts -nonewline $bootfile "[debug read_block memory 0xF000 128]')
                    marker='    debug write_block memory 0xC760 '
                    if text.count(marker)!=1:raise ValueError('unique native matrix RPC setup required')
                    text=text.replace(marker,f"    reg IFF 0\n    debug write {{VDP regs}} 1 194\n    debug write memory {s['t_in_irq']} 1\n    set ::abi [debug read_block memory 0xC600 256]\n"+marker)
                    # Cold ownership was already installed by the ROM loader.
                    text=text.replace('    debug write_block memory 0xF080 [string repeat [binary format c 165] 0x280]\n','')
                    condition=f"debug set_bp {s['ac_names']} {{![debug read memory {s['t_in_irq']}]}}"
                    if text.count(condition)!=1:raise ValueError('unique matrix NAME-list observer required')
                    text=text.replace(condition,f"debug set_bp {s['ac_names']} {{![debug read memory {s['t_in_irq']}] || $::native_flat_ready}}")
                    old_rpc='205 '+str(s['wait_vblank']&255)+' '+str(s['wait_vblank']>>8)
                    if text.count(old_rpc)!=1:raise ValueError('unique obsolete matrix polling call required')
                    text=text.replace(old_rpc,'205 112 199')
                    text=text.replace(marker,'    debug write_block memory 0xC770 [binary format cu* {219 153 230 128 40 250 201}]\n'+marker)
                text+=f'''
set native_flat_ready 0
after time 8 {{if {{!$::native_flat_ready}} {{{fail} "native-loader-timeout PC=[reg PC] SP=[reg SP] A8=[debug read ioports 168]"}}}}
debug set_bp {cold_meta['native_symbols']['nc_entry']} {{!$::native_flat_ready}} {{
 if {{[debug read_block memory 0 62208] ne [binary format H* {image[:0xF300].hex()}]}} {{fail native-real-low-decompression}}
 if {{[debug read_block memory 62336 3188] ne [binary format H* {image[0xF380:0xFFF4].hex()}]}} {{fail native-real-high-decompression}}
 if {{[debug read_block VRAM 0 16384] ne [binary format H* {video.hex()}]}} {{fail native-real-VRAM-initialization}}
 set ::native_flat_ready 1
 set f [open {{{out/'native-takeover.txt'}}} w];puts $f "exact real Normal32K low/high/VRAM cold decompression";close $f
}}
'''
            elif cold:
                entry=int.from_bytes(rom[2:4],'little')
                text+=f'''
set native_flat_ready 0
debug set_bp {entry} {{!$::native_flat_ready}} {{debug break;after break {{
 reg IFF 0
 set primary [debug read ioports 168]
 set ram [expr {{($primary>>6)&3}}]
 set expanded [expr {{[debug read memory [expr {{0xFCC1+$ram}}]]&128}}]
 set secondary [expr {{255^[debug read memory 65535]}}]
 set sub [expr {{($secondary>>6)&3}}]
 set secondary [expr {{$sub*85}}]
 set primary [expr {{$ram*85}}]
 debug write_block {{Main RAM}} 0 [binary format H* {image.hex()}]
 debug write_block VRAM 0 [binary format H* {video.hex()}]
 if {{$expanded}} {{debug write memory 65535 $secondary}}
 debug write ioports 168 $primary
 debug write memory 0xF360 $primary
 debug write memory 0xF361 $secondary
 debug write memory 0xF362 [expr {{$expanded ? 1:0}}]
 set ::native_flat_ready 1
 set f [open {{{out/'native-takeover.txt'}}} w];puts $f "source-defined cold RAM/VRAM; no old game initializer executed";close $f
 reg PC {cold_meta['native_symbols']['nc_entry']}
 debug cont
}}}}
'''
            elif mode=='matrix':
                needle=f"set boot [debug set_bp {s['paced_frame_start']} "
                if text.count(needle)!=1:raise ValueError('unique controlled matrix boot entry required')
                text=text.replace(needle,f"set boot [debug set_bp {s['t_main.frame']} ")
                marker='    debug write_block memory 0xC760 '
                if text.count(marker)!=1:raise ValueError('unique matrix RPC setup required')
                text=text.replace(marker,"    reg IFF 0\n    debug write {VDP regs} 1 194\n"+takeover+f"\n debug write memory {s['t_in_irq']} 1\n set ::slot [debug read ioports 168]\n set ::abi [debug read_block memory 0xC600 256]\n"+marker)
                prefix_condition=f"debug set_bp {s['ac_names']} {{![debug read memory {s['t_in_irq']}]}}"
                if text.count(prefix_condition)!=1:raise ValueError('unique original terminal NAME-list observation required')
                text=text.replace(prefix_condition,f"debug set_bp {s['ac_names']} {{![debug read memory {s['t_in_irq']}] || $::native_flat_ready}}")
                old_rpc='205 '+str(s['wait_vblank']&255)+' '+str(s['wait_vblank']>>8)
                if text.count(old_rpc)!=1:raise ValueError('unique obsolete matrix polling call required')
                text=text.replace(old_rpc,'205 112 199')
                text=text.replace(marker,'    debug write_block memory 0xC770 [binary format cu* {219 153 230 128 40 250 201}]\n'+marker)

                text='set native_flat_ready 0\n'+text
            else:
                text+=f"\nset native_flat_ready 0\ndebug set_bp {s['t_main.frame']} {{!$::native_flat_ready}} {{\n"+takeover+'}\n'
            text+=f'''
{guards}
debug set_watchpoint write_mem 0x7000 {{$::native_flat_ready}} {{{fail} native-mapper-write}}
'''
            if profile:
                if mode=='matrix':raise ValueError('profile natural routes only')
                from native_runtime_profile import script
                text+=script(out,s,l)
            p.write_text(text)
            if cartridge:
                args=list(args);args[args.index('-cart')+1]=str(cartridge);args[args.index('-romtype')+1]='Normal'
        return old_run(args,*a,**kw)
    subprocess.run=run
    try:
        from native_host_oracles import original_namespaces
        with original_namespaces(m):result=compact_game_probe.check(base,out,mode)
    finally:
        subprocess.run=old_run;atlas.audit_row=old_owner
        ownership.decorate_owners,clock.decorate_owners,prepared.decorate_owners=old_decorators
    if not (out/'native-takeover.txt').exists() or not count['rows']:raise ValueError('all-RAM takeover/oracles unexercised')
    if cartridge and cartridge.read_bytes()!=native_cart_bytes:raise ValueError('executed native artifact changed during validation')
    if digest(Path(__file__).read_bytes())!=producer:raise ValueError('native qualification driver changed during validation')
    oracle=json.loads((out/'check.json').read_bytes())
    receipt=dict(complete=True,mode=mode,input_rom_sha256=m['rom']['sha256'],native_image_sha256=digest(image),audits=count,
                 all_RAM_execution=True,legacy_ROM_cold_init_required=not bool(cold),source_defined_cold_start=bool(cold),native_product_loader=bool(cartridge),
                 executed_ROM_sha256=digest(native_cart_bytes) if cartridge else m['rom']['sha256'],
                 host_oracle_ROM_sha256=m['rom']['sha256'],producer_sha256=producer,
                 oracle_receipt_sha256=digest((out/'check.json').read_bytes()),
                 metrics={n:oracle[n] for n in ('source_checkpoints','active_pictures_per_second','mean_prepare_elapsed_cycles','max_prepare_elapsed_cycles','source_cpu_all_ram_equal','coherent_picture_pixels_equal','physical_owners_equal','late_vblanks','canonical_source_writes') if n in oracle},
                 scope='Source/pixel/physical/IRQ original route oracle plus immutable linked objects; not standalone format acceptance.')
    (out/'native-takeover.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','linked','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    p.add_argument('--cold',type=Path);p.add_argument('--cartridge',type=Path)
    p.add_argument('--profile',action='store_true')
    a=p.parse_args();check(a.base,a.linked,a.out,a.mode,a.cold,a.cartridge,a.profile)
