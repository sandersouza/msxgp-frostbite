# Emulated matrix only; never sends host keyboard events.
proc start_controls {} {
    set ::control_x [debug read memory 0xC118]
    keymatrixdown 8 128
    after time 0.16 {checked {
        set right [debug read memory 0xC118]
        require {$right>$::control_x && $right<=159} "RIGHT not consumed"
        lappend ::control_checks right
        keymatrixup 8 128
        set ::control_x $right
        keymatrixdown 8 16
        after time 0.16 {checked {
            require {[debug read memory 0xC118]<$::control_x} "LEFT not consumed"
            lappend ::control_checks left
            keymatrixup 8 16
            set ::control_layout [debug read memory 0xC11F]
            set ::control_width [debug read memory 0xC11E]
            keymatrixdown 8 1
            after time 0.14 {checked {
                require {[debug read memory 0xC11F]==($::control_layout^1)} "SPACE layout edge missing"
                require {[debug read memory 0xC11E]==($::control_width^1)} "SPACE width edge missing"
                lappend ::control_checks space-edge
                after time 0.14 {checked {
                    require {[debug read memory 0xC11F]==($::control_layout^1)} "held SPACE repeated"
                    lappend ::control_checks space-held
                    keymatrixup 8 1
                    after time 0.08 {checked {
                        keymatrixdown 8 1
                        after time 0.14 {checked {
                            require {[debug read memory 0xC11F]==$::control_layout} "SPACE re-press missing"
                            require {[debug read memory 0xC11E]==$::control_width} "SPACE re-press width missing"
                            lappend ::control_checks space-repress
                            keymatrixup 8 1
                            set ::count 1
                            finish
                        }}
                    }}
                }}
            }}
        }}
    }}
}
