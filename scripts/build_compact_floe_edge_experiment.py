"""Integrate the qualified interior floe kernel; retain literal boundary fallback."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_shore_common') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('bound startup-grid integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('source changed')
    source=ROOT/'outputs/compact/issue44-edge-native-full-01'
    proof=json.loads((source/'component-result.json').read_bytes())
    if not proof['complete_native_horizontal_domain'] or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('qualified edge data required')
    assets={n:(source/(n+'.bin')).read_bytes() for n in ('edge_reverse','edge_windows','edge_bits','edge_low_masks','edge_control_clocks','edge_motion_clocks')}
    if any(digest(b)!=proof['files'][n+'.bin'] for n,b in assets.items()):raise ValueError('edge assets changed')
    s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for n,b in assets.items():(out/('cf-'+n+'.bin')).write_bytes(b)
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',
            f'--raw={out/(name+".bin")}',f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes()
    asm=[' ORG $B800',' DEFINE CE_INPUT_ORIGIN $3300',' DEFINE CE_SCRATCH_ORIGIN $0FC0',
         ' DEFINE CE_OUTPUT_ORIGIN $2940',' DEFINE CE_ROW_INPUT_ORIGIN $2970',
         ' DEFINE CE_CONTACT_INPUT_ORIGIN $2990',' DEFINE CE_CONTACT_SCRATCH_ORIGIN $2994',
         ' DEFINE CE_CLIP_QUERY_Y','ce_glyphs EQU $0100','ce_bases EQU $0F00',
         'ce_edge_reverse EQU $BD00','ce_edge_windows EQU $BE00','ce_edge_bits EQU $BF40',
         'ce_edge_low_masks EQU $BF60','ce_edge_control_clocks EQU $BF80','ce_edge_motion_clocks EQU $BF94',
         'cf_contact EQU $3000','cf_control EQU $3300','cf_y EQU $3301','cf_dx EQU $3302','cf_pose EQU $3303',
         ' INCLUDE "compact_floe_edge.asm"',' INCLUDE "compact_floe_edge_row.asm"',
         ' INCLUDE "compact_floe_edge_contact.asm"',' ASSERT $ <= $BC00',' DS $BC00-$,$FF',
         ' INCLUDE "compact_floe_edge_query.asm"',' ASSERT $ <= $BD00']
    for n,a in (('edge_reverse',0xBD00),('edge_windows',0xBE00),('edge_bits',0xBF40),('edge_low_masks',0xBF60),('edge_control_clocks',0xBF80),('edge_motion_clocks',0xBF94)):
        asm += [f' DS ${a:04X}-$,$FF',f' INCBIN "{out/("cf-"+n+".bin")}"']
    asm += [' ASSERT $ <= $C000',' DS $C000-$,$FF'];code=assemble('ce-bank','\n'.join(asm)+'\n')
    asm=[' ORG $3100','cf_contact EQU $3000']
    for i,n in enumerate(('cf_control','cf_y','cf_dx','cf_pose','cf_shift','cf_reflection','cf_absolute_x')):asm.append(f'{n} EQU ${0x3300+i:04X}')
    for n in ('t_enabled','floe_control_index','core_fault','floe_acquire','floe_bit_masks','floe_viewmask','floe_viewbyte','t_mapper'):asm.append(f'{n} EQU ${s[n]:04X}')
    asm += [' INCLUDE "compact_floe_complete.asm"',' ASSERT $ <= $3300',' DS $3300-$,0']
    gate=assemble('ce-acquire','\n'.join(asm)+'\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        target[at:at+len(b)]=b
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason))
    patch(49*16384+0x3800,code,'edge query module in retired NAME storage')
    patch(46*16384+0x3900,gate,'complete native floe acquisition after bootstrap')
    for n in ('scripts/build_compact_floe_edge_experiment.py','src/compact_floe_edge.asm','src/compact_floe_edge_row.asm','src/compact_floe_edge_contact.asm','src/compact_floe_complete.asm','src/compact_floe_edge_query.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    for row in m['contact14']['arena']:
        if row['bank'] in (46,49):row['packed_sha256']=digest(target[row['bank']*16384:(row['bank']+1)*16384])
    m['compact_floe_complete']=dict(parent_rom_sha256=digest(parent),patches=patches,
        immutable_ram=[[0x3100,0x3300]],scratch_ram=[[0x3300,0x3307],[0x0FC0,0x0FE0],[0x2940,0x2996]],
        eligibility='all source floe X after RAM takeover; cold startup alone retains table fallback',
        original_tables_retained=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-floe-complete-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-floe-complete-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Unqualified integration experiment.')
    m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),patches=len(patches),human_test_candidate=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
