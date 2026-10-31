# Issue #1 — preserved baseline and Frostbite workflow implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the supplied copy and make active repository guidance exclusively describe the Frostbite project.

**Architecture:** Keep an external verified archive of the complete pre-migration tree, excluding only root Git internals. Quarantine inherited untracked Seaquest files locally, then publish only Frostbite guidance, provenance and delivery records. Keep the original ROM at its canonical local path.

**Tech Stack:** Git/GitHub, Markdown, Python standard library for one-off archive and integrity checks.

**Spec:** `docs/superpowers/specs/2026-10-31-frostbite-design.md`, approved by the owner in the planning chat on 2026-10-31; issue https://github.com/sandersouza/msxgp-frostbite/issues/1.

## Global Constraints

- Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions.
- Exact original gameplay remains the acceptance objective; this issue changes no game mechanics.
- No original ROM, complete disassembly or original-derived generated assets in public Git.
- One issue per dedicated forked Frostbite chat, at most one owner of the shared checkout.
- Each new testable ROM requires a versioned release with exact ROM attached, hash/commit, current state, next work and concrete human tests.
- Definitive legacy removal is issue #17 after working replacement acceptance.
- User approval already authorizes native execution and routine delivery; do not repeat architecture or execution-method questions.

## Review Focus

1. Ignored original inputs must stay local even when migrating ignore rules; verify indexed paths and archive member identities.
2. Inherited commands must not launch Seaquest under a Frostbite name; remove the active inherited Makefile from the working root by reversible quarantine.
3. Every moved source/evidence byte must survive; compare quarantined files with snapshot manifest hashes and link targets.
4. Historical success records must never become Frostbite proof; isolate old docs/reference reports and state the truthful development status.
5. Fork/kanban/release rules must travel with the repository; verify active guidance and a durable successor handoff before transferring ownership.

## Preconditions already verified

- Full archive and member hashes: 6,452 files, 4 symlinks, 7,141 total entries; source file hashes unchanged after archival.
- Snapshot SHA-256 `f40e2592543a3283741e664fbf5ba0f2165e14fbd57f6f48d6ee0b905098609b`.
- User-approved planning PR #18 merged as `468bfa53ac77e99af10aa0fa22130c230d019698`.
- Dedicated branch `codex/chore/1-frostbite-workflow`; issue #1 In progress; this chat owns the shared checkout.

### Task 1: Isolate the preserved inherited baseline

**Files:** Local-only `.legacy/seaquest/`; modify `.gitignore`; create `docs/baseline-preservation.md`.

**Interfaces:** Consumes the external archive/manifest and the initial untracked-file inventory. Produces an ignored, hash-verified local legacy tree plus a compact public provenance record; canonical `references/roms/frostbite.bin` stays in place.

- [x] Move only snapshot-matching inherited untracked files into `.legacy/seaquest/`, preserving relative paths. Keep active AGENTS.md, LICENSE and .gitignore for deliberate replacement/preservation. Copy the old README/AGENTS/ignore rules into quarantine before editing them. Keep `.tools/`, `.venv/` and Frostbite planning research outputs in place.
- [x] Move inherited ignored Seaquest output folders into quarantine; retain original ROM and tool caches locally.
- [x] Replace ignore rules with focused protections for local originals, generated assets, legacy, outputs, tools, environments and skill workspaces.
- [x] Write provenance, archive/member verification evidence, restore instructions and migration boundaries.
- [x] Verify each moved/copied file against the external manifest and verify the canonical original ROM hash. Expected: no mismatches; no inherited Makefile/src/scripts/tests active in the root; local-only directories ignored.
- [x] Commit only preservation documentation and ignore rules after verification.

### Task 2: Publish truthful guidance and deliver issue #1

**Files:** Modify `README.md`, `AGENTS.md`, `docs/project-workflow.md`, `docs/development.md`, approved design/backlog and issue #1 local copy; create `docs/handoffs/issue-1.md`.

**Interfaces:** Consumes Task 1's verified preservation evidence. Produces English repository guidance, an approved design status, issue/PR evidence and an exclusive successor handoff.

- [x] Replace active Seaquest claims with Frostbite's actual state: no MSX ROM or fresh setup validated yet, no inherited commands represented as working Frostbite tooling.
- [x] Record forked issue chat, branch, status, review/integration, release and evidence rules; preserve owner Obsidian guideline requirements in AGENTS.md.
- [x] Preserve the supplied GPLv3 LICENSE unchanged; state that original Atari material has separate ownership and is not included.
- [x] Record owner design approval without rewriting historical starting-point evidence. Update issue #1 progress and acceptance record, keeping local/remote copies equal.
- [x] Verify relative Markdown links, tracked-file scope, absence of original/generated binaries, whitespace and all workflow/release requirements. Expected: all checks pass; no gameplay claim or testable-ROM release for this documentation-only issue.
- [ ] Obtain independent whole-branch review, resolve material findings, create/link PR and move #1 to In review while pending. Integrate only after its acceptance checks pass; then close #1/Done.
- [ ] Fork a dependency-ready successor (normally #2) within Frostbite, hand over verified branch/artifact/dirty-state evidence and stop editing this checkout.

## Execution rulings and evidence

- Native execution in the existing checkout follows the explicit exclusive-ownership handoff; no additional worktree is needed for these preserved local inputs.
- Operational preservation preceded this plan so no supplied file was changed before a verified backup existed.
- This is a reversible documentation/migration task; verification uses integrity and repository checks rather than tests that mirror document implementation.
- Self-review: both task scopes trace to issue #1; runtime/toolchain work stays in #5 and final deletion in #17; each Review Focus item has an explicit verification step.
