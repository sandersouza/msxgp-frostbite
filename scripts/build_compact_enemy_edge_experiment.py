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
    if not m.get('compact_floe_complete') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('bound startup-grid integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('source changed')
    source=ROOT/'outputs/compact/issue44-hazard-program-native-full-02'
    proof=json.loads((source/'component-result.json').read_bytes())
    if not proof['complete'] or not proof['complete_native_domain'] or proof['original_sha256']!=m['profile']['source_sha256']:raise ValueError('qualified ordinary program required')
    for n,addr in (('enemy',0x2700),('shapes',0x2900)):
        data=(source/(n+'.bin')).read_bytes()
        if digest(data)!=proof['files'][n+'.bin']:raise ValueError('program assets changed')
        lower=parent[48*16384+0x3800+addr-0x2700:48*16384+0x3800+addr-0x2700+len(data)]
        if lower!=data:raise ValueError('shared ordinary assets differ')
    assets={}
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
    asm=[' ORG $B800',' DEFINE CX_INPUT_ORIGIN $3300',' DEFINE CX_OUTPUT_ORIGIN $2980',
         ' DEFINE HP_INPUT_ORIGIN $3300',' DEFINE HP_OUTPUT_ORIGIN $2940',' DEFINE HP_SCRATCH_ORIGIN $0FC0',
         ' DEFINE HP_QUERY_TAG $2990',' DEFINE CE_ROW_INPUT_ORIGIN $2970',
         ' DEFINE MP_INPUT_ORIGIN $2990',' DEFINE MP_SCRATCH_ORIGIN $2997',
         'ce_glyphs EQU $0100','ce_bases EQU $0F00','hp_enemy EQU $2700','hp_shapes EQU $2900','hp_samples EQU $BD00',
         ' INCLUDE "compact_hazard_context.asm"',' INCLUDE "compact_hazard_program.asm"',
         ' INCLUDE "compact_floe_edge_row.asm"',' INCLUDE "compact_mask_program.asm"',
         ' ASSERT $ <= $BC00',' DS $BC00-$,$FF']
    for n in ('hazard_y','hazard_shape_index','core_fault'):asm.append(f'{n} EQU ${s[n]:04X}')
    asm += [' INCLUDE "compact_enemy_edge_query.asm"',' ASSERT $ <= $BD00',' DS $BD00-$,$FF',
            ' DB 128,64,32,16,8,4,2,1',' DS $C000-$,$FF']
    code=assemble('he-bank','\n'.join(asm)+'\n')
    asm=[f' ORG ${s["i_shift4"]:04X}',f't_mapper EQU ${s["t_mapper"]:04X}',f't_enabled EQU ${s["t_enabled"]:04X}',
         f'hazard_lookup EQU ${s["hazard_lookup"]:04X}',
         ' PUSH AF',' LD A,(t_enabled)',' OR A',' JR Z,cold',' POP AF',' LD A,50',' CALL t_mapper',' JP $BC00',
         'cold:',' POP AF',' JP hazard_lookup',f' ASSERT $ <= ${s["i_shift5"]:04X}']
    gate=assemble('he-gate','\n'.join(asm)+'\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        target[at:at+len(b)]=b
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason))
    control=ROOT/'outputs/presentation/credit-reference-at/build-final'
    cm=json.loads((control/'build.json').read_bytes());cr=(control/cm['rom']['filename']).read_bytes()
    at=s['i_shift4']-0x4000
    if parent[at:at+len(gate)]!=cr[at:at+len(gate)]:raise ValueError('retired shift gate already occupied')
    patch(at,gate,'resident exceptional enemy gate')
    patch(50*16384+0x3800,code,'native exceptional enemy program/query')
    start=s['hazard_row_active']-0x4000;end=s['hazard_copy_distance']-0x4000
    needle=bytes((0xCD,s['hazard_lookup']&255,s['hazard_lookup']>>8))
    positions=[i for i in range(start,end-2) if parent[i:i+3]==needle]
    if len(positions)!=2:raise ValueError('two literal exceptional ordinary calls required')
    entry=s['i_shift4']
    for at in positions:patch(at,bytes((0xCD,entry&255,entry>>8)),'native ordinary exceptional query; cold fallback retained')
    for n in ('scripts/build_compact_enemy_edge_experiment.py','src/compact_hazard_context.asm','src/compact_hazard_program.asm','src/compact_floe_edge_row.asm','src/compact_mask_program.asm','src/compact_enemy_edge_query.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    for row in m['contact14']['arena']:
        if row['bank'] in (50,):row['packed_sha256']=digest(target[row['bank']*16384:(row['bank']+1)*16384])
    m['compact_enemy_complete']=dict(parent_rom_sha256=digest(parent),patches=patches,
        immutable_ram=[],scratch_ram=[[0x3300,0x3307],[0x0FC0,0x0FE0],[0x2940,0x2999]],
        eligibility='all ordinary exceptional-X calls after takeover; original common and cold paths retained',
        original_tables_retained=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-enemy-complete-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-enemy-complete-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Unqualified integration experiment.')
    m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),patches=len(patches),human_test_candidate=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
