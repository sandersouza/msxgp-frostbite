# Local Stella electrical observer

`stella-floe.patch` applies only to
[Stella](https://github.com/stella-emu/stella) commit
`d55b1aec0d067a4c901a6dcdf81cb8f579685659` (7.0).
Original Stella files retain their upstream copyright and GPL-2.0 license;
see upstream `License.txt`. This third-party observation patch does not change
the license of unrelated Frostbite sources. No emulator binary/full checkout
is distributed here or linked into the MSX cartridge.

Use `.venv/bin/python -B scripts/stella_floe.py build` on the prepared macOS
host. The helper clones a private ignored checkout, checks the exact revision
and patch, configures a debugger build with existing SDL2/compiler dependencies,
and records build commands plus patch/binary hashes. It never resets unrelated
edits or installs system packages. `--directory` selects another fresh ignored
checkout, or the exact already patched checkout.

The patch adds a bounded `floeProbe` debugger command and parallel literal-view
collision sidecars at real TIA counters. It never modifies original ROM bytes,
CPU execution, actual collision latches or event ordering. Line caching is
disabled only while observing; independent unmodified-Stella comparisons check
full CPU/RAM semantics. Input/output files, snapshots, original-derived tables,
logs and compiled tools remain under ignored `outputs/floes/`.

See [floe-loop.md](../docs/floe-loop.md) for the strict record protocol, complete
domain, validations, source replay journal and limitations.
