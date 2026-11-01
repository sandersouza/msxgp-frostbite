"""Closed raw-artifact sets and independently checked failure identities."""
import hashlib
import json
from pathlib import Path

VISUAL_ROOT=frozenset(('adapters.bin','before_regs.bin','before_vram.bin','build.json','complete.json','emulator.log',
    'initial.bin','launch.tcl','prepared.bin','prepared_regs.bin','presented.bin','presented_regs.bin',
    'scene_actual.bin','scenes.bin','settings.xml','states.bin'))
VISUAL_PROFILE='user-data/machines/Frostbite_Movement.xml'
CPU_PROFILE='user-data/machines/Frostbite_Native.xml'
PORT2_DECLARED=frozenset(('actual.bin','cases.bin','complete.json','emulator.log','expected.json'))
FAILURES={'spacing':('emulator','fast-io-spacing'),'sprite':('emulator','fifth-sprite-slot'),
    'guard':('emulator','heap-guard'),'state':('comparison','RAM AA'),'pixel':('comparison','pixel mismatch'),
    'port2_fire':('comparison','RAM AF')}


def cpu_files(devices=False,verified=True):
    names={'native-contract.rom','build.json','cases.bin','expected.json','actual.bin','complete.json','emulator.log','launch.tcl','settings.xml',CPU_PROFILE}
    if verified:names.add('verified.json')
    if devices:names|={'devices.omr','mirrors.bin','seed.omr','seed.tcl'}
    return frozenset(names)


def visual_files(rom_name,verified=True,complete=True):
    names=set(VISUAL_ROOT)|{rom_name,VISUAL_PROFILE}
    if verified:names.add('verified.json')
    if not complete:names.remove('complete.json')
    return frozenset(names)


def digest_files(directory,required):
    directory=Path(directory);result={}
    for name in sorted(required):
        relative=Path(name);path=directory/relative
        if relative.is_absolute() or '..' in relative.parts or not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError(f'missing/unsafe required artifact: {name}')
        result[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def audit_files(directory,hashes,required):
    if not isinstance(hashes,dict) or set(hashes)!=set(required):raise ValueError('complete fixed artifact set required')
    if digest_files(directory,required)!=hashes:raise ValueError('required artifact hash differs')


def validate_failure_identity(record):
    expected=FAILURES.get(record.get('injection'))
    if (expected is None or record.get('detected') is not True or (record.get('stage'),record.get('cause'))!=expected
            or expected[1] not in record.get('detail','')):raise ValueError('wrong/missing negative failure identity')


def cpu_row(data):
    if len(data)!=133:raise ValueError('complete CPU/RAM row required')
    return {'registers':dict(zip(('a','x','y','p','sp'),data[:5])),'ram':list(data[5:])}


def verify_failure_data(record,directory,baseline=None):
    """Derive each intended failure from existing raw logs or raw comparisons.

    The state/pixel controls have identical first-step inputs to the verified
    NTSC baseline. Reuse that already source/pixel-checked result as the oracle;
    no source ROM or mutable emulator installation is needed for this audit.
    """
    validate_failure_identity(record);directory=Path(directory);fault=record['injection']
    if record['stage']=='emulator':
        if f'MOVEMENT_FAIL {record["cause"]}' not in (directory/'emulator.log').read_text():raise ValueError('negative cause absent from emulator records')
    elif fault=='port2_fire':
        from native_contract import compare
        expected=json.loads((directory/'expected.json').read_text());actual=(directory/'actual.bin').read_bytes()
        if len(actual)!=len(expected)*233:raise ValueError('incomplete port2 raw records')
        found=None
        for i,want in enumerate(expected):
            try:compare(want,cpu_row(actual[i*233:i*233+133]))
            except ValueError as error:found=f'{want["id"]}: {error}';break
        if found is None or 'RAM AF' not in found or found!=record['detail'].split('; ',1)[0]:raise ValueError('port2 raw comparison does not prove expected failure')
    elif fault=='state':
        from native_contract import compare
        before=(directory/'states.bin').read_bytes()[:271];normal=(Path(baseline)/'states.bin').read_bytes()[:271]
        if len(before)!=271 or len(normal)!=271 or before[:133]!=normal[:133] or before[266:]!=normal[266:]:raise ValueError('state negative inputs differ from verified baseline')
        try:compare(cpu_row(normal[133:266]),cpu_row(before[133:266]))
        except ValueError as error:
            if 'RAM AA' not in str(error) or str(error) not in record['detail']:raise ValueError('wrong state negative comparison') from error
        else:raise ValueError('state negative raw corruption absent')
    elif fault=='pixel':
        import render_model as model
        normal=Path(baseline)
        if (directory/'scene_actual.bin').read_bytes()[:32]!=(normal/'scene_actual.bin').read_bytes()[:32]:raise ValueError('pixel negative scene differs from verified baseline')
        def image(folder):return model.decode_pixels((folder/'presented.bin').read_bytes()[:16384],list((folder/'presented_regs.bin').read_bytes()[:8]))
        if image(directory)==image(normal):raise ValueError('pixel negative raw corruption absent')
    else:raise ValueError('unsupported negative comparison')
