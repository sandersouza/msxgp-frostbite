# macOS development toolchain and diagnostic checklist

The supported host setup is macOS arm64 or x86_64 with Python >=3.11, Git,
Xcode command-line build tools and Homebrew. **arm64 was exercised; Intel and
Rosetta remain untested.** The clean-clone checks used existing host CLT,
Homebrew, openMSX 21.0 and Stella 7.0, with a new project venv and freshly built
local assemblers. This is a fresh-source test, not a claim of installing a new OS.

## Pins, ownership and prerequisites

[tools-lock.json](../references/tools-lock.json) is the source tool authority:

| Tool | Pin | Build |
|---|---|---|
| sjasmplus | d379eeac9ad3857fb48fd3a3929175d0a56038ce / 1.24.0 | native make, USE_LUA=0 |
| DiStella | 1015ae53b2d222320eb706c220186305fcac55dd | native make auto |
| DASM | cee322098fdf56585247433922dbac4aa93001fe / v2.20.17 | native make build; this tag still prints banner2.20.16 |
| Python reference backend | py65==1.2.0 | requirements-reference.txt |

New assemblers live under `.tools/frostbite/<name>-<commit>/`. Each has a
receipt recording source commit, build command, architecture, version output
and executable SHA-256. Check rejects tracked-source edits, wrong revisions,
changed binaries or incompatible architecture, preserving them for inspection.
It does not reset a repository or overwrite an unverified binary.

The supplied `.tools/sjasmplus`, `.tools/distella`, other legacy tools and
existing `.venv` are preserved. Setup creates a venv only when absent, adds a
missing pinned py65, and refuses an incompatible existing version rather than
upgrading/downgrading it. Package consistency is checked. Tools are native host
binaries; the output cartridge contains Z80 code. There is no MADS/Atari800
requirement and no original ROM dependency for build/test/smoke.

