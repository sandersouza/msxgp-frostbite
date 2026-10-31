#!/usr/bin/env python3
"""Publish only compact verified evidence, never raw state or original assets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from reference_inventory import ROOT, load_manifest

COMPONENTS = {'stella':('reference-traces','reference_traces'), 'cpu':('reference-cpu','reference_cpu_check'),
              'ale':('reference-ale','reference_ale_check'), 'refuge':('reference-refuge','reference_routes'),
              'console':('reference-console','reference_routes')}
NEGATIVES = {'coordinate','flag','collision','order','input','seed'}


def require(condition, message):
    if not condition: raise ValueError(message)


def digest(value, length=64):
    require(isinstance(value,str) and re.fullmatch(f'[0-9a-f]{{{length}}}',value), 'invalid evidence hash/revision')


def validate_reports(source_sha, parts):
    require(set(parts)==set(COMPONENTS),'all five source evidence classes required')
    for part in parts.values():
        require(part['schema_version']==1 and part['source']['sha256']==source_sha,'evidence source/schema mismatch')
        digest(part['tool_source_commit'],40);digest(part['utility_sha256'])
    stella=parts['stella'];cpu=parts['cpu'];ale=parts['ale'];refuge=parts['refuge'];console=parts['console']
    backend=stella['backend']
    require(backend['name']=='Stella' and backend['version']=='7.0'
            and backend['source_contract']=='d55b1aec0d067a4c901a6dcdf81cb8f579685659','unsupported source backend')
    digest(backend['binary_sha256'])
    require(ale['backend']['name']=='ALE' and ale['backend']['source_commit']=='8a8fafb1ac37796e3e8197a2e5727204fa1b926d',
            'unsupported secondary backend')
    digest(ale['backend']['binary_sha256'])
    require(re.fullmatch('[0-9][0-9A-Za-z.+-]{0,39}',ale['backend']['numpy']), 'invalid NumPy version metadata')
    require(stella['warmup_full_states_equal'] is True and stella['warmup_intervals']==32,'warmup evidence incomplete')
    require([s['variation'] for s in stella['scenarios']]==[0,1,2,3],'all four original variations required')
    for scenario in stella['scenarios']:
        require(scenario['full_states_equal'] is True and set(scenario['negative_controls_detected'])==NEGATIVES,
                'source replay/negative controls incomplete')
        require(type(scenario['steps']) is int and 0<scenario['steps']<=5000,'invalid source interval count')
        digest(scenario['trace_sha256']);digest(scenario['raw_state_chain_sha256'])
    turns=stella['controlled_player1_turns']
    require([turn['variation'] for turn in turns]==[1,3],'both alternating-mode fixtures required')
    for turn in turns:
        require(turn['full_states_equal'] is True and turn['port1_direction_and_fire_observed'] is True,'port1 evidence incomplete')
        digest(turn['trace_sha256'])
    require(cpu['stella']==stella['backend'] and cpu['py65']=='1.2.0','CPU backend identity mismatch')
    require(cpu['matched']==cpu['total']==374 and cpu['mechanics_cases_checked']==86
            and cpu['arithmetic_boundary_vectors']==288 and cpu['excluded_constant_mmio_cases']==15,'CPU matrix incomplete/failed')
    require([mode['mode'] for mode in ale['modes']]==[0,2] and ale['backend']['version']=='0.12.1','ALE mode/version mismatch')
    for mode in ale['modes']:
        require(mode['steps']==27 and mode['full_serialized_states_equal'] is True
                and mode['ram_screen_inputs_equal'] is True,'ALE full-state evidence incomplete')
        require(mode['policy']=={'seed':1,'frame_skip':1,'repeat_action_probability':0},'ALE policy mismatch')
    observation=refuge['observation']
    require(refuge['steps']==1056 and refuge['independent_runs']==2 and refuge['full_states_equal'] is True,'natural route incomplete')
    require(observation['effective_bear_hits']==0 and observation['reserve']==3
            and observation['grounded_shore'] is True and observation['bear_blocked_at_edge'] is True
            and 0<=observation['refuge_x']<16,'natural refuge failed')
    require(console['steps']==125 and console['full_states_equal'] is True
            and console['observed_wrap_modes']==[3,0,1,2] and console['mode_after_select_hold35']==0
            and console['mode_after_reset_select']==0,'console wrap/hold/priority evidence failed')
    for part in (refuge,console):
        require(part['provenance']['preparation_trace_sha256']==stella['scenarios'][2]['trace_sha256'],
                'route preparation differs from current source trace')


def select(record, names):
    return {name:record[name] for name in names.split()}


def compact_reports(source_sha, parts):
    validate_reports(source_sha,parts)
    stella,cpu,ale,refuge,console=(parts[name] for name in COMPONENTS)
    backend_keys='name version source_contract binary_sha256'
    result={'schema_version':1,'source_sha256':source_sha,
        'scope':'Independent original-execution oracles; no MSX gameplay/hardware acceptance',
        'stella':{'backend':select(stella['backend'],backend_keys),
            **select(stella,'warmup_intervals warmup_full_states_equal config_sha256 poweron_sha256 aligned_sha256'),
            'initial_conditions':select(stella['policy'],'host_seed riot_timer_preset'),
            'scenarios':[select(s,'variation steps mode_after_reset player_after_reset full_states_equal trace_sha256 raw_state_chain_sha256 negative_controls_detected') for s in stella['scenarios']],
            'controlled_player1_turns':[select(s,'variation steps full_states_equal port1_direction_and_fire_observed trace_sha256') for s in stella['controlled_player1_turns']]},
        'cpu':select(cpu,'py65 py65_cpu_source_sha256 cases_sha256 mechanics_cases_checked arithmetic_boundary_vectors excluded_constant_mmio_cases matched total'),
        'ale':{'backend':select(ale['backend'],'name version source_commit binary_sha256 numpy'),
               'modes':[select(mode,'mode steps policy full_serialized_states_equal ram_screen_inputs_equal initial_sha256 trace_sha256') for mode in ale['modes']]},
        'refuge':{**select(refuge,'steps independent_runs full_states_equal trace_sha256'),
            'config_sha256':refuge['policy']['config_sha256'],
            'observation':select(refuge['observation'],'refuge_x bear_min bear_max bear_direction_reversals bear_blocked_at_edge reserve grounded_shore effective_bear_hits')},
        'console':select(console,'steps full_states_equal observed_wrap_modes mode_after_select_hold35 mode_after_reset_select trace_sha256')}
    for name in ('refuge','console'):
        result[name]['provenance']=select(parts[name]['provenance'],'preparation_summary_sha256 preparation_trace_sha256 source_sha256 preparation_tool_commit')
    result['limits']=['Controlled power-on RIOT/host seed, not every physical power-on',
        'C7=1 port1 fixtures do not prove natural death/record swapping',
        'One natural refuge route, not every geometry or complete game',
        'ADC/SBC boundary matrix, not exhaustive NMOS conformance',
        'ALE modes0/2 startup is not aligned to Stella; no cross-backend whole-state equality',
        'Native logical adapter, target timing, audio, PAL and physical MSX remain later gates']
    return result


def audit_producer(report, script_path, root=ROOT):
    commit=report['tool_source_commit'];digest(commit,40);digest(report['utility_sha256'])
    blob=subprocess.check_output(['git','show',f'{commit}:{script_path}'],cwd=root,timeout=30)
    require(hashlib.sha256(blob).hexdigest()==report['utility_sha256'],'reported utility does not match producer commit')


def assemble():
    parts={};raw_hashes={}
    for name,(directory,module) in COMPONENTS.items():
        path=ROOT/f'outputs/{directory}/summary.json';data=path.read_bytes()
        parts[name]=json.loads(data);raw_hashes[name]=hashlib.sha256(data).hexdigest()
        audit_producer(parts[name],f'scripts/{module}.py')
    source_sha=load_manifest()['input']['sha256']
    result=compact_reports(source_sha,parts)
    for name,path,key in (('stella','references/trace-scenarios.json','config_sha256'),
                         ('cpu','references/mechanics-cases.json','cases_sha256'),
                         ('refuge','references/refuge-scenario.json','config_sha256')):
        part=parts[name];expected=part['policy'][key] if name=='refuge' else part[key]
        blob=subprocess.check_output(['git','show',f'{part["tool_source_commit"]}:{path}'],cwd=ROOT,timeout=30)
        require(hashlib.sha256(blob).hexdigest()==expected,'producer input/config identity mismatch')
    result['producers']={name:{**select(part,'tool_source_commit utility_sha256'),'private_summary_sha256':raw_hashes[name]}
                         for name,part in parts.items()}
    result['logical_projection']={'contract':'frostbite/source-logical/F019/v1',
        'utility_sha256':hashlib.sha256((ROOT/'scripts/trace_compare.py').read_bytes()).hexdigest(),
        'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
    result['publication']={'utility_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                           'tool_source_commit':result['logical_projection']['tool_source_commit']}
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'references/reference-traces.json')
    args=parser.parse_args(argv)
    try:
        report=assemble();args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+'\n')
        print(f'Compact reference evidence/producers verified: {args.output}');return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print(f'Reference publication refused: {error}',file=sys.stderr);return 1


if __name__=='__main__':sys.exit(main())
