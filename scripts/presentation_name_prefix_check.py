"""Validate complete dirty input before exact private terminal NAME-list trimming."""
import argparse,json,subprocess
from pathlib import Path
import presentation_matrix_check as matrix
from presentation_border_closure_check import check as parent_check
from presentation_dirty_audit import audit_list as complete_list
from presentation_name_prefix import start
from render_build import symbols

def check(build,out,mode,steps=2252):
    build,out=Path(build).resolve(),Path(out).resolve();m=json.loads((build/'build.json').read_text())
    if not m.get('name_prefix'):return parent_check(build,out,mode,steps)
    s=symbols(build/'presentation.sym');old_run=subprocess.run;old_audit=matrix.audit_list;entries=[];index=0;audits=0
    def run(args,*a,**kw):
        nonlocal entries
        script=None
        if isinstance(args,list)and'-script'in args and'openmsx'in Path(args[0]).name.lower():
            script=Path(args[args.index('-script')+1]);text=script.read_text()
            text+=f'''
set prefix_evidence [open {{{out/'prefix-before.bin'}}} wb]
debug set_bp {s['ac_names']} {{![debug read memory {s['t_in_irq']}]}} {{
 set prefix_flags [debug read_block memory {s['p_fd_rows']} 3]
 binary scan $prefix_flags cu* prefix_fv
 set prefix_wanted {{}}
 for {{set prefix_row 0}} {{$prefix_row<24}} {{incr prefix_row}} {{if {{[lindex $prefix_fv [expr {{$prefix_row/8}}]]&(1<<($prefix_row%8))}} {{lappend prefix_wanted $prefix_row}}}}
 set prefix_n [debug read memory {s['p_fd_count']}]
 set prefix_raw [debug read_block memory {s['p_fd_list']} 24]
 if {{$prefix_n!=[llength $prefix_wanted] || [string range $prefix_raw 0 [expr {{$prefix_n-1}}]] ne [binary format c* $prefix_wanted]}} {{puts stderr "PREFIX_FAIL complete-before-list";exit 1}}
 set prefix_lower [expr {{[debug read memory {s['hy_lo']}]|([debug read memory {s['hy_lo']+1}]<<8)}}]
 if {{$prefix_lower==14 && ([lindex $prefix_fv 0]&7)==7 && [lindex $prefix_fv 0]!=255}} {{
  set prefix_page [debug read memory {s['PAGE']}]
  set prefix_cpu [expr {{$prefix_page ? 0xCD00 : 0xC800}}];set prefix_vram [expr {{$prefix_page ? 0x1C00 : 0x1800}}]
  if {{[debug read_block memory $prefix_cpu 96] ne [debug read_block VRAM $prefix_vram 96]}} {{puts stderr "PREFIX_FAIL changed-header-name";exit 1}}
 }}
 puts -nonewline $::prefix_evidence "$prefix_flags[debug read_block memory {s['hy_lo']} 2][binary format c $prefix_n]$prefix_raw";flush $::prefix_evidence
}}
'''
            script.write_text(text)
        result=old_run(args,*a,**kw)
        if script is not None and(out/'prefix-before.bin').exists():
            raw=(out/'prefix-before.bin').read_bytes()
            if len(raw)%30:raise ValueError('partial pre-publication list record')
            entries=[raw[i:i+30]for i in range(0,len(raw),30)]
        return result
    def terminal(raw,flags):
        nonlocal index,audits
        scenes=(out/'scenes.bin').stat().st_size//95
        if len(entries)!=scenes+1:raise ValueError('one boot and every matrix pre-publication record required')
        before=entries[index+1];index+=1
        if before[:3]!=flags:raise ValueError('pre-publication dirty flags changed')
        complete_list(before[5:],flags)
        skip=start(int.from_bytes(flags,'little'),int.from_bytes(before[3:5],'little'))
        wanted=before[6:6+before[5]][skip:]
        if raw[0]!=len(wanted)or raw[1:1+raw[0]]!=wanted:raise ValueError('terminal list is not the exact validated suffix')
        audits+=1
    subprocess.run=run;matrix.audit_list=terminal
    try:result=parent_check(build,out,mode,steps)
    finally:subprocess.run=old_run;matrix.audit_list=old_audit
    if not entries and mode!='boundary-negative':raise ValueError('pre-publication list guard was not exercised')
    (out/'name-prefix-contract.json').write_text(json.dumps(dict(complete=bool(result['complete']),rom_sha256=m['rom']['sha256'],mode=mode,complete_prepublication_records=len(entries),exact_terminal_suffix_audits=audits,unchanged_header_name_guard=True,public_uploader_unchanged=True,dirty_flags_and_source_owner_active_guards_retained=True),indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('build',type=Path);p.add_argument('out',type=Path);p.add_argument('mode');p.add_argument('steps',type=int,nargs='?',default=2252);a=p.parse_args();check(a.build,a.out,a.mode,a.steps)