If prerequisites are absent, install Apple's command-line tools with
`xcode-select --install`, follow the official [Homebrew instructions](https://brew.sh/),
and provide Python >=3.11. Setup fails with the missing prerequisite; it does
not install Homebrew or replace the system Python. It installs openMSX/Stella
through Homebrew only if their commands are absent. Cold Homebrew/emulator
installation was not needed on the tested host. Their actual versions are
recorded/guarded by the relevant probes rather than inferred from tool presence.

## Fresh-clone command-by-command checklist

```sh
git clone https://github.com/sandersouza/msxgp-frostbite.git
cd msxgp-frostbite
python3 --version
git --version
cc --version
make --version
brew --version
bash scripts/setup.sh --dry-run
bash scripts/setup.sh
bash scripts/setup.sh --check
make test
make build
make smoke
shasum -a 256 outputs/diagnostic/frostbite-0.0.1-diagnostic.rom
make environment
make environment-check
make build
make smoke
```

Dry-run prints the intended actions without creating tools/venvs. Check is
read-only and performs no installations. The second environment/build pass
must leave verified tool binaries and existing environment packages unchanged,
and produce the same ROM hash. A partial or mismatched managed directory is
preserved with a failure message; inspect it before deliberately repairing or
moving that exact directory. Never clean the whole .tools or .venv tree.

`make test` uses .venv and should report no skips with py65 installed. It needs
no original Atari inputs. Standard python3 can run stdlib utility tests, but
four CPU-specific tests skip if the optional backend is absent; that is a
smaller evidence class. Public runtime CI is delivered by issue #6, not by
these local results.

For an interactive emulator run and an actual rendered preview:

```sh
make run
# Close the interactive emulator before returning to the shell.
.venv/bin/python -B scripts/smoke.py --screenshot
```

The diagnostic is a **16,384-byte Normal/plain 16 KiB** ROM, loaded at 4000 with
an AB header. It uses BIOS SCREEN1/font/input/PSG services, RAM variables at
C000–C00F and a stack below the BIOS work area. It requires no disk, expanded
RAM, turbo or additional sound hardware. Normal/no mapper is explicit in the
emulator command. The final game mapper/layout remains a separate measured
decision; no Seaquest 128 KiB layout is inherited.

The screen displays the diagnostic/version and an advancing heartbeat. Arrow
keys/joystick1 show directions0–8; SPACE/joystick1fire shows0/1 and enables a
steady PSG tone while held. These BIOS input calls are diagnostic tests, not
an implementation of Frostbite's raw opposed-input/phase contracts.

## What smoke proves

Each run creates a new artifact directory and isolated openMSX user-data and
settings files. It copies the installed C-BIOS_MSX1 hardware profile, verifies
64 KiB RAM/TMS9918-family/configured 16 KiB VRAM, resolves the bundled free C-BIOS
firmware with its SHA-1, and loads the copy under a unique machine name.
User firmware caches, machine overrides and saved settings are unnecessary.
No HOME/CODEX_HOME value is replaced and user settings are not saved.

Runtime checks require TMS9918A, a 3,579,545 Hz Z80, a 64 KiB RAM device and only
the expected Normal cartridge extension. They verify enabled SCREEN1,
title/readouts in VRAM, ready signature4642, advancing heartbeat, UP/release,
SPACE/held-edge/release and PSG period/volume-on/off. Structural cartridge
validation and the current build's byte identity precede emulator launch.
A timeout, failed callback, missing result or changed ROM rejects the attempt;
old latest-success summaries are removed. A booting heartbeat-disabled ROM was
rejected as a runtime negative control.

The debugger's VRAM backing buffer is larger than the TMS9918's configured
memory; its debug size is **not** used as hardware capacity. The verified
profile and runtime VDP type establish this diagnostic's 16 KiB configuration.
BIOS WIDTH may center a 29-column logical line; display checks locate the title
margin and check the corresponding status columns.

Headless checks accelerate wall time while retaining the standard virtual
Z80 clock. They are functional evidence, not CPU-budget acceptance. Rendered
capture uses normal speed and no frame skipping; an accelerated capture can
precede an updated visible framebuffer. The actual screenshot was inspected.
PSG register checks are separate from human listening; physical MSX and PAL
results remain pending. See [diagnostic evidence](../references/diagnostic-baseline.json).

## Original reference commands

After providing the owner-supplied canonical ROM locally at
references/roms/frostbite.bin, these optional research commands are available:

```sh
make reference-check
make reference-rebuild
make mechanics-check
.venv/bin/python -B scripts/source_timing.py
```

Canonical validation runs before a backend. Rebuild defaults now select the
verified managed DiStella/DASM tools; explicit overrides remain available.
DiStella has fixed50-byte input/132-byte argv buffers: a verified short local
input plus short backend symlink avoids both limits. Never add its `-r` flag.
Full original-derived files stay under ignored outputs; public CI does not
fetch the ROM. The Stella timing decoder still requires its reviewed7.0
Debugger format. CPU slices do not solve #7's full-emulator alignment/geometry.

## Packaging and release checklist

Commit and integrate the reviewed source first. From a clean checkout of that
exact commit, run:

```sh
make environment-check
make test
make build
.venv/bin/python -B scripts/smoke.py --screenshot
make package
cat outputs/releases/latest-package.json
```

Packaging requires clean build/smoke/source commit identities and matching ROM
hashes, the diagnostic version and successful unexpanded smoke. It stages the
validated byte snapshot in a new directory, with build/smoke metadata,
SHA256SUMS, rendered release notes and an optional screenshot. The package
command does not publish anything. The printed directory is used for GitHub
Release attachments; source commit and SHA placeholders in the note template
are resolved from verified metadata.

Publish a versioned **prerelease** using that exact commit, ROM and notes. Do
not use upload clobber to replace a published binary. Changed ROM bytes require
a new version and new human-test instructions. Download the published assets
again and verify SHA256SUMS plus the ROM hash before marking delivery Done.
Issue #5's PR uses Refs#5 so the issue stays open until the release is verified.

## Reuse and source provenance

Seaquest's environment/Makefile/smoke architecture was inspected as the supplied
reference. The Frostbite setup/diagnostic/checks were rewritten for this target,
with no source-address/gameplay substitutions or original assets copied. The
GPLv3 project LICENSE remains unchanged; the full supplied snapshot/quarantine
stays protected until #17. Host tool sources retain their own licenses:
[sjasmplus BSD](https://github.com/z00m128/sjasmplus/tree/d379eeac9ad3857fb48fd3a3929175d0a56038ce),
[DiStella source/provenance](https://github.com/johnkharvey/distella/tree/1015ae53b2d222320eb706c220186305fcac55dd),
[DASM GPL2+](https://github.com/dasm-assembler/dasm/tree/cee322098fdf56585247433922dbac4aa93001fe).
Compilers/C-BIOS/Atari binaries are not embedded or redistributed in this ROM.
