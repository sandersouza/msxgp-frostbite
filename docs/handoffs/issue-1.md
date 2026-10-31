# Issue #1 handoff — preserved baseline and Frostbite workflow

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/1
Implementation branch: `codex/chore/1-frostbite-workflow`.
Planning integration: `468bfa53ac77e99af10aa0fa22130c230d019698` (PR #18).
Preservation commit: `410b25fcaf358ad6eb11be6a18af01758afe9857`.
Final delivery identity is the linked issue PR's verified head/merge commit.

## Ownership and scope

The dedicated `Frostbite — ISSUE #1` chat owns the shared checkout until the
explicit successor handoff. The planning chat stopped editing it on transfer.
No successor implementation may overlap this issue in the checkout.

The owner approved the native Z80 design and autonomous continuation on
2026-10-31. No further architecture/start permission is required for the
dependency-ready roadmap. The local design/backlog now record that approval.

## Delivered preparation

- External local snapshot of the complete pre-migration working tree except
  root Git internals; archive members, modes, links and source hashes verified.
- Reversible quarantine of inherited code, commands, docs, reports and output
  folders under ignored `.legacy/seaquest/`; 1,641 file relocations/copies
  checked against the original manifest.
- Truthful Frostbite README, active agent instructions, development status and
  project workflow. Old Seaquest release links and active build commands removed.
- Supplied GPLv3 LICENSE retained byte-identically; original Atari inputs and
  derived source/assets remain local.
- Fork/kanban/branch/review/integration and testable-ROM release requirements
  made durable in the repository.

See [preservation details](../baseline-preservation.md) for backup hashes,
local path, recovery instructions and reuse boundaries.

## Verified reference and limits

Canonical input: `references/roms/frostbite.bin`, 4096 bytes.
SHA-256: `cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
MD5: `4ca73eb959299471788f0b685c3ba0b5`.

Initial DiStella/DASM research round-trip was byte-identical. Generated
Frostbite research remains ignored in `outputs/frostbite-planning/`.
This is not a semantic disassembly, region/cadence proof or MSX gameplay test.
No Frostbite MSX ROM, fresh-machine setup, runtime CI, visual/listening test or
physical-hardware acceptance is claimed. This documentation-only issue has no
ROM release or human gameplay request.

## Pending files and local material

Only explicit Frostbite guidance, planning/issue records, ignore rules and the
unchanged license belong in this delivery. Do not add the local tree wholesale.
After integration the tracked checkout must have no pending changes before
transferring it. Expected ignored local material:
`.legacy/`, `.tools/`, `.venv/`, `outputs/`, `references/roms/` and
`.superpowers/`. These belong to preservation/research, not a pending source
implementation.

Do not delete the external snapshot or the quarantined copy. Audit selected
Seaquest infrastructure before reuse. Definitive removal is issue #17.

## Successor and next actions

After issue #1 acceptance/review passes and its delivery is integrated, mark
#1 Done/closed. Normally choose dependency-ready
[issue #2](https://github.com/sandersouza/msxgp-frostbite/issues/2) next:
verify ROM revision, region and measured cadence. Read its local copy and design,
revalidate actual GitHub state and original hash, fork another dedicated
`Frostbite — ISSUE #2` chat in the Frostbite project and move only that item to
In progress when the chat starts.

The successor needs the ignored ROM and preserved local tool caches, so use the
existing checkout with exclusive ownership unless a fresh verified input setup
justifies another workspace. The prior chat stops editing after dispatch.

Every new testable ROM later produced must have a versioned prerelease with
the exact ROM attached, hash/source commit, current state, next work and the
specific human test checklist. Automated, manual-emulator and physical evidence
must remain separate.
