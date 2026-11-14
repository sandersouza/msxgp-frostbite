"""Seal already-qualified native artifacts; never rebuild or modify game bytes."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import zipfile
from build_native_flat_image import digest
from environment import ROOT

VERSION='v0.0.31-native-formats-diagnostic'


def package(build,qualification,matrix,extended,boundaries,disk_checks,workbook,out):
    build,qualification,matrix,extended,boundaries,disk_checks,out=(p.resolve() for p in (build,qualification,matrix,extended,boundaries,disk_checks,out))
    if out.exists():raise ValueError('fresh release output required')
    qualification_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for name in ('scripts/package_native_diagnostic.py','scripts/native_flat_takeover_check.py','scripts/native_disk_boot_check.py'):
        result=subprocess.run(['git','show',qualification_commit+':'+name],cwd=ROOT,capture_output=True)
        if result.returncode or digest(result.stdout)!=digest((ROOT/name).read_bytes()):
            raise ValueError('qualification/packaging source must be committed before sealing: '+name)
    m=json.loads((build/'native-delivery-build.json').read_bytes())
    artifacts={}
    for name,row in m['files'].items():
        p=build/name
        if p.stat().st_size!=row['size'] or digest(p.read_bytes())!=row['sha256']:raise ValueError('native product changed: '+name)
        artifacts[p.name]=dict(row)
    if artifacts['FROSTBIT.ROM']['size']!=32768 or (build/'cartridge/FROSTBIT.ROM').read_bytes()[:2]!=b'AB':raise ValueError('complete Normal32K required')
    for name,value in m['source_files'].items():
        original=subprocess.check_output(['git','show',m['source_commit']+':'+name],cwd=ROOT)
        if digest(original)!=value or digest((build/'source'/name).read_bytes())!=value:
            raise ValueError('source archive is not the declared committed source: '+name)
    checks={};metrics={};accepted=json.loads((ROOT/'outputs/presentation/credit-reference-at/release/PERFORMANCE.json').read_bytes())
    def native(label,path):
        d=json.loads(path.read_bytes())
        if not d['complete'] or not d['native_product_loader'] or d['executed_ROM_sha256']!=artifacts['FROSTBIT.ROM']['sha256']:
            raise ValueError('actual native-cartridge qualification required: '+label)
        oracle=path.parent/'check.json'
        if digest(oracle.read_bytes())!=d['oracle_receipt_sha256']:raise ValueError('bound inner oracle changed')
        checks[label]=dict(path=str(path.relative_to(ROOT)),sha256=digest(path.read_bytes()),result=d)
        return json.loads(oracle.read_bytes())
    for mode in ('ntsc','pal','bear-ntsc','bear-pal'):
        d=native(mode,qualification/mode/'native-takeover.json')
        if not all(d[n] for n in ('source_cpu_all_ram_equal','coherent_picture_pixels_equal','physical_owners_equal')) or d['late_vblanks'] or d['canonical_source_writes']:
            raise ValueError('source/picture/IRQ oracle must pass')
        a=accepted['comparison'][mode]['metrics'];rate=d['active_pictures_per_second']
        metrics[mode]=dict(active_pictures_per_second=rate,accepted_v30_pictures_per_second=a['active_pictures_per_second'],
            cadence_change=rate/a['active_pictures_per_second']-1,mean_prepare_elapsed_cycles=d['mean_prepare_elapsed_cycles'],
            source_steps_per_second=d['source_steps_per_second'])
    for label,p,cases in (('matrix',matrix/'native-takeover.json',2115),('density',extended/'density/native-takeover.json',1920),('header',extended/'header/native-takeover.json',54)):
        d=native(label,p)
        if d['cases']!=cases or d['different_frames']:raise ValueError('complete zero-difference scene proof required')
    # Boundary tests have an explicit replacement for the retired mapper and
    # deliberately delayed timings. Keep them out of cadence metrics.
    for family in ('ntsc','pal'):
        p=boundaries/f'boundary-{family}/native-takeover.json';d=native('boundary-'+family,p)
        b=json.loads((p.parent/'boundary-check.json').read_bytes())
        if len(b['boundaries'])!=9 or not checks['boundary-'+family]['result']['native_IRQ_boundary_relocation']:
            raise ValueError('all nine native IRQ boundaries required')
    expected={n:artifacts[n] for n in ('FROSTBIT.COM','FROSTBIT.BIN','FBGFX.BIN','FROSTBIT.BAS')}
    for name in ('ntsc-dos','ntsc-basic','pal-dos','pal-basic'):
        p=disk_checks/name/'native-disk-check.json';d=json.loads(p.read_bytes())
        if not d['complete'] or not d['actual_disk_loading'] or not d['exact_cold_RAM_and_VRAM'] or d['host_target_state_injection'] or d['files']!=expected:
            raise ValueError('all four actual disk load checks required')
        checks[name]=dict(path=str(p.relative_to(ROOT)),sha256=digest(p.read_bytes()),result=d)
    out.mkdir(parents=True)
    rom_name='frostbite-0.0.31-native-formats-diagnostic.rom'
    shutil.copyfile(build/'cartridge/FROSTBIT.ROM',out/rom_name)
    for name in expected:shutil.copyfile(build/'disk'/name,out/name)
    shutil.copyfile(workbook,out/workbook.name)
    notes=ROOT/'docs/releases/v0.0.31-native-formats-diagnostic.md';shutil.copyfile(notes,out/'TESTS.md')
    validation=dict(complete=True,scope='bounded automated native-format diagnostic qualification',
        version=VERSION,runtime_source_commit=m['source_commit'],artifacts=artifacts,checks=checks,
        issue44_complete=False,cadence_accepted=False,owner_acceptance=False,physical_hardware=False,manual_audio_listening=False)
    (out/'VALIDATION.json').write_text(json.dumps(validation,indent=2)+'\n')
    (out/'PERFORMANCE.json').write_text(json.dumps(dict(version=VERSION,metrics=metrics,cadence_accepted=False),indent=2)+'\n')
    (out/'SOURCE.txt').write_text('Runtime source: '+m['source_commit']+'\nNative payloads are reproduced from source-defined initializers, never captured emulator state.\nQualification source: '+qualification_commit+'\n')
    with zipfile.ZipFile(out/(VERSION+'.zip'),'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in ('FROSTBIT.COM','FROSTBIT.BIN','FBGFX.BIN','FROSTBIT.BAS','TESTS.md','SOURCE.txt'):
            z.write(out/name,name)
        z.write(out/rom_name,'FROSTBIT.ROM')
    with zipfile.ZipFile(out/(VERSION+'.zip')) as z:
        if z.testzip() or digest(z.read('FROSTBIT.ROM'))!=artifacts['FROSTBIT.ROM']['sha256']:raise ValueError('release ZIP verification failed')
    files={p.name:digest(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
    (out/'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name,value in files.items()))
    print(dict(version=VERSION,runtime_source_commit=m['source_commit'],files=files,cadence_accepted=False))
    return validation


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','qualification','matrix','extended','boundaries','disk-checks','workbook','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();package(a.build,a.qualification,a.matrix,a.extended,a.boundaries,a.disk_checks,a.workbook,a.out)
