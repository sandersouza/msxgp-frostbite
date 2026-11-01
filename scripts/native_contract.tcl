set save_settings_on_exit false
set renderer none
set throttle off
set speed 999
set power true
set cases [open $native_dir/cases.bin rb]
set actual [open $native_dir/actual.bin wb]
fconfigure $actual -translation binary
set count 0
set stop_bp -1
set trace_file [open $native_dir/profile.bin wb]
fconfigure $trace_file -translation binary
set last_source -1
set last_time 0
proc trace_source {source} {
    set now [machine_info time]
    if {$::last_source!=-1} {puts -nonewline $::trace_file [binary format ii $::last_source [expr {round(($now-$::last_time)*3579545)}]]}
    set ::last_source $source
    set ::last_time $now
}
proc fail_native {detail} {puts stderr "NATIVE_FAIL $detail";exit 1}
proc dispatch_native {} {
    set header [read $::cases 13]
    if {[string length $header]==0} {
        close $::actual
        close $::trace_file
        set heap_ok [expr {[debug read_block memory 0xD000 0x2300] eq [string repeat [binary format c 165] 0x2300]}]
        set heap_json [expr {$heap_ok ? "true" : "false"}]
        set stack_min 0xF380
        binary scan [debug read_block memory 0xF300 128] cu* stack
        for {set index 0} {$index<128} {incr index} {
            if {[lindex $stack $index]!=165} {set stack_min [expr {0xF300+$index}];break}
        }
        set f [open $::native_dir/complete.json w]
        puts $f "\{\"cases\":$::count,\"complete\":true,\"stack_min\":$stack_min,\"heap_guard\":$heap_json,\"clock_hz\":[machine_info z80_freq],\"ram_bytes\":[debug size {Main RAM}]\}"
        close $f
        exit
        return
    }
    if {[string length $header]!=13} {fail_native "truncated count=$::count bytes=[string length $header] position=[tell $::cases]"}
    binary scan $header cu* h
    set entry [expr {[lindex $h 0]+256*[lindex $h 1]}]
    set stop [expr {[lindex $h 2]+256*[lindex $h 3]}]
    set keep [lindex $h 12]
    if {$keep} {
        debug write_block memory 0xC6F0 [binary format ssc $::last_af $::last_bc $::last_carry]
        debug write memory 0xC602 $::last_sp
    } else {
        debug write_block memory 0xC6F0 [string range $header 4 8]
        debug write memory 0xC601 [lindex $h 9]
        debug write memory 0xC600 [lindex $h 10]
        debug write memory 0xC602 [lindex $h 11]
    }
    debug write_block memory 0xC6FE [string range $header 0 1]
    set ram [read $::cases 128]
    if {$keep} {
        debug write_block memory 0xC030 [string range $ram 48 57]
        debug write memory 0xC06D [scan [string index $ram 109] %c]
    } else {debug write_block memory 0xC000 $ram}
    debug write_block memory 0xC300 [read $::cases 16]
    debug write_block memory 0xC340 [read $::cases 8]
    debug write_block memory 0xC700 [string repeat [binary format c 0] 96]
    debug write memory 0xC6FD 0
    if {$::stop_bp!=-1} {debug remove_bp $::stop_bp}
    set ::stop_bp [debug set_bp $stop {} {debug break;after break capture_native}]
    set ::started [machine_info time]
    reg PC $::rpc_start
    debug cont
}
proc capture_native {} {
    if {$::last_source!=-1} {trace_source -1}
    set af [reg AF]
    set bc [reg BC]
    set carry [expr {[reg DE]&1}]
    set ::last_af $af
    set ::last_bc $bc
    set ::last_carry $carry
    set ::last_sp [expr {([reg IX]&127)|[debug read memory 0xC60B]}]
    set p [expr {($af&128)|(($af&64)>>5)|$carry|[debug read memory 0xC600]|[debug read memory 0xC601]}]
    set row [binary format cu* [list [expr {$af>>8}] [expr {$bc>>8}] [expr {$bc&255}] $p [expr {([reg IX]&127)|[debug read memory 0xC60B]}]]]
    append row [debug read_block memory 0xC000 128]
    append row [debug read_block memory 0xC700 96]
    append row [binary format i [expr {round(([machine_info time]-$::started)*3579545)}]]
    puts -nonewline $::actual $row
    incr ::count
    dispatch_native
}
after time 5 {
    if {[debug read memory 0xC6FC]!=83} {fail_native "not-booted pc=[reg PC] marker=[debug read memory 0xC6FC] first=[debug read memory 0x4000]"}
    debug break
    debug write_block memory 0xD000 [string repeat [binary format c 165] 0x2300]
    debug write_block memory 0xF300 [string repeat [binary format c 165] 128]
    foreach pc [array names source_labels] {
        debug set_bp $pc {} [list trace_source $source_labels($pc)]
    }
    after break dispatch_native
}
after time 600 {fail_native watchdog}
