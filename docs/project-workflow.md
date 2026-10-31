# Frostbite delivery and project tracking

Work is tracked in [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Only change this repository's items. Preserve shared fields and other games.

The owner approved the design and autonomous issue execution on 2026-10-31.
The [approved design](superpowers/specs/2026-10-31-frostbite-design.md) and
[backlog](superpowers/specs/2026-10-31-frostbite-backlog.md) define scope and
dependencies. Operational work follows the current local issue copy.

## Dedicated forked issue chats

Create or reuse `Frostbite — ISSUE #N` within the Frostbite Codex project before
starting issue N. Use a fork so accepted context travels with it. Verify its
project and workspace. Do not use a Seaquest chat for Frostbite work.

A handoff under docs/handoffs/ carries:
- Issue URL, scope and dependencies.
- Branch, source commit and pending files with their owner.
- Exact ROM/input hashes and reproducible verification evidence.
- Known limitations, pending human checks and the next concrete action.

Only one issue implementation owns a shared checkout. The previous chat stops
editing after transfer. Continue to a dependency-ready successor through another
dedicated fork without asking again for routine permission.

## Issue and PR lifecycle

- Backlog: proposed work; Ready: dependencies and inputs available.
- In progress: the dedicated chat is implementing its issue.
- In review: required checks/review or integration remain pending.
- Done: that issue's DoD is satisfied and its delivery is integrated.

Use `codex/<kind>/<N>-<slug>` branches and focused linked PRs. Obtain independent
review and fix material findings before integration. Use `Closes #N` only when
merging delivers the full issue; otherwise use `Refs #N`.
No issue closes because a ROM merely boots or because another issue passed.

Write local issue bodies under .github/issues/frostbite/ before publication;
keep meaningful changes synchronized. Categories use existing repository labels.
Record intended Task type and priority in the body when native types/priority
labels are unavailable; keep project Priority consistent. Project Size and
numeric Estimate are effort estimates, not deadlines. No milestone is currently
assigned and none will be invented without an established scheme.

## Every testable ROM gets a release

The owner's instruction applies at EVERY new testable ROM version, from useful
diagnostics to full gameplay. Publish a versioned GitHub release with the exact
MSX ROM attached. Use prereleases during development. Do not wait for the final
game before providing downloadable tests.

Each release includes:
1. Version, exact source commit, ROM filename/size, mapper and RAM/VRAM needs,
   and SHA-256 for the attached bytes.
2. Current state: working behavior, checks already run, limitations and known
   defects. Identify diagnostic builds as such.
3. Next steps: planned improvements and linked issues.
4. Human test request: emulator/hardware setup, load instructions and controls,
   precise actions, expected results, requested feedback and evidence to return.

Run appropriate automated checks before publishing and link the release from
its issue/handoff. Changed ROM bytes require a new version; never silently
replace an existing published binary. Documentation-only work has no ROM
release. The latest downloadable test must always identify its real state.

## Evidence and repository boundaries

Keep source-ROM equivalence, synthetic CI, automated emulator replay, manual
visual/listening review and physical MSX acceptance as separate evidence classes.
A successful boot is not complete gameplay. Natural-play and controlled-replay
routes need an explicit completion predicate and bounded failure outcome.

Only publish Frostbite implementation and audited reusable infrastructure.
Local original ROMs, complete disassemblies and original-derived generated
assets remain ignored. Public CI does not fetch those inputs.
Inherited Seaquest evidence is quarantined and cannot satisfy Frostbite checks;
see [preservation/provenance](baseline-preservation.md).

Final removal of obsolete legacy belongs to issue #17 after working replacement
acceptance. No testable Frostbite ROM, fresh-install toolchain or runtime CI has
been validated as of issue #1.
