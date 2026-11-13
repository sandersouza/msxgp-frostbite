"""Measure visible movement gaps on a proven original-input route."""
import sys,json,statistics,hashlib
from pathlib import Path

def active(r):return all(r[k]==0 for k in (0x46,0x67,0x71))
def stats(v):return dict(count=len(v),mean=statistics.mean(v),median=statistics.median(v),p95=sorted(v)[int((len(v)-1)*.95)],maximum=max(v)) if v else None
def measure(folder):
 receipt=json.loads((folder/'check.json').read_text())
 for name in ('route-cpu.bin','pictures.tsv'):
  assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==receipt['artifacts'][name],name
 raw=(folder/'route-cpu.bin').read_bytes();assert len(raw)%133==0
 points=[raw[i+5:i+133] for i in range(0,len(raw),133)]
 rows=[line.split() for line in (folder/'pictures.tsv').read_text().splitlines()];samples={int(row[1]) for row in rows}
 assert all(len(r)==8 and int(r[1])<=int(r[2])<len(points) for r in rows)
 intervals=[];steps=[];vblanks=[]
 for a,b in zip(rows,rows[1:]):
  first,last=int(a[1]),int(b[1]);assert first<last
  if all(active(r) for r in points[first:last+1]):
   intervals.append((float(b[3])-float(a[3]))*1000);steps.append(last-first);vblanks.append(int(b[4])-int(a[4]))
 runs=[];start=None;key=None
 for i,r in enumerate(points+[bytes([255]*128)]):
  new=(r[0x6e],r[0x6b],r[0x70],r[0x6c]&8) if active(r) else None
  if new!=key:
   if key is not None:runs.append(dict(first=start,last=i-1,steps=i-start,pose=key,sampled_steps=sorted(samples.intersection(range(start,i)))))
   start=i if new is not None else None;key=new
 missed=[r for r in runs if not r['sampled_steps']]
 check=json.loads((folder/'check.json').read_text());assert check['source_cpu_all_ram_equal'] and check['coherent_picture_pixels_equal']
 return dict(rom_sha256=check['rom_sha256'],family=check['family'],active_pictures_per_second=check['active_pictures_per_second'],active_gaps_ms=stats(intervals),source_steps_between_active_pictures=stats(steps),vblank_gap_histogram={str(n):vblanks.count(n) for n in sorted(set(vblanks))},active_pose_runs=len(runs),fully_unpresented_pose_runs=len(missed),unpresented_duration_steps={str(n):sum(r['steps']==n for r in missed) for n in sorted(set(r['steps'] for r in missed))},runs=runs,evidence={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ['check.json','route-cpu.bin','pictures.tsv']})
if __name__=='__main__':
 folder=Path(sys.argv[1]).resolve();r=measure(folder);out=Path(sys.argv[2]);assert not out.exists();out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['runs','evidence']},indent=2))
