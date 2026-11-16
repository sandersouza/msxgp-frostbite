# Build tools

Required: Python >=3.11 (standard library only), Git, Make, a C/C++ compiler and
`file`. macOS Command Line Tools provide the compiler and Make. Linux systems
can use their normal compiler/build packages. A Python virtual environment is
optional; no pip installation is required.

```sh
git clone https://github.com/sandersouza/msxgp-frostbite.git
cd msxgp-frostbite
make build
make verify
```

The [tool lock](../references/tools-lock.json) pins sjasmplus. The first build
fetches that source revision and compiles it with Lua disabled. Its source,
binary and verification receipt remain under `.tools/frostbite/`. Internet is
required for this initial toolchain provisioning. Existing modified tool
checkouts are preserved and reported rather than reset automatically.

ZX0 revision `ecde3a2ae05061fe06469ed46df81a33b7de7d86` is vendored under
`src/third_party/zx0/compressor/`, including its BSD license. Make compiles it
into `.tools/zx0`. No Seaquest checkout or external compressor is required.

`make environment` prepares the tools without building the game.
`make environment-check` validates the assembler receipt.
Override `PYTHON` or `CC` when needed. All product build inputs are versioned;
no original ROM, BIOS, DOS disk, emulator or private cache is a compilation input.

Playing with `make run` requires openMSX and its C-BIOS MSX1 profile. Actual
DOS/BASIC loading checks additionally require locally supplied licensed DOS
and machine firmware; see [native formats](native-formats.md).
