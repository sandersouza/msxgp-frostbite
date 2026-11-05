"""Read-only M1 jump coverage for proven fixed-clock routes.

A jump has15 vertical updates, not60 unique positions. Phase0F/1F is an
optional observable launch state: the first update may occur in that step.
Only committed snapshots count. Source completion lies within its recorded
IRQ, so wall-clock landing latency is an interval, never a fabricated point.
"""
from pathlib import Path
import argparse,hashlib,json,statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
CAPTURE_BYTES=49304
HZ=3579545
FIELDS={'phase':0x6a,'y':0x64,'x':0x66,'counter':1,'landing_latch':0x76,'attachment':0x72}

def sha(b):return hashlib.sha256(b).hexdigest()
def active(r):return all(r[k]==0 for k in (0x46,0x67,0x71))
def phase(r):return r[0x6a]
def signed(n):return n-256 if n&128 else n

def stats(values):
 if not values:return {'count':0}
 return {'count':len(values),'minimum':min(values),'mean':statistics.mean(values),'median':statistics.median(values),'p95':sorted(values)[int((len(values)-1)*.95)],'maximum':max(values)}

def expected_arc(rom,y,direction):
 indices=range(30,15,-1) if direction=='up' else range(14,-1,-1)
 result=[]
 for index in indices:
  delta=signed(rom[0xcc0+index]);y=(y+delta)&255
  result.append({'update':len(result)+1,'table_index':index,'phase':0 if index in (0,16) else index,'y':y,'delta':delta})
 assert len(result)==15 and sum(x['delta'] for x in result)==(-26 if direction=='up' else 26)
 return result

def find_arcs(points,rom):
 spans=[];i=0
 while i<len(points):
  if not phase(points[i]):i+=1;continue
  start=i
  while i<len(points) and phase(points[i]):i+=1
  landing=i if i<len(points) else None
  first=phase(points[start]);direction='up' if first>=17 else 'down'
  previous=start-1 if start else None
  problems=[]
  if previous is None:problems.append('route_starts_airborne')
  if landing is None:problems.append('route_ends_airborne')
  last=landing if landing is not None else len(points)-1
  inactive=[n for n in range(max(0,start-1),last+1) if not active(points[n])]
  if inactive:problems.append('inactive_or_death_state')
  attached=[n for n in range(start,last) if points[n][0x72]<128]
  if attached:problems.append('hazard_attachment_during_arc')
  launch=31 if direction=='up' else 15
  if first not in (launch,launch-1):problems.append('missing_initial_phase')
  expected=expected_arc(rom,points[previous][0x64],direction) if previous is not None else []
  updates=[];validation=[];last_idx=-1
  if expected:
   index_for_phase={r['phase']:n for n,r in enumerate(expected)}
   for n in range(start,last+1):
    r=points[n];p=phase(r)
    idx=-1 if p==launch else index_for_phase.get(p)
    if idx is None:validation.append({'step':n,'reason':'invalid_phase','phase':p});continue
    y=points[previous][0x64] if idx==-1 else expected[idx]['y']
    if r[0x64]!=y:validation.append({'step':n,'reason':'table_y_mismatch','actual':r[0x64],'expected':y})
    if idx not in (last_idx,last_idx+1):validation.append({'step':n,'reason':'phase_discontinuity','from':last_idx,'to':idx})
    if idx!=last_idx:
     if r[1]&1:validation.append({'step':n,'reason':'vertical_update_on_odd_counter'})
     updates.append({'step':n,**expected[idx]})
    last_idx=idx
   if len(updates)!=15:validation.append({'reason':'vertical_update_count','actual':len(updates),'expected':15})
   if landing is not None and not points[landing][0x76]&128:validation.append({'reason':'missing_landing_latch'})
  if validation:problems.append('M1_sequence_mismatch')
  if previous is None or 'missing_initial_phase' in problems:category='partial_start'
  elif inactive or attached:category='interrupted'
  elif landing is None:category='partial_end'
  elif problems:category='interrupted'
  else:category='complete_normal_active'
  spans.append({'id':len(spans),'category':category,'direction':direction,'preceding_grounded_step':previous,'start_step':start,'landing_step':landing,'last_observed_airborne_step':(landing-1 if landing is not None else last),'launch_phase_observed':first==launch,'source_step_count':last-start+1,'problems':problems,'first_inactive_step':inactive[0] if inactive else None,'attached_steps':attached,'expected_vertical_updates':expected,'observed_vertical_updates':updates,'sequence_validation':validation})
 return spans

