#!/usr/bin/env python3
"""Bounded, fresh openMSX diagnostic checks on an isolated unexpanded profile."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from rom import ROOT, OUT, ROM, validate_rom


def validate_build_identity(data, metadata):
    if (metadata.get('diagnostic') is not True or metadata.get('rom',{}).get('size')!=len(data)
        or metadata.get('rom',{}).get('sha256')!=hashlib.sha256(data).hexdigest()):
        raise ValueError('ROM does not match its diagnostic build identity')


def validate_machine_profile(data):
    root=ET.fromstring(data)
    ram=sum(int(node.attrib['size'],0) for node in root.findall('.//RAM/mem'))
    if ram!=65536 or root.findall('.//MemoryMapper'):
        raise ValueError('diagnostic requires unexpanded 64 KiB RAM')
    vdp=root.find('.//VDP')
    if vdp is None or not vdp.findtext('version','').startswith(('TMS9918','TMS9928','TMS9929')):
        raise ValueError('diagnostic requires TMS9918-family VDP')
    if vdp.findtext('vram')!='16':
        raise ValueError('diagnostic requires configured 16 KiB VRAM')


def find_machine_profile(executable):
    prefix=Path(executable).resolve().parent.parent
    candidates=[prefix/'openMSX.app/Contents/Resources/share/machines/C-BIOS_MSX1.xml',
                prefix/'share/openmsx/machines/C-BIOS_MSX1.xml',
                Path('/usr/share/openmsx/machines/C-BIOS_MSX1.xml')]
    for path in candidates:
        if path.is_file():
            return path
    raise ValueError('C-BIOS_MSX1 profile not found; install full openMSX data or pass --machine-profile')


def isolated_profile(path):
    root=ET.fromstring(path.read_bytes())
    for descriptor in root.findall('.//ROM/rom'):
        filename=descriptor.find('filename')
        if filename is None or not filename.text:
            raise ValueError('C-BIOS profile has no firmware filename')
        firmware=(path.parent/filename.text.strip()).resolve()
        data=firmware.read_bytes()
        expected=descriptor.findtext('sha1')
        if expected and hashlib.sha1(data).hexdigest()!=expected.strip():
            raise ValueError(f'bundled C-BIOS firmware identity mismatch: {firmware}')
        filename.text=str(firmware)
    return (b'<?xml version="1.0"?>\n<!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">\n'
            + ET.tostring(root,encoding='utf-8'))


def run_smoke(rom=ROM, metadata_path=OUT/'build.json', screenshot=False, machine_profile=None):
    (OUT/'smoke.json').unlink(missing_ok=True)
    data=rom.read_bytes()
    problems=validate_rom(data)
    if problems:
        raise ValueError('; '.join(problems))
    metadata=json.loads(metadata_path.read_text())
    validate_build_identity(data,metadata)
    emulator=shutil.which('openmsx')
    if emulator is None:
        raise ValueError('openmsx unavailable; run environment setup')
    profile=machine_profile or find_machine_profile(emulator)
    profile_data=profile.read_bytes()
    validate_machine_profile(profile_data)
    OUT.mkdir(parents=True,exist_ok=True)
    directory=Path(tempfile.mkdtemp(prefix='smoke-',dir=OUT))
    user_data=directory/'user-data'
    machines=user_data/'machines'
    machines.mkdir(parents=True)
    # Unique user data search path prevents an existing user machine overriding it.
    effective_profile=isolated_profile(profile)
    (machines/'Frostbite_Diagnostic.xml').write_bytes(effective_profile)
    settings=directory/'settings.xml'
    settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd">'
                        '<settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    result_path=directory/'result.json'
    screenshot_path=directory/'diagnostic.png'
    env={**os.environ,'OPENMSX_USER_DATA':str(user_data),
         'FROSTBITE_SMOKE_RESULT':str(result_path),'FROSTBITE_SMOKE_ROM':str(rom.resolve()),
         'FROSTBITE_CAPTURE':'1' if screenshot else '0','FROSTBITE_SCREENSHOT':str(screenshot_path),
         'SDL_AUDIODRIVER':'dummy'}
    if screenshot:
        env.pop('SDL_VIDEODRIVER',None)
    else:
        env['SDL_VIDEODRIVER']='dummy'
    command=[emulator,'-setting',str(settings),'-machine','Frostbite_Diagnostic',
             '-cart',str(rom.resolve()),'-romtype','Normal','-script',str(ROOT/'scripts/smoke.tcl')]
    try:
        process=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=30)
    except subprocess.TimeoutExpired as error:
        (directory/'emulator.log').write_text(str(error))
        raise ValueError(f'diagnostic timed out; no acceptance claimed; see {directory}') from error
    (directory/'emulator.log').write_text(process.stdout+process.stderr)
    if process.returncode or not result_path.exists():
        raise ValueError(f'no fresh successful diagnostic result; see {directory}/emulator.log')
    result=json.loads(result_path.read_text())
    if result.get('passed') is not True:
        raise ValueError(f'diagnostic check failed; see {directory}/emulator.log')
    if rom.read_bytes()!=data:
        raise ValueError('ROM changed during smoke; evidence rejected')
    if screenshot and not screenshot_path.is_file():
        raise ValueError('requested screenshot missing')
    result.update({'version':metadata['version'],'rom_sha256':hashlib.sha256(data).hexdigest(),
        'source_commit':metadata['source_commit'],'source_dirty':metadata['source_dirty'],
        'emulator':subprocess.check_output([emulator,'-v'],text=True).strip(),
        'machine_profile':str(profile),'machine_profile_sha256':hashlib.sha256(profile_data).hexdigest(),
        'effective_profile_sha256':hashlib.sha256(effective_profile).hexdigest(),
        'artifacts_directory':str(directory.relative_to(ROOT)),
        'acceptance':'Automated diagnostic only; manual listening and physical MSX pending; no gameplay acceptance.'})
    if screenshot:
        result['screenshot']=str(screenshot_path.relative_to(ROOT))
    (OUT/'smoke.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'Diagnostic smoke passed: ROM SHA-256 {result["rom_sha256"]}; artifacts {directory}')
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROM)
    parser.add_argument('--build-metadata',type=Path,default=OUT/'build.json')
    parser.add_argument('--machine-profile',type=Path)
    parser.add_argument('--screenshot',action='store_true')
    args=parser.parse_args(argv)
    try:
        run_smoke(args.rom,args.build_metadata,args.screenshot,args.machine_profile)
        return 0
    except (OSError,ValueError,KeyError,ET.ParseError,subprocess.SubprocessError) as error:
        print(f'Smoke failed: {error}',file=sys.stderr)
        return 1


if __name__=='__main__':
    sys.exit(main())
