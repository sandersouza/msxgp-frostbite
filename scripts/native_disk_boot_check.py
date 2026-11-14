"""Real MSX1 DOS1/Disk BASIC loading; no target RAM or PC injection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
from build_native_flat_image import digest
from smoke import validate_machine_profile
from render_build import symbols


def check(disk,cold,out,mode,family,*,dos1_disk,machine_profile=None,firmware_dir=None,emulator=None):
    disk,cold,out=disk.resolve(),cold.resolve(),out.resolve()
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((disk/'native-disk.json').read_bytes());c=json.loads((cold/'cold-image.json').read_bytes())
    ram=(cold/'cold-ram.bin').read_bytes();video=(cold/'cold-vram.bin').read_bytes()
    if digest(ram)!=m['cold_RAM_sha256'] or digest(video)!=m['cold_VRAM_sha256']:raise ValueError('identical native cold payload required')
    for name,row in m['files'].items():
        if (disk/name).stat().st_size!=row['size'] or digest((disk/name).read_bytes())!=row['sha256']:raise ValueError('bound disk delivery files required')
    emulator=Path(emulator or shutil.which('openmsx') or 'openmsx').resolve()
    if machine_profile:profile=Path(machine_profile)
    else:
        candidates=(emulator.parent.parent/'Resources/share/machines/Sony_HB-701FD.xml',
                    emulator.parent.parent/'openMSX.app/Contents/Resources/share/machines/Sony_HB-701FD.xml',
                    emulator.parent.parent/'share/openmsx/machines/Sony_HB-701FD.xml')
        profile=next((p for p in candidates if p.exists()),None)
        if profile is None:raise ValueError('pass installed --machine-profile Sony_HB-701FD.xml explicitly')
    firmware_dir=Path(firmware_dir) if firmware_dir else Path.home()/'.openMSX/share/systemroms/sony'
    root=ET.fromstring(profile.read_bytes());firmware=[]
    for node in root.findall('.//rom'):
        f=node.find('filename');p=firmware_dir/f.text
        data=p.read_bytes();wanted=[n.text for n in node.findall('sha1')]
        if wanted and hashlib.sha1(data).hexdigest() not in wanted:raise ValueError('real Sony firmware differs: '+p.name)
        f.text=str(p);firmware.append(dict(filename=p.name,sha256=digest(data)))
    vdp=root.find('.//VDP');vdp.find('version').text='TMS9918A' if family=='ntsc' else 'TMS9929A'
    ET.SubElement(vdp,'vram').text='16'
    raw=b'<?xml version="1.0"?><!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">'+ET.tostring(root)
    validate_machine_profile(raw);out.mkdir(parents=True);user=out/'user-data';(user/'machines').mkdir(parents=True)
    (user/'machines/Frostbite_RealDisk.xml').write_bytes(raw)
    original=Path(dos1_disk).resolve();boot=out/'boot.dsk';shutil.copyfile(original,boot)
    boot_sha=digest(original.read_bytes())
    if mode=='dos':
        auto=out/'AUTOEXEC.BAT';auto.write_bytes(b'VER\r\nFROSTBIT\r\n\x1A');imports=[disk/'FROSTBIT.COM',auto]
        entry=0x100;executable=(disk/'FROSTBIT.COM').read_bytes();setup=''
    else:
        auto=out/'AUTOEXEC.BAS';auto.write_bytes(b'10 RUN"FROSTBIT.BAS"\r\n\x1A');imports=[disk/n for n in ('FROSTBIT.BAS','FROSTBIT.BIN','FBGFX.BIN')]+[auto]
        entry=int.from_bytes((disk/'FROSTBIT.BIN').read_bytes()[1:3],'little');executable=(disk/'FROSTBIT.BIN').read_bytes()[7:];setup=''
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    # The original Sony drive is single-sided80-track360K. Keep the owner's
    # DOS1 source image immutable; transfer its actual system files to a fresh
    # correctly sized private disk instead of treating720K as compatible.
    sysdir=out/'system-files';sysdir.mkdir()
    fresh=out/'native360.dsk'
    setup=f'diskmanipulator export diska {{{sysdir}}}\ndiskmanipulator create {{{fresh}}} 360\ndiska {{{fresh}}}\n'
    if mode=='dos':
        setup+=f'''set sysfiles {{}}
foreach f [glob {{{sysdir}/*}}] {{if {{[string toupper [file tail $f]] in {{MSXDOS.SYS COMMAND.COM}}}} {{lappend sysfiles $f}}}}
if {{[llength $sysfiles]!=2}} {{error "actual DOS1 system files required"}}
diskmanipulator import diska {{*}}$sysfiles
'''
    paths=' '.join('{'+str(p)+'}' for p in imports)
    tcl=f'''set save_settings_on_exit false
set renderer none
set throttle off
set power off
set native_seen 0
set disk_entry_seen 0
set pictures 0
set stage_log [open {{{out/'stages.txt'}}} w]
proc fail_disk {{message}} {{puts stderr "NATIVE_DISK_FAIL $message PC=[reg PC]";exit 1}}
{setup}
diskmanipulator import diska {paths}
debug set_bp {entry} {{!$::disk_entry_seen && [debug read_block memory {entry} 24] eq [binary format H* {executable[:24].hex()}]}} {{
 set ::disk_entry_seen 1
 puts $::stage_log "REAL_{mode.upper()}_ENTRY time=[machine_info time] TPA=[debug read_block memory 6 2]"
 flush $::stage_log
 set f [open {{{out/'OS-screen.bin'}}} wb];puts -nonewline $f [debug read_block VRAM 0 16384];close $f
}}
debug set_bp {c['native_symbols']['nc_entry']} {{!$::native_seen && $::disk_entry_seen}} {{
 if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_disk target}}
 if {{[debug read_block memory 0 62208] ne [binary format H* {ram[:0xF300].hex()}]}} {{fail_disk exact-low-RAM}}
 if {{[debug read_block memory 62336 3188] ne [binary format H* {ram[0xF380:0xFFF4].hex()}]}} {{fail_disk exact-high-RAM}}
 if {{[debug read_block VRAM 0 16384] ne [binary format H* {video.hex()}]}} {{fail_disk exact-VRAM}}
 set ::native_seen 1
 puts $::stage_log "EXACT_NATIVE_COLD_STATE time=[machine_info time] slot=[debug read ioports 168]"
 flush $::stage_log
 after time 4 {{
  set commits [expr {{[debug read memory 0xE88A]+256*[debug read memory 0xE88B]}}]
  if {{$commits<30}} {{fail_disk no-gameplay}}
  set f [open {{{out/'complete.txt'}}} w];puts $f "{mode} native cold equality; committed pictures=$commits IRQ services=$::pictures";close $f
  close $::stage_log;exit
 }}
}}
debug set_bp 0xEA7D {{$::native_seen}} {{incr ::pictures}}
after time 15 {{if {{!$::native_seen}} {{
 set f [open {{{out/'waiting-VRAM.bin'}}} wb];puts -nonewline $f [debug read_block VRAM 0 16384];close $f
 set f [open {{{out/'waiting-regs.bin'}}} wb];puts -nonewline $f [debug read_block {{VDP regs}} 0 8];close $f
}}}}
after time 90 {{fail_disk timeout}}
set power on
'''
    (out/'launch.tcl').write_text(tcl)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_RealDisk','-diska',str(boot),'-script',str(out/'launch.tcl')],env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    (out/'emulator.log').write_text(run.stdout+run.stderr)
    if run.returncode or not (out/'complete.txt').exists():raise ValueError('real native disk boot failed: '+(run.stdout+run.stderr)[-1800:])
    if digest(original.read_bytes())!=boot_sha:raise ValueError('immutable DOS1 source disk changed')
    for name,row in m['files'].items():
        if digest((disk/name).read_bytes())!=row['sha256']:raise ValueError('executed disk file changed during qualification')
    result=dict(complete=True,format=mode,family=family,actual_disk_loading=True,real_MSX1_BIOS_and_BASIC=True,firmware=firmware,
                source_bootdisk_sha256=digest(original.read_bytes()),profile_sha256=digest(raw),files=m['files'],
                exact_cold_RAM_and_VRAM=True,host_target_state_injection=False,physical_hardware=False,
                scope='Real disk file load, exact shared cold low/high/VRAM initializer equality and subsequent renderer/IRQ execution; no physical acceptance.')
    (out/'native-disk-check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('disk','cold','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--mode',choices=('dos','basic'),required=True);p.add_argument('--family',choices=('ntsc','pal'),default='ntsc')
    p.add_argument('--dos1-disk',type=Path,required=True,help='local licensed DOS1 disk; read-only source of MSXDOS.SYS and COMMAND.COM')
    for n in ('machine-profile','firmware-dir','emulator'):p.add_argument('--'+n,type=Path)
    a=p.parse_args();check(a.disk,a.cold,a.out,a.mode,a.family,dos1_disk=a.dos1_disk,machine_profile=a.machine_profile,firmware_dir=a.firmware_dir,emulator=a.emulator)
