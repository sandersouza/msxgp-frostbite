"""Replace expanded owner NAME rows with small palettes and a RAM copier."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_grid_palette_probe import assets
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_footer_vram') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound VRAM footer stage required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-grid-palette-native-01';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=1280 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('all1280 prepared rows required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('palette copier source changed')
    data,_,_=assets(ROOT/'outputs/presentation/credit-reference-at/build-final');s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1300:])
        return (out/(name+'.bin')).read_bytes()
    code=assemble('gp-code',' ORG $1C00\ncg_directory EQU $1000\ncg_rows EQU $1900\ncg_palettes EQU $1100\n INCLUDE "compact_grid_palette.asm"\n ASSERT $ <= $1D00\n')
    if len(code)!=182:raise ValueError('exact component-proven palette copier required')
    gate=[f' ORG ${s["i_shifts"]:04X}']
    for n in ('p_tl_delta_index','p_tl_root','PAGE','p_w_row','t_mapper','x_name_row','t_enabled'):gate.append(f'{n} EQU ${s[n]:04X}')
    gate+=[' PUSH DE',' LD A,(p_tl_delta_index)']+[' RLCA']*4
    gate+=[' LD B,A',' LD A,(p_tl_root)',' AND 15',' OR B',' LD ($C7F0),A',' LD A,(PAGE)',' ADD A,A',' ADD A,A',
           ' LD B,A',' LD A,(p_w_row)',' ADD A,B',' LD ($C7F1),A',' LD A,(t_enabled)',' OR A',' JR Z,gp_cold',
           ' CALL $1C00',' JR gp_ready','gp_cold:',' LD A,45',' CALL t_mapper',' LD A,($C7F0)',' LD L,A',' LD H,$BD',' LD A,(HL)',
           ' LD ($C7F0),A',' CALL $B800','gp_ready:',' POP DE',' LD HL,$C480',' JP x_name_row',' ASSERT $ <= $7C51']
    gate=assemble('gp-gate','\n'.join(gate)+'\n')
    loader=[' ORG $BF00',' LD HL,$1100',' LD DE,$1101',' LD BC,$15FF',' LD (HL),$A5',' LDIR',
            ' LD HL,$BD00',' LD DE,$1000',' LD BC,160',' LDIR',' LD HL,$BA00',' LD DE,$1900',' LD BC,704',' LDIR',
            ' LD HL,$1900',' LD BC,704','gp_normalize:',' LD A,(HL)',' CP $FF',' JR NZ,gp_next',' LD (HL),8','gp_next:',
            ' INC HL',' DEC BC',' LD A,B',' OR C',' JR NZ,gp_normalize',
            ' LD HL,$BE40',' LD DE,$1100',' LD B,8','gp_palette:',' PUSH BC',' LD BC,9',' LDIR',' POP BC',' INC D',' LD E,0',' DJNZ gp_palette',
            ' LD HL,$B930',' LD DE,$1C00',f' LD BC,{len(code)}',' LDIR',' RET',' ASSERT $ <= $C000']
    loader=assemble('gp-loader','\n'.join(loader)+'\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    for address,blob in ((0xB930,code),(0xBE40,data['palettes'])):
        at=45*16384+address-0x8000
        if parent[at:at+len(blob)]!=bytes([255])*len(blob):raise ValueError('unused cold grid storage required')
        patch(at,blob,'startup image of normalized RAM copier/owner palettes')
    if parent[45*16384+0x3D00:45*16384+0x3DA0]!=data['directory']:raise ValueError('complete original phase-directory IDs required')
    if parent[45*16384+0x3A00:45*16384+0x3A00+704].replace(b'\xff',b'\x08')!=data['rows']:raise ValueError('complete original normalized rows required')
    patch(45*16384+0x3F00,loader,'new compact lower-RAM preload; poison all retired expansion bytes')
    patch(s['i_shifts']-0x4000,gate,'same prepared floe caller; cold ROM path and direct white atlas remain intact')
    initializers=[]
    for name,address,blob in (('directory',0x1000,data['directory']),('rows',0x1900,data['rows']),('code',0x1C00,code)):
        filename='gp-'+name+'.bin';(out/filename).write_bytes(blob);initializers.append(dict(file=filename,ram_address=address,size=len(blob),sha256=digest(blob)))
    for owner in range(8):
        blob=data['palettes'][owner*9:owner*9+9];filename=f'gp-palette-{owner}.bin';(out/filename).write_bytes(blob)
        initializers.append(dict(file=filename,ram_address=0x1100+owner*256,size=9,sha256=digest(blob)))
    occupied=set()
    for row in initializers:occupied.update(range(row['ram_address'],row['ram_address']+row['size']))
    ranges=[];start=None
    for address in range(0x1100,0x2701):
        free=address<0x2700 and address not in occupied
        if free and start is None:start=address
        elif not free and start is not None:ranges.append(dict(address=start,size=address-start));start=None
    if sum(r['size'] for r in ranges)!=4674:raise ValueError('exact recovered expanded-row capacity required')
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    for n in ('scripts/build_compact_grid_palette.py','scripts/compact_grid_palette_probe.py','src/compact_grid_palette.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_grid_palette']=dict(parent_rom_sha256=digest(parent),patches=patches,initializers=initializers,reclaimed_ranges=ranges,
        old_expanded_bytes=5632,normalized_rows_bytes=704,palette_bytes=72,copier_bytes=len(code),reclaimed_bytes=sum(r['size'] for r in ranges),
        cold_constructor_retained=True,white_atlas_unchanged=True,phase_owner_cases=1280,mapperless=False,human_test_candidate=False)
    m['compact_grid_experiment']['representation_replaced_by']='compact_grid_palette: exact936-byte data/182-byte code allocation; old expanded fields are ancestry only'
    filename='frostbite-compact-grid-palette-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();m.update(source_commit=commit,source_dirty=True,version='compact-grid-palette-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Normalized owner-paletted NAME rows reclaim lower RAM; exact preload/new guards and whole-frame qualification required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),copier_bytes=len(code),reclaimed_lower_RAM_bytes=m['compact_grid_palette']['reclaimed_bytes'],gate_bytes=len(gate),loader_bytes=len(loader)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
