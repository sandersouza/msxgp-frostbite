# Public-source checks and tracking

[CI](../.github/workflows/ci.yml) runs on main/codex pushes, pull requests and
manual dispatch. Ubuntu creates a project venv, installs the hash-locked py65
wheel and builds source-pinned sjasmplus. It runs the original-free suite,
repeats the hardware diagnostic build against
[its synthetic baseline](../references/diagnostic-baseline.json), and builds
the synthetic SCREEN2 renderer. These are infrastructure checks; the released
native game requires separate local qualification. During the maintenance
freeze, the unit suite contains only six essential files (36 checks); broad
development suites are preserved in Git history.

Actions use full commit pins, read-only contents permissions and checkout
without persisted credentials. Only the test log and diagnostic build/hash
reports are uploaded. CI has no release or project-board mutation step.

## Local validation

With the [host tools](toolchain.md) prepared:

```sh
make test
make ci-verify
make render-build
```

`make source-check` inspects Git index blobs. Run it after selectively staging
changes. It rejects ignored research paths, cartridge/archive files,
symlinks/conflicts, binary/non-UTF8 content, oversized sources and recognized
generated-disassembly markers. It is not a complete provenance oracle.
The owner-supplied donation banner from commit `52ff734` is the only reviewed
binary exception, bound to its exact path and SHA-256 in `source_policy.py`.
Changed bytes or another path fail the gate. Other publishable binary assets
require an explicit policy/provenance decision; generated game assets remain
forbidden.

Automated emulator play, original-state comparisons, audio listening and
physical machines are separate from CI. A successful synthetic build cannot
certify the 1.0.0 cartridge or its disk loaders.

## Project helper

The retained [catalog](../.github/project.json) covers original issues 1–17;
it is not a current backlog or source of lifecycle status. Extend it deliberately
before using the helper for a new issue. The helper defaults to dry-run:

```sh
.venv/bin/python -B scripts/project_tracking.py
```

Only use `--apply` for intended changes after inspecting the plan. The helper
validates project/repository identity, complete field/item responses, unique
attachments and finite estimates. It never deletes items or changes shared
fields. Coordinate metadata with the live issue and follow
[the delivery workflow](project-workflow.md).
