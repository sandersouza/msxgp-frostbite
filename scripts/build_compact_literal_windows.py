"""Share immutable bear/P0 byte windows and retire obsolete source copies."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_byte_windows import bear_lookup,strip_lookup
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_enemy_occupancy') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound exact occupancy stage required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofs={}
    for name,cases in (('bear-window-native-01',4230),('bear-window-strip-native-01',210),('shore-window-native-01',239)):
        root=ROOT/'outputs/compact'/('issue44-'+name);q=json.loads((root/'component-result.json').read_bytes())
        if not q['complete'] or q['cases']!=cases or q['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('complete literal window proof required')
        for n,h in q['sources'].items():
            if digest((ROOT/n).read_bytes())!=h:raise ValueError('literal window producer changed')
        for n in ('directory.bin','pool.bin') if name.startswith('bear') else ('directory.bin','halves.bin'):
            if digest((root/n).read_bytes())!=q['files'][n]:raise ValueError('window component data changed')
        proofs[name]=(root,q)
    bear=proofs['bear-window-native-01'][0];shore=proofs['shore-window-native-01'][0]
    directory=(bear/'directory.bin').read_bytes();pool=(bear/'pool.bin').read_bytes();sp_directory=(shore/'directory.bin').read_bytes();sp_pool=(shore/'halves.bin').read_bytes()
    if (len(directory),len(pool),len(sp_directory),len(sp_pool))!=(940,1415,956,2342):raise ValueError('finite literal window bounds changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--raw={out/(name+".bin")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes()
    pool_at=0xA900+len(directory)
    defs=f'cw_directory EQU $A900\ncw_pool EQU ${pool_at:04X}\n'
    tile=assemble('lw-tile',' ORG $A800\ncb_bases EQU $B7B0\n'+defs+bear_lookup((ROOT/'src/compact_bear_tile_fast.asm').read_text())+'\n ASSERT $ <= $A900\n')
    strip=assemble('lw-strip',' ORG $6A50\n'+defs+strip_lookup((ROOT/'src/compact_bear_strip_fast.asm').read_text())+'\n ASSERT $ <= $6B54\n')
    target=bytearray(parent);patches=[];graphics=m['compact_retired_graphics']
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    def retire(bank,address,size,reason):
        patch(bank*16384+address-0x8000,bytes([255])*size,reason)
        graphics['ranges'].append(dict(bank=bank,address=address,size=size,kind=reason));graphics['retired_physical_bytes']+=size
    old_masks=(bear/'patterns.bin').read_bytes()
    if parent[56*16384+0x2900:56*16384+0x2900+3760]!=old_masks:raise ValueError('old complete mask pool changed')
    patch(56*16384+0x2800,tile,'same native tile entry with literal-window pointer lookup')
    patch(0x6A50-0x4000,strip,'same native bulk entry with shared literal-window lookup')
    patch(56*16384+0x2900,directory+pool,'470 mask pointers share exact1415-byte literal superstring')
    retire(56,pool_at+len(pool),3760-len(directory)-len(pool),'retired fixed-stride native bear mask suffix')
    patch(58*16384+0x2900,sp_directory,'existing P0 offsets now reference overlapping16-byte windows')
    patch(58*16384+0x2D00,sp_pool,'unchanged P0 reader uses2342-byte overlapping half pool')
    retire(58,0xAD00+len(sp_pool),3712-len(sp_pool),'retired fixed-stride P0 shore half suffix')
    # Native queries bypass root/base shadow acquisition. The four live source
    # entry gates already have independent all-state query proofs; keep cold
    # read guards here, and do not infer deletion merely from absence in traces.
    shadow=m['contact_shadow']
    if shadow['bank']!=255 or shadow['root_address']!=0xA700 or shadow['root_bytes']+shadow['base_bytes']!=6400:raise ValueError('exact obsolete contact shadow required')
    retire(255,0xA700,6400,'retired contact root/base shadow after complete native acquisition')
    header=m['template_assets']['sections']['header'];banks=m['template_assets']['physical_banks'];bank=banks[header['offset']//16384];address=0x8000+header['offset']%16384
    if (bank,address,header['size'])!=(12,0xB880,1360):raise ValueError('exact old generic header fragments required')
    retire(bank,address,1360,'retired generic header copy; compact native font remains immutable')
    for key in ('template_assets','static_presentation'):
        for bank in (12,255):
            filename=f'assets-{bank:03d}.bin'
            if filename in m[key]['files']:m[key]['files'][filename]=digest(target[bank*16384:(bank+1)*16384])
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    names=('scripts/build_compact_literal_windows.py','scripts/compact_byte_windows.py','scripts/compact_bear_windows_probe.py','scripts/compact_shore_windows_probe.py','tests/test_compact_byte_windows.py')
    for n in names:m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_literal_windows']=dict(parent_rom_sha256=digest(parent),patches=patches,bear_old_mask_bytes=3760,bear_new_mask_bytes=2355,
        shore_old_half_bytes=3712,shore_new_half_bytes=2342,P0_runtime_code_unchanged=True,bear_tile_cases=4230,bear_strip_cases=210,shore_pattern_cases=239,
        retired_contact_shadow_bytes=6400,retired_generic_header_bytes=1360,requires_cold_read_and_pixel_proof=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-literal-windows-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();m.update(source_commit=commit,source_dirty=True,version='compact-literal-windows-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Literal windows and obsolete copies removed; full retirement/source/picture gates required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),shared_window_savings=2775,retired_obsolete_copies=7760,tile_code_bytes=len(tile),strip_code_bytes=len(strip)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
