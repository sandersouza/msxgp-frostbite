"""Original ordered PSG intervals after the actual native32K cartridge loader.

Controlled source CPU/RAM/audio-latch injection is explicit. No captured target
state builds a product, and this test establishes neither listening nor cadence.
"""
import argparse
import json
from pathlib import Path
import subprocess
import presentation_audio_check as audio
from build_native_flat_image import digest
from render_build import symbols


def check(base,delivery,out,negative=False):
    base,delivery,out=base.resolve(),delivery.resolve(),out.resolve()
    if out.exists():raise ValueError('fresh audio qualification output required')
    producer=digest(Path(__file__).read_bytes())
    m=json.loads((base/'build.json').read_bytes());d=json.loads((delivery/'native-delivery-build.json').read_bytes())
    cold=json.loads((delivery/'cold/cold-image.json').read_bytes())
    linked=json.loads((delivery/'linked/native-link.json').read_bytes())
    ram=(delivery/'cold/cold-ram.bin').read_bytes();video=(delivery/'cold/cold-vram.bin').read_bytes()
    cartridge=delivery/'cartridge/FROSTBIT.ROM';rom=cartridge.read_bytes()
    if digest(rom)!=d['files']['cartridge/FROSTBIT.ROM']['sha256'] or len(rom)!=32768:
        raise ValueError('bound complete native32K cartridge required')
    if digest(ram)!=cold['ram_sha256'] or digest(video)!=cold['vram_sha256'] or linked['image_sha256']!=cold['parent_native_image_sha256']:
        raise ValueError('bound native source-defined cold initializer required')
    s=symbols(base/'presentation.sym');original_run=subprocess.run
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p=Path(args[args.index('-script')+1]);text=p.read_text()
            needle=f"set boot [debug set_bp {s['native_reset_done']} "
            if text.count(needle)!=1:raise ValueError('unique original audio boot checkpoint required')
            text=text.replace(needle,f"set boot [debug set_bp {cold['native_symbols']['nc_source_ready']} ")
            # The old unused heap now contains linked code/immutable objects.
            # Preserve its exact boot state rather than poisoning a live game.
            needle='    debug write_block memory 0xE800 [string repeat [binary format c 165] 0xB40]'
            if text.count(needle)!=1:raise ValueError('unique obsolete audio heap poison required')
            text=text.replace(needle,'    set ::native_audio_guard [debug read_block memory 0xE800 0xB40]')
            needle='[debug read_block memory 0xE800 0xB40] ne [string repeat [binary format c 165] 0xB40]'
            if text.count(needle)!=1:raise ValueError('unique historical audio heap guard required')
            text=text.replace(needle,'[debug read_block memory 0xE800 0xB40] ne $::native_audio_guard')
            # C6D0 is no longer spare RAM. Use the same private RPC area as the
            # native controlled graphics matrix; keep the source ABI output.
            text=text.replace('0xC6D0','0xC760').replace('0xC6D3','0xC763').replace('0xC6D9','0xC769')
            needle='195 217 198 24 254'
            if text.count(needle)!=1:raise ValueError('unique original audio RPC return required')
            text=text.replace(needle,'195 105 199 24 254')
            # Keep all original source, ordered events/writes, PSG GPIO and
            # unowned-register, stack/slot and complete-VRAM comparisons.
            text+=f'''
set native_audio_loader 0
after time 8 {{if {{!$::native_audio_loader}} {{fail_game_audio native-loader-timeout}}}}
debug set_bp {cold['native_symbols']['nc_entry']} {{!$::native_audio_loader}} {{
 if {{[debug read_block memory 0 62208] ne [binary format H* {ram[:0xF300].hex()}]}} {{fail_game_audio native-low-RAM}}
 if {{[debug read_block memory 62336 3188] ne [binary format H* {ram[0xF380:0xFFF4].hex()}]}} {{fail_game_audio native-high-RAM}}
 if {{[debug read_block VRAM 0 16384] ne [binary format H* {video.hex()}]}} {{fail_game_audio native-VRAM}}
 set ::native_audio_loader 1
 set f [open {{{out/'native-loader.txt'}}} w];puts $f "exact real Normal32K decompression before source/audio initialization";close $f
}}
debug set_watchpoint write_mem 0x7000 {{$::native_audio_loader}} {{fail_game_audio mapper-write}}
'''
            for name,row in linked['objects'].items():
                first,last=row['address'],row['address']+row['size']-1
                text+=f'debug set_watchpoint write_mem {{{first} {last}}} {{$::native_audio_loader}} {{fail_game_audio native-immutable-{name}}}\n'
            p.write_text(text);args=list(args);args[args.index('-cart')+1]=str(cartridge);args[args.index('-romtype')+1]='Normal'
        return original_run(args,*a,**kw)
    subprocess.run=run;expected_failure=None
    try:
        try:result=audio.check(base,out,inject=negative)
        except ValueError as error:
            if not negative or str(error)!='native ordered source audio events differ or truncate':raise
            if (out/'check.json').exists():raise ValueError('negative audio control created positive evidence')
            expected_failure=str(error);result=None
    finally:subprocess.run=original_run
    if negative and not expected_failure:raise ValueError('negative ordered-audio control was accepted')
    if not (out/'native-loader.txt').exists() or cartridge.read_bytes()!=rom or digest(Path(__file__).read_bytes())!=producer:
        raise ValueError('actual native loader/producers/artifact must remain bound')
    if result and (result['cases']!=2115 or not result['complete']):raise ValueError('all original ordered intervals required')
    receipt=dict(complete=True,negative_control=negative,expected_failure=expected_failure,
        executed_ROM_sha256=digest(rom),host_oracle_ROM_sha256=m['rom']['sha256'],actual_native_loader=True,
        controlled_source_phase_injection=True,target_state_used_as_build_input=False,
        source_CPU_all_RAM_equal=bool(result),ordered_source_and_physical_PSG_equal=bool(result),
        cases=result['cases'] if result else 2115,ordered_source_writes=result['ordered_source_writes'] if result else None,
        physical_PSG_writes=result['physical_psg_writes'] if result else None,immutable_native_objects_guarded=len(linked['objects']),
        producer_sha256=producer,original_receipt_sha256=digest((out/'check.json').read_bytes()) if result else None,
        manual_listening=False,physical_hardware=False,cadence_accepted=False)
    (out/'native-audio-check.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','delivery','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--negative',action='store_true');a=p.parse_args()
    check(a.base,a.delivery,a.out,a.negative)
