"""Exact P0 rectangle packing and three-sprite fullbear from sealed v25."""
import argparse,json,hashlib,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from build_player_bands import build as player_build
from presentation_bear_three import full_assets
from render_build import symbols
sha=lambda b:hashlib.sha256(b).hexdigest()

def build(base,out,mode='full'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if mode not in('full','original'):raise ValueError('declared full/original mode required')
    m=player_build(base,out,'original'if mode=='original'else'packed')
    if mode=='original':return m
    phase1=(out/m['rom']['filename']).read_bytes();s=symbols(out/'presentation.sym');a=full_assets(base)
    (out/'bear-three-pool.bin').write_bytes(a['pool']);(out/'bear-three-info.bin').write_bytes(a['info'])
    defs={n:v for n,v in s.items()if not n.startswith('an_')and n not in('AN_RECORD','AN_TILE','AN_KEYS','AO_INFO','AO_PACKET')};defs['AN_HUD_CONT']=s['presentation_hud_prepare']+3
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in defs.items()if'.'not in n)+'\n');source=ROOT/'src/presentation_bear_three.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"bear-three.bin"}',f'--sym={out/"bear-three.sym"}',f'--lst={out/"bear-three.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True);(out/'bear-three-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'bear-three.sym');code=(out/'bear-three.bin').read_bytes();slot=s['w_selected']-s['w_header'];ram=115*16384+0x3800+s['w_header']-0xe900
    if slot!=110 or len(code)!=slot+2048 or code[:slot]!=phase1[ram:ram+slot]or q['an_body']!=0xb800:raise ValueError('original110B RAM wrapper must remain byte-identical')
    rom=bytearray(phase1);patches=[]
    for bank,data in((114,code[slot:]),(132,a['payload']+bytes([255])*(2048-len(a['payload'])))):
        at=bank*16384+0x3800;old=bytes(rom[at:at+2048]);rom[at:at+2048]=data;patches.append(dict(offset=at,size=2048,before_sha256=sha(old),after_sha256=sha(data)));assert rom[bank*16384:at]==phase1[bank*16384:at]
        name=f'assets-{bank:03d}.bin';blob=bytes(rom[bank*16384:(bank+1)*16384])
        for section in('template_assets','static_presentation'):
            if name in m[section]['files']:m[section]['files'][name]=sha(blob);(out/'template-assets'/name).write_bytes(blob)
    assert rom[115*16384:116*16384]==phase1[115*16384:116*16384]
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    files=dict(m['source_files'])
    for p in(Path(__file__),source,ROOT/'scripts/presentation_bear_three.py',ROOT/'scripts/presentation_bear_three_check.py',ROOT/'tests/test_presentation_bear_three.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip());m.update(version='bear-three-ao-internal',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Exact packed-color P0 and weighted-admission three-sprite fullbear; original mechanics/clock/palette/input/PSG unchanged.'))
    m['player_bands'].update(mode='packed-player-and-three-sprite-bear',full_bear=True)
    m['bear_hybrid']['registry_address']=q['an_registry']
    m['bear_three']=dict(parent_rom_sha256=m['player_bands']['parent_rom_sha256'],phase1_rom_sha256=sha(phase1),patches=patches,body_bank=114,body_bytes=q['an_body_end']-q['an_body'],data_bank=132,data_bytes=len(a['payload']),group_info_address=0xbc00,triple_pool_address=0xbc20,triple_bytes=96,triple_count=a['packet_count'],groups=a['groups'],prefixes_byte_identical=True,prefix_pattern_slots=[[22,23],[46,47]],extra_pattern_slots=[58,59],occupied_reserved_sgt_bytes_added=64,sgt_reserved_bytes=2048,cache_key_addresses=[0xe8b9,0xe8ba],cache_protocol='low7 group+1, highbit thirdvalid; publish after all SGT writes',scratch_info=[0xc496,0xc49a],original_ram_wrapper_bytes_unchanged=110,tile_packet_only_on_hybrid=True,full_fast_bound='M3relative start span>=16',new_ram_allocation_bytes=0,new_vram_bytes=0,scope='Original AN common guards/NAME history retained; fullN<=28 and exact weightedS4, then originalhybrid/nativefallback. Active extraPAGE SGT stays immutable even if unreferenced.')
    s.update({n:v for n,v in q.items()if n.startswith(('an_','ao_'))});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n');name='frostbite-bear-three-ao.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),body_bytes=m['bear_three']['body_bytes'],data_bytes=len(a['payload']),new_allocation=0));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('full','original'),default='full');a=p.parse_args();build(a.base,a.out,a.mode)
