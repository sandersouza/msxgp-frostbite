"""Read the complete frozen source-observation domain, without recapturing it."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from environment import ROOT
from original_graphics import SOURCE_SHA256
from presentation_records import normalize_frame,parse_records
from presentation_source_check import CHECK_FILES as SOURCE_FILES,audit_capture,read_blob
from reference_provenance import audit_manifest

FILES=tuple(dict.fromkeys((*SOURCE_FILES,'scripts/presentation_source_cases.py',
    'references/presentation-assets-config.json','references/presentation-source-config.json','references/presentation-source-result.json')))
EXPECTED={'fixtures':1690,'cold_route':31,'natural_window':394}


def sha(data):return hashlib.sha256(data).hexdigest()


def validate_domain(cases,unmapped):
    counts=dict(Counter(row['family'] for row in cases))
    if counts!=EXPECTED or unmapped!=7 or len({row['id'] for row in cases})!=2115:
        raise ValueError('whole unique approved source domain and seven explicit startup frames required')
    return counts


def collect():
    config_path=ROOT/'references/presentation-assets-config.json';config=json.loads(config_path.read_text())
    summary_path=ROOT/config['source_summary'];summary=json.loads(summary_path.read_text())
    receipt_path=ROOT/config['source_receipt'];receipt=json.loads(read_blob(receipt_path,summary['private_sha256']))
    audit_manifest(receipt['checker_producer'],SOURCE_FILES)
    if receipt['checker_producer']!=summary['checker_producer'] or receipt['source_sha256']!=SOURCE_SHA256:
        raise ValueError('source proof producer/ROM differs from approved authority')
    source_path=ROOT/config['source_config'];source=json.loads(source_path.read_text());backend=ROOT/source['backend']
    roots=[]
    for family in ('fixtures','cold_route'):
        root=ROOT/source[family][0];expected=receipt['groups'][family]['repeats'][0]['report_sha256']
        roots.append((root,family,expected))
    for window in receipt['groups']['natural_windows']['windows']:
        root=ROOT/source['windows'][0]/f'{window["route"]}-{window["event"]}'
        roots.append((root,'natural_window',window['report_sha256']))
    files={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (config_path,summary_path,receipt_path,source_path)}
    cases=[];startup=0;audits=[]
    for root,family,expected in roots:
        read_blob(root/'report.json',expected)
        audited=audit_capture(root,backend,family=='fixtures',family=='cold_route')
        if audited['report_sha256']!=expected:raise ValueError('source report changed while auditing')
        audits.append({'root':str(root.relative_to(ROOT)),'family':family,'report_sha256':expected})
        for path in sorted(root.rglob('*')):
            if path.is_file():files[str(path.relative_to(ROOT))]=sha(path.read_bytes())
        for batch in sorted(root.glob('batch-*')):
            path=batch/'records.bin';blob=read_blob(path,files[str(path.relative_to(ROOT))])
            for record in parse_records(blob):
                ram=bytes(record['before']['ram'])
                if len(ram)!=128:raise ValueError('whole canonical source RAM required')
                for physical,frame in enumerate(record['frames']):
                    if frame['scanlines'] not in (262,263):startup+=1;continue
                    raster=normalize_frame(frame)
                    if len(raster)!=33600:raise ValueError('whole original160x210 raster required')
                    name=f'{root.relative_to(ROOT)}/{batch.name}/{record["index"]}/{physical}'
                    cases.append({'id':name,'name':name,'family':family,'ram':ram,'raster':raster,
                                  'ram_sha256':sha(ram),'raster_sha256':sha(raster),'source_scanlines':frame['scanlines']})
    families=validate_domain(cases,startup)
    verify_files(files)
    return {'cases':cases,'families':families,'unmapped_startup':startup,'audits':audits,'files':files,
            'source_receipt_sha256':summary['private_sha256'],'source_sha256':SOURCE_SHA256,
            'scope':'Frozen controlled/input-only original observations; overlapping windows are not a whole-game verdict'}


def verify_files(files):
    if any(sha((ROOT/name).read_bytes())!=expected for name,expected in files.items()):raise ValueError('frozen source artifacts changed')


if __name__=='__main__':
    result=collect();print(json.dumps({key:result[key] for key in ('families','unmapped_startup','source_receipt_sha256')}))
