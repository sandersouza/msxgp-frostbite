"""Explicit source interaction predicates and input-only route acquisition.

Predicates certify their named event sequence; complete source continuity and
native equality have separate mandatory gates. Original states remain private.
"""
from reference_routes import assess_refuge


def validate_policy(policy):
    if (policy.get('ram_injections')!={} or policy.get('source_hazards_disabled') is not False
            or policy.get('instruction_skipping') is not False or policy.get('raw_input_every_interval') is not True):
        raise ValueError('continuous input-only source policy with enabled hazards required')


def score(ram):
    result=0
    for value in ram[0x48:0x4B]:
        high,low=divmod(value,16)
        if high>9 or low>9:raise ValueError('complete valid source BCD score required')
        result=result*100+high*10+low
    return result


def reserves(ram):return ram[0x4C]+ram[0x52]


def recovery(rows,death,initial):
    for i in range(death+1,len(rows)):
        r=rows[i]
        if (reserves(r)==reserves(initial)-1 and r[0x64]==27 and r[0x65]==69 and r[0x66]==64
                and r[0x6A]==0 and r[0x71]==0 and r[0x67]==0 and r[0x46]==0):return i
    raise ValueError('observed loss and initialized active recovery required')


def assess(points,route_kind,active_start=0,approach_end=None):
    if (len(points)<2 or not 0<=active_start<len(points) or any(len(p.get('ram',[]))!=128 for p in points)
            or [p.get('index') for p in points]!=list(range(len(points)))):
        raise ValueError('complete continuous indexed source RAM checkpoints required')
    rows=[p['ram'] for p in points]
    if any(r[0x45]&128 or r[0x46]&128 for r in rows[active_start:]):raise ValueError('route entered terminal/attract before acceptance')
    initial=rows[active_start]
    if route_kind=='bear-refuge':
        end=approach_end if approach_end is not None else active_start+288
        result=assess_refuge(points[active_start:end],points[end:])
        return {'kind':route_kind,**result,'approach_end':end,'observed_steps':len(points)-active_start}
    if route_kind=='bear-chase':
        contact=next((i for i in range(active_start,len(rows)) if rows[i][0x6D]&128 and rows[i][0x4B]>=3
                      and rows[i][0x64]==27 and rows[i][0x6A]==0 and rows[i][0x71]==0),None)
        if contact is None:raise ValueError('actual grounded shore contact required')
        push=next((i for i in range(contact+1,len(rows)) if rows[i][0x6D]&128 and rows[i][0x71]==0
                   and rows[i][0x66]<rows[i-1][0x66]),None)
        if push is None:raise ValueError('effective bear chase movement required')
        death=next((i for i in range(push+1,len(rows)) if rows[i][0x71]&128),None)
        if death is None:raise ValueError('bear chase death transition required')
        end=recovery(rows,death,initial)
        return {'kind':route_kind,'contact_step':contact,'push_step':push,'death_step':death,'recovery_step':end,
                'initial_reserves_total':reserves(initial),'final_reserves_total':reserves(rows[end]),
                'player_changed':rows[end][0x47]!=initial[0x47]}
    if route_kind=='fish-envelope':
        collection=next((i for i in range(max(1,active_start),len(rows)) if rows[i][0x77]==rows[i-1][0x77]+1),None)
        if collection is None:raise ValueError('observed fish collection required')
        before,r=rows[collection-1],rows[collection]
        removed=[row for row in range(4) if before[0x5C+row]!=r[0x5C+row]]
        if (len(removed)!=1 or r[0x74]!=91 or r[0x67]!=16 or r[0x6A]!=0
                or before[0x11+removed[0]]&3!=1):raise ValueError('source fish segment/envelope entry required')
        row=removed[0];old,new=before[0x5C+row],r[0x5C+row]
        if new&~old or (old^new).bit_count()!=1:raise ValueError('exactly one real fish segment must be removed')
        previous=r;awards=0;end=None
        for i in range(collection+1,len(rows)):
            r=rows[i];expected=previous[0x74]-1
            if expected&31==0:expected=0
            delta=(score(r)-score(previous))%1000000;award=10 if expected&3 else 0
            if r[0x74]!=expected or delta!=award:raise ValueError('fish delayed reward/envelope ordering differs')
            awards+=int(bool(award));previous=r
            if expected==0:end=i;break
        if end is None or awards!=20 or (score(rows[end])-score(rows[collection]))%1000000!=200:
            raise ValueError('complete twenty-award fish envelope required')
        return {'kind':route_kind,'collection_step':collection,'reward_end_step':end,'fish_row':row,'awards':awards,'reward_points':200}
    if route_kind=='threat-push':
        attach=next((i for i in range(max(1,active_start),len(rows)) if rows[i][0x72]<4 and rows[i-1][0x72]>=128),None)
        if attach is None:raise ValueError('observed source threat attachment required')
        row=rows[attach][0x72];r=rows[attach]
        if not r[0x31+row*2]&128 or r[0x11+row]&3==1 or r[0x6A]!=0:raise ValueError('real grounded odd threat contact required')
        push=next((i for i in range(attach+1,len(rows)) if rows[i][0x72]==row and rows[i][0x71]==0
                   and rows[i][0x66]!=rows[i-1][0x66]),None)
        if push is None:raise ValueError('observed attached-row movement required')
        death=next((i for i in range(push+1,len(rows)) if rows[i][0x71]&128),None)
        if death is not None:end=recovery(rows,death,initial);exit_kind='death/recovery'
        else:
            end=next((i for i in range(push+1,len(rows)) if rows[i][0x72]>=128 and rows[i][0x71]==0 and rows[i][0x6A]==0),None);exit_kind='released'
            if end is None:raise ValueError('explicit threat release or death/recovery required')
        return {'kind':route_kind,'attachment_step':attach,'row':row,'push_step':push,'completion_step':end,'exit':exit_kind}
    if route_kind in ('water-death','temperature-death'):
        water=route_kind=='water-death'
        death=next((i for i in range(active_start,len(rows)) if (rows[i][0x71]&128 and rows[i][0x64]>=145 if water
                   else rows[i][0x71]&16 and rows[i][0x65]==0)),None)
        if death is None:raise ValueError('distinct source water/temperature death entry required')
        end=recovery(rows,death,initial)
        return {'kind':route_kind,'death_step':death,'recovery_step':end,'entry_flag':128 if water else 16}
    raise ValueError('known explicit hazard interaction predicate required')