def latency(picture,landing,irq_by_step):
 irq=irq_by_step[landing];entry=irq['entry'];exit=irq['exit'];t=picture['time']
 assert t>=exit
 return {'picture':picture['id'],'snapshot_step':picture['snapshot'],'source_steps_after_landing_at_snapshot':picture['snapshot']-landing,'source_steps_after_landing_at_commit':picture['completed_source_before_commit']-landing,'hardware_vblanks_after_landing':picture['vblank']-irq['vblank'],'latency_ms_lower':(t-exit)*1000,'latency_ms_upper':(t-entry)*1000}

def cover_arc(arc,points,pictures,irq_by_step):
 result=dict(arc)
 if arc['category']!='complete_normal_active':return result
 start=arc['start_step'];land=arc['landing_step'];end=land
 while end+1<len(points) and active(points[end+1]) and phase(points[end+1])==0 and points[end+1][0x64]==points[land][0x64]:end+=1
 endpoint_end=land
 while endpoint_end+1<len(points) and active(points[endpoint_end+1]) and points[endpoint_end+1][0x64]==points[land][0x64]:endpoint_end+=1
 sample=lambda a,b:[p for p in pictures if a<=p['snapshot']<=b]
 trajectory=sample(start,land)
 states=[]
 for n,update in enumerate(arc['observed_vertical_updates']):
  first=update['step'];last=arc['observed_vertical_updates'][n+1]['step']-1 if n<14 else end
  seen=sample(first,last)
  states.append({**update,'last_source_step':last,'presented':bool(seen),'pictures':[p['id'] for p in seen],'snapshot_steps':[p['snapshot'] for p in seen]})
 assert len(states)==15
 yruns=[]
 for state in states:
  if yruns and yruns[-1]['y']==state['y']:
   yruns[-1]['last_source_step']=state['last_source_step'];yruns[-1]['updates'].append(state['update']);yruns[-1]['pictures']+=state['pictures']
  else:yruns.append({'y':state['y'],'first_source_step':state['step'],'last_source_step':state['last_source_step'],'updates':[state['update']],'pictures':list(state['pictures'])})
 yset={s['y'] for s in states};seen_y={s['y'] for s in states if s['presented']}
 xy={(r[0x66],r[0x64]) for r in points[start:land+1]};seen_xy={(points[p['snapshot']][0x66],points[p['snapshot']][0x64]) for p in trajectory}
 grounded=sample(land,end);endpoint=sample(land,endpoint_end);post=next((p for p in pictures if p['snapshot']>=land),None)
 result.update(vertical_update_states=states,vertical_update_states_presented=sum(s['presented'] for s in states),vertical_update_states_total=15,distinct_y_total=len(yset),distinct_y_presented=len(seen_y),distinct_y_values=sorted(yset),presented_y_values=sorted(seen_y),consecutive_y_runs=yruns,consecutive_y_runs_total=len(yruns),consecutive_y_runs_presented=sum(bool(s['pictures']) for s in yruns),trajectory_pictures=[{'picture':p['id'],'snapshot_step':p['snapshot'],'phase':phase(points[p['snapshot']]),'x':points[p['snapshot']][0x66],'y':points[p['snapshot']][0x64]} for p in trajectory],unique_xy_total=len(xy),unique_xy_presented=len(seen_xy),grounded_landing_window=[land,end],endpoint_y_window=[land,endpoint_end],grounded_landing_presented=bool(grounded),grounded_landing_latency=latency(grounded[0],land,irq_by_step) if grounded else None,endpoint_y_presented=bool(endpoint),endpoint_y_latency=latency(endpoint[0],land,irq_by_step) if endpoint else None,first_post_landing_snapshot_latency=latency(post,land,irq_by_step) if post else None)
 return result

