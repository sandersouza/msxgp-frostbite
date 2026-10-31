# Fresh isolated profile; every callback failure emits explicit failed evidence.
set save_settings_on_exit false
if {$::env(FROSTBITE_CAPTURE) eq "1"} {
    set renderer SDLGL-PP
    set maxframeskip 0
    set throttle on
    set speed 100
} else {
    set renderer none
    set throttle off
    set speed 999
}
set power true

proc fail {message} {
    puts stderr "FROSTBITE_SMOKE_FAIL $message"
    set file [open $::env(FROSTBITE_SMOKE_RESULT) w]
    puts $file {{"passed":false}}
    close $file
    exit
}
proc guard {script} {
    if {[catch {uplevel #0 $script} message]} {fail $message}
}
proc require {condition message} {
    if {![uplevel 1 [list expr $condition]]} {error $message}
}
proc check_cell {row column expected} {
    set address [expr {0x1800+$row*32+$column}]
    require {[debug read VRAM $address]==$expected} "wrong display cell $row,$column"
}

after time 5 {guard {
    require {[machine_info config_name] eq "Frostbite_Diagnostic"} "unexpected profile"
    require {[dict get [machine_info device VDP] version] eq "TMS9918A"} "unexpected VDP"
    require {[debug size {Main RAM}]==65536} "RAM not64KiB"
    require {[machine_info z80_freq]==3579545} "nonstandard Z80 clock"
    set extensions [machine_info extension]
    require {[llength $extensions]==1 && [file normalize [lindex $extensions 0]] eq [file normalize $::env(FROSTBITE_SMOKE_ROM)]} "unexpected hardware extension"
    require {[debug read memory 0xC000]==70 && [debug read memory 0xC001]==66} "diagnostic not ready"
    require {[debug read {VDP regs} 2]==6} "unexpected name-table base"
    require {([debug read {VDP regs} 1]&0x58)==0x40 && ([debug read {VDP regs} 0]&2)==0} "SCREEN1 display not enabled"
    set title "FROSTBITE MSX1"
    # BIOS WIDTH may center a 29-column logical line within the 32-cell table.
    set ::text_margin -1
    for {set offset 0} {$offset<=32-[string length $title]} {incr offset} {
        set matched true
        for {set i 0} {$i<[string length $title]} {incr i} {
            scan [string index $title $i] %c code
            if {[debug read VRAM [expr {0x1800+$offset+$i}]]!=$code} {set matched false; break}
        }
        if {$matched} {set ::text_margin $offset; break}
    }
    require {$::text_margin>=0} "diagnostic title not on first row"
    set ::first_tick [debug read memory 0xC002]
    after time 0.2 {guard {
        require {[debug read memory 0xC002]!=$::first_tick} "heartbeat stopped"
        keymatrixdown 8 32
        after time 0.2 {guard {
            require {[debug read memory 0xC004]==1} "UP not observed"
            check_cell 8 [expr {$::text_margin+17}] 49
            keymatrixup 8 32
            keymatrixdown 8 1
            after time 0.2 {guard {
                require {[debug read memory 0xC004]==0} "direction release failed"
                require {[debug read memory 0xC005]==1} "SPACE not observed"
                require {[debug read {PSG regs} 8]==8} "tone volume not enabled"
                require {[debug read {PSG regs} 0]==0 && [debug read {PSG regs} 1]==1} "tone period changed"
                check_cell 9 [expr {$::text_margin+17}] 49
                set ::presses [debug read memory 0xC007]
                require {$::presses==1} "unexpected press edge count"
                after time 0.2 {guard {
                    require {[debug read memory 0xC007]==$::presses} "held fire repeated edge"
                    keymatrixup 8 1
                    after time 0.2 {guard {
                        require {[debug read memory 0xC005]==0} "SPACE release failed"
                        require {[debug read {PSG regs} 8]==0} "tone not muted"
                        check_cell 8 [expr {$::text_margin+17}] 48
                        check_cell 9 [expr {$::text_margin+17}] 48
                        if {$::env(FROSTBITE_CAPTURE) eq "1"} {screenshot -raw $::env(FROSTBITE_SCREENSHOT)}
                        set file [open $::env(FROSTBITE_SMOKE_RESULT) w]
                        puts $file {{"passed":true,"signature":"4642","heartbeat":"advancing","video":"SCREEN1/title/readouts","keyboard":"up/neutral/space/release/held-edge","psg":"period/volume-on/off","ram_bytes":65536,"configured_vram_kib":16,"vdp":"TMS9918A","z80_hz":3579545,"extra_extensions":0}}
                        close $file
                        puts stderr "FROSTBITE_SMOKE_PASS diagnostic only"
                        exit
                    }}
                }}
            }}
        }}
    }}
}}
