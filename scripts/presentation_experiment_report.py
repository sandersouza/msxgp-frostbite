"""Matched whole-frame report for private renderer implementations, against M-C."""
import argparse
import importlib.util
import json
from pathlib import Path
import statistics
import collections
import types

from environment import ROOT
from presentation_band_report import validate_sequence
from presentation_band_spike import sha,verified_bytes
from presentation_experiment_evidence import validate_probe,validate_owner_receipt,validate_scene_receipt


def measured_io_cost(byte_count,calls,fill_calls,fill_bytes=None):
    if fill_bytes is None:fill_bytes=128*fill_calls
    if (any(type(v)is not int or v<0 for v in (byte_count,calls,fill_calls,fill_bytes))
            or not 0<=fill_calls<=calls or not fill_calls<=fill_bytes<=256*fill_calls
            or byte_count<fill_bytes):
        raise ValueError('invalid direct-fill event count/bytes')
    return 29*(byte_count-fill_bytes)+53*(calls-fill_calls)+33*fill_bytes+55*fill_calls


def report(root,build,suffix,kind,scene_suffix=None,output_suffix=None):
    output_suffix=output_suffix or suffix
    base=ROOT/'outputs/presentation/playfield-m-c'
    old=json.loads(verified_bytes(base/'analysis.json','2679aa50049a9995e9329c61a225c94ba6bd55ccabb6dd31c3a4e648c7b0f485'))
    analyzer=base/'analyze.py'
    verified_bytes(analyzer,'df20d1f9a6ced3574bbca3a8da12e930f73d5500da08cc91c798b84bb24b67dd')
    module=types.ModuleType('sealed_mc_analysis');module.__file__=str(analyzer)
    source=analyzer.read_text()
    old_assert='assert vdp_cycles == 29*traffic[index][1]+53*calls'
    if source.count(old_assert)!=1:raise ValueError('known analyzer IO check changed')
    source=source.replace(old_assert,'assert vdp_cycles == io_cost(family,index,traffic[index][1],calls)')
    def io_cost(family,index,byte_count,calls):
        fills=collections.Counter()
        filled=collections.Counter()
        if kind=='prepared':
            path=root/(family+'-'+suffix)/'fill-events.tsv'
            for line in path.read_text().splitlines():
                frame,count,address=map(int,line.split())
                if frame<0 or frame>=(2253 if family=='ntsc' else 1886) or count not in (24,128) or not 0x6000<=address<address+count<=0x7800:
                    raise ValueError('invalid direct-CGT transfer event')
                fills[frame]+=1
                filled[frame]+=count
        return measured_io_cost(byte_count,calls,fills[index],filled[index])
    module.io_cost=io_cost
    exec(compile(source,str(analyzer),'exec'),module.__dict__)
    inputs=root/('report-inputs-v2-'+suffix);inputs.mkdir(exist_ok=True)
    for family in ('ntsc','pal'):
        link=inputs/(family+'-a');target=(root/(family+'-'+suffix)).resolve()
        if link.is_symlink():
            if link.resolve()!=target:raise ValueError('report input alias changed')
        else:link.symlink_to(target,target_is_directory=True)
    if any((root/(name+'-'+output_suffix+'.json')).exists() for name in ('analysis','comparison')):
        raise ValueError('immutable report already exists')
    module.ROOT=inputs
    meta=json.loads((build/'build.json').read_text())
    candidate_sha=sha((build/meta['rom']['filename']).read_bytes())
    if candidate_sha!=meta['rom']['sha256']:raise ValueError('actual candidate ROM differs')
    results=[module.analyze(f) for f in ('ntsc','pal')]
    rows,checks=[],[]
    for before,after in zip(old['results'],results,strict=True):
        family=after['family'];directory=root/(family+'-'+suffix)
        validate_sequence(after,family,candidate_sha,(directory/'captures.bin').stat().st_size)
        validate_sequence(before,family,old['candidate_rom_sha256'],(base/(family+'-a')/'captures.bin').stat().st_size)
        if len(before['records'])!=len(after['records']):raise ValueError('paired frame count differs')
        receipt=json.loads((directory/'route-research.json').read_text())
        probe=validate_probe(directory,candidate_sha,len(after['records']))
        extra=validate_owner_receipt(directory,candidate_sha,len(after['records']),kind)
        if not extra['complete'] or extra['frames']!=len(after['records']):raise ValueError('missing physical ownership checks')
        if receipt['expanded_private_profiler_sha256']!='6ef44410eb45ad5f5aba995dfda913f9336a6354245931b949ca9e83c732b5ed':raise ValueError('unrecognized pixel/timing oracle')
        if probe['frames']!=len(after['records']) or probe['rom_sha256']!=candidate_sha:raise ValueError('pixel/timing receipt count or ROM differs')
        if receipt['probe_receipt_sha256']!=sha((directory/'check.json').read_bytes()):raise ValueError('probe receipt changed')
        for name in ('captures.bin','cycles.tsv','phases.tsv','costs.tsv','traffic.tsv','route-cpu.bin'):
            if probe['artifacts'][name]!=sha((directory/name).read_bytes()):raise ValueError('route evidence changed: '+name)
        if (directory/'route-cpu.bin').read_bytes()!=(base/(family+'-a')/'route-cpu.bin').read_bytes():
            raise ValueError('complete original CPU/RAM route differs')
        for a,b in zip(before['records'],after['records'],strict=True):
            if [a[k] for k in ('frame','active','source_steps','source_x','source_y','c6','e7','f1')]!=[b[k] for k in ('frame','active','source_steps','source_x','source_y','c6','e7','f1')]:
                raise ValueError('paired source state selection differs')
        for population in ('active','all'):
            a,b=before['groups'][population],after['groups'][population]
            rows.append(dict(family=family,population=population,frames=b['frames'],
                baseline_rate=a['updates_per_second'],candidate_rate=b['updates_per_second'],
                rate_gain=b['updates_per_second']/a['updates_per_second']-1,
                baseline_busy=a['metrics']['busy']['mean'],candidate_busy=b['metrics']['busy']['mean'],
                candidate_p95=b['metrics']['busy']['p95'],candidate_max=b['metrics']['busy']['maximum'],
                baseline_stages={k:v['mean'] for k,v in a['stages'].items()},candidate_stages={k:v['mean'] for k,v in b['stages'].items()},
                baseline_bytes=a['metrics']['bytes']['mean'],candidate_bytes=b['metrics']['bytes']['mean']))
        checks.append(dict(family=family,frames=len(after['records']),native_points=receipt['native_checkpoints'],
            native_cpu_all_ram_identical=True,source_pixel_oracle_complete=True,physical_ownership_complete=extra['complete']))
    density=[]
    scene_suffix=scene_suffix or suffix
    for population,new,prior in [('all',root/('density-'+scene_suffix),base/'density-m')]:
        check=validate_scene_receipt(new,candidate_sha,1920,kind)
        if not check['complete'] or check['cases']!=1920:raise ValueError('incomplete dense scenes')
        a,b=[[int(l.split()[1]) for l in (p/'timing.tsv').read_text().splitlines()] for p in (prior,new)]
        if len(a)!=1920 or len(b)!=1920:raise ValueError('incomplete density timings')
        density.append(dict(population=population,frames=1920,baseline=statistics.mean(a),candidate=statistics.mean(b),reduction=1-statistics.mean(b)/statistics.mean(a)))
    matrix=validate_scene_receipt(root/('matrix-'+scene_suffix),candidate_sha,2115,kind)
    if not matrix['complete'] or matrix['cases']!=2115:raise ValueError('incomplete original scene matrix')
    summary=dict(baseline_rom_sha256=old['candidate_rom_sha256'],candidate_rom_sha256=candidate_sha,
        rows=rows,checks=checks,density=density,matrix_cases=2115,matrix_different_frames=matrix['different_frames'],
        source_sha256=sha(Path(__file__).read_bytes()),
        evidence_validator_sha256=sha((ROOT/'scripts/presentation_experiment_evidence.py').read_bytes()),
        scope='Measured complete frames including all added work; paired source state and original pixel oracles. Not stable30/60Hz, all-level, listening, owner or physical acceptance. Oracle/zero-stage fields in detailed analysis are hypothetical only.')
    (root/('comparison-'+output_suffix+'.json')).write_text(json.dumps(summary,indent=2)+'\n')
    (root/('analysis-'+output_suffix+'.json')).write_text(json.dumps(dict(results=results,candidate_rom_sha256=candidate_sha,model_scope=summary['scope']),indent=2)+'\n')
    print(json.dumps([r for r in rows if r['population']=='active'],indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--suffix',required=True);parser.add_argument('--kind',choices=('shared','prepared'),required=True)
    parser.add_argument('--scene-suffix')
    parser.add_argument('--output-suffix')
    args=parser.parse_args();report(args.root.resolve(),args.build.resolve(),args.suffix,args.kind,args.scene_suffix,args.output_suffix)