def measure(folder,rom):
 names=('check.json','route-cpu.bin','pictures.tsv','irq.tsv','captures.bin')
 data={n:(folder/n).read_bytes() for n in names};check=json.loads(data['check.json'])
 assert check['complete'] and check['source_cpu_all_ram_equal'] and check['coherent_picture_pixels_equal']
 for name in names:
  if name=='check.json':continue
  assert name in check['artifacts'] and sha(data[name])==check['artifacts'][name], f'evidence differs from completed check receipt: {name}'
 raw=data['route-cpu.bin'];assert len(raw)%133==0
 points=[raw[i+5:i+133] for i in range(0,len(raw),133)]
 rows=[l.split() for l in data['pictures.tsv'].decode().splitlines()]
 pictures=[dict(id=int(r[0]),snapshot=int(r[1]),completed_source_before_commit=int(r[2]),time=float(r[3]),vblank=int(r[4])) for r in rows]
 assert all(len(r)==8 for r in rows) and len(data['captures.bin'])==len(rows)*CAPTURE_BYTES
 for i,p in enumerate(pictures):
  assert p['id']==i and p['snapshot']<=p['completed_source_before_commit']<len(points)
  assert data['captures.bin'][i*CAPTURE_BYTES:i*CAPTURE_BYTES+128]==points[p['snapshot']]
  if i:assert p['snapshot']>pictures[i-1]['snapshot'] and p['time']>pictures[i-1]['time']
 irq_by_step={};cumulative=0
 for r in (l.split() for l in data['irq.tsv'].decode().splitlines()):
  assert len(r)==7 and int(r[4]) in (1,2) and int(r[6])==0
  for _ in range(int(r[4])):
   cumulative+=1;irq_by_step[cumulative]={'vblank':int(r[1]),'entry':float(r[2]),'exit':float(r[2])+int(r[3])/HZ}
 assert cumulative==len(points)-1
 arcs=[cover_arc(a,points,pictures,irq_by_step) for a in find_arcs(points,rom)]
 complete=[a for a in arcs if a['category']=='complete_normal_active'];summary={'complete_normal_active_jumps':len(complete),'other_arcs':{k:sum(a['category']==k for a in arcs) for k in ('interrupted','partial_start','partial_end')}}
 for field in ('vertical_update_states','distinct_y','consecutive_y_runs','unique_xy'):
  seen=sum(a[field+'_presented'] for a in complete);total=sum(a[field+'_total'] for a in complete)
  summary[field]={'presented':seen,'total':total,'fraction':seen/total if total else None,'per_jump_presented':stats([a[field+'_presented'] for a in complete])}
 for field in ('grounded_landing','endpoint_y'):
  values=[a[field+'_latency'] for a in complete if a[field+'_latency']]
  summary[field]={'presented_jumps':len(values),'missed_jumps':len(complete)-len(values),'source_steps_after_landing_at_commit':stats([v['source_steps_after_landing_at_commit'] for v in values]),'latency_ms_lower':stats([v['latency_ms_lower'] for v in values]),'latency_ms_upper':stats([v['latency_ms_upper'] for v in values])}
 summary['first_post_landing_snapshot_source_steps_at_commit']=stats([a['first_post_landing_snapshot_latency']['source_steps_after_landing_at_commit'] for a in complete if a['first_post_landing_snapshot_latency']])
 for n,b in data.items():assert (folder/n).read_bytes()==b,'evidence changed during measurement'
 return {'folder':str(folder),'rom_sha256':check['rom_sha256'],'family':check['family'],'active_pictures_per_second':check['active_pictures_per_second'],'summary':summary,'arcs':arcs,'source_ram_sha256':sha(b''.join(points)),'evidence':{n:sha(b) for n,b in data.items()}},points

