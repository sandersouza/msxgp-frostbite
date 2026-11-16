# Frostbite delivery workflow

The current accepted product is [1.0.0](release-1.0.0.md). Its source tag and
published assets are immutable. The owner approved native Z80 development and
autonomous issue execution on 2026-10-31; the initial design, backlog and
completed handoffs remain available in the v1.0.0 source tree and Git history.

## Issue work

Track work in [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Preserve unrelated games, project items and shared settings. Use one dedicated
`Frostbite — ISSUE #N` chat, one writer per checkout and a scoped
`codex/<kind>/<N>-<slug>` branch with a focused linked PR.

Read the live issue, current baseline and relevant source contracts before
implementation. For new issues, write a local draft under `.github/issues/`
before publishing. Completed historical drafts need not remain duplicated in
the working tree. Move the issue to `In progress` at implementation, `In review`
while delivery checks remain and `Done` only when its own acceptance conditions
pass and delivery is integrated. Use `Closes #N` only for full resolution.

Create `docs/handoffs/` when an active transfer needs it. Include issue/scope,
dependencies, checkout/branch/commit, pending-file ownership, exact artifact
hashes, verified evidence, limitations and next actions. Superseded handoffs
are recovered from Git rather than retained as current instructions.

## Testable builds and releases

Every new testable MSX ROM version requires a versioned GitHub release;
development diagnostics use prereleases. Run relevant checks first and attach
the exact tested ROM, SHA-256 and source commit. Documentation-only changes
do not create a ROM release. Never replace an existing published binary with
changed bytes under the same version.

Release notes must describe current behavior, checks and limitations, next
work and relevant issues, plus human tests: setup, mapper, controls, exact
actions, expected results and requested evidence. Download published assets
again and verify their byte identity before claiming delivery.

## Evidence and source boundaries

Keep original CPU/state equivalence, synthetic CI, automated emulator routes,
manual play/listening and physical hardware evidence distinct. Original logic
cadence and complete presented-picture cadence require separate measurements.
See [development](development.md) for validation entry points and
[CI boundaries](ci-and-tracking.md) for the public checks.

Original ROMs, full disassemblies, generated assets, licensed OS/BIOS files and
raw research outputs remain local/ignored. Historical Seaquest results never
establish Frostbite correctness. Preserve its verified external snapshot and
local inputs; see [recovery/provenance](baseline-preservation.md).
