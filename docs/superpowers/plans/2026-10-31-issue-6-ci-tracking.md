# Original-free CI and scoped tracking implementation plan

> **For agentic workers:** Use superpowers:executing-plans. Native execution and autonomous delivery are already approved. Steps use checkbox syntax.

**Goal:** Build/test clean public sources without Atari inputs and manage only Frostbite's project items reproducibly.
**Architecture:** A read-only Ubuntu CI builds the pinned sjasmplus and synthetic diagnostic. A staged-source guard rejects prohibited material. A separate local GH CLI planner applies only explicitly requested Frostbite item changes; no board credentials enter CI.
**Tech stack:** Python >=3.11/venv/unittest, pinned sjasmplus, GitHub Actions pinned by commit, GH CLI.
**Spec:** docs/superpowers/specs/2026-10-31-frostbite-design.md; .github/issues/frostbite/p06-configure-ci-and-project-tracking.md.

## Global constraints

- Standard-speed MSX1,64KiB RAM/16KiB VRAM,TMS9918-family/built-in PSG; no original inputs/secrets in CI.
- English repository content; exclusive shared checkout on codex/chore/6-original-free-ci-tracking.
- Keep Seaquest quarantine/snapshot and local ROMs untouched; no game changes.
- Only repository sandersouza/msxgp-frostbite items in existing project7; preserve other games and field definitions.
- Existing diagnostic bytes/version remain unchanged. Any changed testable ROM needs a new release.

## Review focus

1. Forced staged original/binary/derived files must fail without reading ignored research or publishing it.
2. Fresh Linux CI must build without inherited tools/venv/originals and run all tests, not skip backends silently.
3. Missing, duplicate, malformed or truncated project data must fail before writing; preserve unrelated items/settings.
4. Repeated tracking apply must do nothing when already aligned; partial failures must remain visible/recoverable.
5. Diagnostic build artifacts must match published version bytes; CI must not silently publish or replace releases.

## Task 1: Original-free source gate and CI

**Files:** scripts/source_policy.py, scripts/ci_setup.py, scripts/ci_verify.py, tests/test_source_policy.py, requirements-ci.txt, .github/workflows/ci.yml, Makefile.
**Interfaces:** source_policy.check_index(root:Path)->list[str] reads staged blobs; ci_setup prepares only verified sjasmplus; ci_verify validates repeated diagnostic bytes against the declared baseline.

- [ ] Write failing tests using temporary Git indexes: prohibited reference/output paths, renamed binary, symlink, generated-disassembly marker, canonical original hash and allowed text/synthetic sources.
- [ ] Run the source-policy tests; expect missing implementation failure. Implement fail-closed index scanning with path/size/type/content checks; keep compact hashes/manifests allowed.
- [ ] Write/run failing version-identity tests; implement ci_verify.check_artifact(data,version,baseline) rejecting changed bytes under a published version.
- [ ] Add source-pinned sjasmplus-only CI preparation and hash-locked py65 wheel install. Ubuntu24.04, read-only permissions, SHA-pinned checkout/upload, no secret or privileged event, explicit safe report upload only.
- [ ] Run all original-free tests, source gate and repeated builds. Commit task1. Remote CI run is required before issue closure.

## Task 2: Scoped project planner

**Files:** scripts/project_tracking.py, tests/test_project_tracking.py, .github/project.json.
**Interfaces:** plan_changes(config,fields,snapshot,issue=None,status=None)->list[dict]; sync(...,apply=False) loads fresh snapshots and uses only planned attach/edit operations. JSON config holds project identity/repository and intended issue Priority/Size/Estimate; status changes require one issue.

- [ ] Write/run failing tests for no-op repeat, missing attachment, changed fields, unrelated same-number issues, duplicate matches, invalid options, malformed estimate, truncated lists and mismatched project identity. Expectations use hand-authored snapshots.
- [ ] Implement pure validated planning and GH transport with bounded commands, complete-list checks and targeted mutations; default dry-run. Apply refreshes/readbacks and reports partial failure, never resets unrelated fields.
- [ ] Run tests/all suite, compare live dry-run with all17 issue bodies and confirm no metadata drift. Exercise #6 lifecycle through helper when ready for review; repeat apply must yield no changes.
- [ ] Commit task2.

## Task 3: Templates, operational docs and delivery

**Files:** .github/ISSUE_TEMPLATE/task.md, .github/pull_request_template.md, docs/ci-and-tracking.md, docs/project-workflow.md, docs/handoffs/issue-6.md, local issue6 copy.
**Interfaces:** docs consume task1 commands and task2 CLI; PR links #6 and records remote CI evidence.

- [ ] Add concise templates covering DoR/DoD, metadata, evidence boundaries, dedicated chat and conditional release gate; no invented milestone/labels.
- [ ] Document exact commands, public-source policy limits, local authentication, dry-run/apply/recovery and manual release boundaries. Link implementation and current limitations from issue6.
- [ ] Run all tests/source gate, clean-clone CI path, remote Actions and inspect uploaded reports. Obtain one independent whole-branch review; fix material findings in one RED→GREEN pass and rerun affected checks.
- [ ] Integrate PR after successful review/checks. Close/Done only once DoD passes; transfer clean checkout and exact release identity via durable handoff to dependency-ready #7 in a new fork.

Self-review: all issue6 scope maps to these tasks. Task1 source gate and CI share no board credentials; task3 consumes both command interfaces. Linux CI is a builder choice within the approved design, distinct from macOS setup and from emulator/hardware acceptance.