def selftest(rom):
 tested=[]
 for direction in ('down','up'):
  for immediate in (False,True):
   r=bytearray(128);r[0x64]=79;r[0x72]=255;r[1]=0 if not immediate else 1;points=[bytes(r)]
   launch=15 if direction=='down' else 31
   if not immediate:r[1]+=1;r[0x6a]=launch;points.append(bytes(r))
   for update in expected_arc(rom,79,direction):
    r[1]=(r[1]+1)&255;r[0x6a]=update['phase'];r[0x64]=update['y'];r[0x76]=255 if not update['phase'] else 0;points.append(bytes(r))
    if update['phase']:r[1]=(r[1]+1)&255;points.append(bytes(r))
   arcs=find_arcs(points,rom);assert len(arcs)==1 and arcs[0]['category']=='complete_normal_active',arcs
   assert len(arcs[0]['observed_vertical_updates'])==15 and arcs[0]['launch_phase_observed']!=immediate
   assert len({u['y'] for u in arcs[0]['observed_vertical_updates']})<15
   cut=find_arcs(points[:-4],rom);assert cut[0]['category']=='partial_end'
   cut=find_arcs(points[5:],rom);assert cut[0]['category']=='partial_start'
   interrupted=list(points);bad=bytearray(interrupted[7]);bad[0x67]=1;interrupted[7]=bytes(bad);assert find_arcs(interrupted,rom)[0]['category']=='interrupted'
   arc=arcs[0]
   clock={n:{'vblank':n,'entry':n/60,'exit':n/60+.001} for n in range(1,len(points)+2)}
   def picture(n):return {'id':n,'snapshot':n,'completed_source_before_commit':n+2,'time':(n+3)/60,'vblank':n+3}
   full=cover_arc(arc,points,[picture(u['step']) for u in arc['observed_vertical_updates']],clock)
   assert full['vertical_update_states_presented']==15 and full['distinct_y_presented']==9 and full['consecutive_y_runs_presented']==11
   plateau=next(u for n,u in enumerate(arc['observed_vertical_updates'][:-1]) if u['y']==arc['observed_vertical_updates'][n+1]['y'])
   sparse=cover_arc(arc,points,[picture(plateau['step'])],clock)
   assert sparse['vertical_update_states_presented']==sparse['distinct_y_presented']==sparse['consecutive_y_runs_presented']==1
   assert not sparse['grounded_landing_presented']
   tail=bytearray(points[-1]);tail[0x6a]=15;tail[1]=(tail[1]+1)&255
   endpoint=cover_arc(arc,points+[bytes(tail)],[picture(len(points))],clock)
   assert not endpoint['grounded_landing_presented'] and endpoint['endpoint_y_presented']
   tested.append({'direction':direction,'first_update_in_launch_step':immediate,'phase_sequence':[u['phase'] for u in arcs[0]['observed_vertical_updates']],'y_sequence':[u['y'] for u in arcs[0]['observed_vertical_updates']]})
 return tested

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('folders',nargs='+',type=Path);args=ap.parse_args();assert not args.out.exists()
 rom=(ROOT/'references/roms/frostbite.bin').read_bytes();assert sha(rom)=='cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834';validation=selftest(rom);results=[];control=None
 for folder in args.folders:
  result,points=measure(folder.resolve(),rom)
  if control is None:control=points
  else:assert points==control,'comparison source RAM routes differ'
  results.append(result)
 result={'complete':True,'method':'M1 exact original-ROM FCC0 trajectory table;15 vertical updates per complete normal active jump. Optional launch state excluded from update denominator. Snapshot coverage means actually committed coherent pictures. Landing milliseconds are bounds from IRQ entry/exit, not precise source-return timestamps. Grounded landing and endpoint-Y representation are distinct. Interrupted/partial arcs excluded from aggregate coverage. Y-only coverage can merge multiple phases and repeated visits; consecutive-Y-run coverage preserves visits.','validation':validation,'source_sha256':sha(rom),'script_sha256':sha(Path(__file__).read_bytes()),'contract_sha256':sha((ROOT/'docs/gameplay-contracts.md').read_bytes()),'same_source_ram_route':True,'results':results}
 args.out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps([{k:v for k,v in r.items() if k in ('folder','active_pictures_per_second','summary')} for r in results],indent=2))

if __name__=='__main__':main()
