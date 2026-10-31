# Public-source CI and project tracking

The [workflow](../.github/workflows/ci.yml) runs on pushes to main/codex branches,
pull requests and manual dispatch. Ubuntu24.04 starts without local ROMs, tools
or environments. It creates `.venv`, installs the hash-locked py65 wheel, builds
the source-pinned sjasmplus and runs the complete original-free unit suite.
Two diagnostic builds must match each other and the declared version's baseline.
Python must be>=3.11; the runner's Python patch level/compiler image is not pinned.
Tool source revisions and Python wheel bytes are pinned; this is not a claim of
bit-reproducible host executables across runner updates.

Actions are pinned by full commit and permissions are contents:read. Checkout
does not persist credentials. There are no repository secrets, board tokens,
privileged PR events or release mutations. Reports use an explicit three-file
allowlist: unit log, build.json and SHA256SUMS. ROMs/research/tool caches are not
uploaded. GitHub's [secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use)
describes full-commit pins and minimum token permissions.

CI proves synthetic test/build identity. It does not run Atari or MSX emulators,
validate gameplay, listen to audio or certify physical machines. Use the separate
[macOS/runtime checklist](toolchain.md) for those evidence classes. A changed
testable ROM needs a new version and release; CI never replaces published assets.
The current baseline remains [v0.0.1-diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.1-diagnostic).

## Reproduce the CI build from a clean source clone

Git, C/C++ compiler, make, file and Python>=3.11 are prerequisites on Linux/macOS.
No emulator, original ROM, Homebrew or board authentication is needed:

```sh
git clone https://github.com/sandersouza/msxgp-frostbite.git frostbite-ci
cd frostbite-ci
python3 -B scripts/source_policy.py
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements-ci.txt
.venv/bin/python -B scripts/ci_setup.py
.venv/bin/python -B -m unittest discover -s tests -v
make ci-verify
```

The dedicated CI preparation installs no system packages and prepares only
sjasmplus. Existing tools/venvs remain subject to the same receipts and refusal
rules as macOS setup. It does not bypass host checks in `scripts/setup.sh`.

## Staged-source boundary

`make source-check` reads Git's index blobs, not working-copy contents or ignored
research. Run it after selectively staging files and before committing. It rejects
local/generated paths, cartridge/archive extensions, symlinks/submodules/conflicts,
binary/non-UTF8 content, the canonical original hash, blobs over1MiB and recognizable
generated-disassembly headers regardless of extension. Assembly files also receive
a broader marker check. Force-added ignored inputs still fail.

This is an enforceable source policy for the current text-only tree, not a
copyright/provenance oracle. Renamed text tables without identifying markers
still require human/agent provenance review. New publishable binary assets or
large sources need an explicit policy/provenance change; never relax the gate to
publish original-derived material. Original ROMs/full disassemblies/generated
graphics stay local/ignored. Build products belong in outputs, releases attach
only reviewed delivery files, and Seaquest cleanup remains issue17.

## Scoped project operations

The [catalog](../.github/project.json) records intended Priority/Size/Estimate
for issues1–17 in this repository. Lifecycle status is deliberately not stored
there: a catalog sync must not reset WIP/Done. New issues require reviewed catalog
entries and matching local issue bodies. Existing native issue types/priority
labels remain unavailable as recorded in those bodies; no fields/labels/milestones
are created by the helper.

Use an existing local GH CLI login with access to the user's project7. No token
is stored in this repository or sent to CI. If access is missing, follow GH's
interactive authentication guidance locally; do not paste credentials into chat.
The [GH item-edit manual](https://cli.github.com/manual/gh_project_item-edit)
documents the targeted field updates used here.

```sh
# Inspect all Frostbite attachments and intended metadata; read-only by default.
.venv/bin/python -B scripts/project_tracking.py
# Apply missing attachments or metadata drift only; repeat should be a no-op.
.venv/bin/python -B scripts/project_tracking.py --apply
# Explicitly move one cataloged issue when its lifecycle changes.
.venv/bin/python -B scripts/project_tracking.py --issue 6 --status 'In progress'
.venv/bin/python -B scripts/project_tracking.py --issue 6 --status 'In progress' --apply
```

The helper verifies project identity, complete item/field responses, canonical
repository/issue URL, unique attachments/options and finite positive estimates
before writing. Estimate's NUMBER schema is independently read through GraphQL;
missing/contradictory Frostbite identity is an error, not an absent attachment.
More than10,000 returned items/fields fails closed instead of
operating on a truncated list. It refreshes/readbacks after each operation and
never deletes items, changes shared field definitions or touches other games.
An operation whose result is not visible stops rather than repeatedly writing.

Project APIs are not transactional. On permission/network/readback failure,
the error lists successful operations; an uncertain last write may have reached
GitHub. Inspect live state, rerun dry-run, then apply the remaining plan. Do not
roll back unrelated edits. Concurrent editors of the same issue's intended
metadata require coordination; refreshed snapshots are not a compare-and-swap.
Templates and [per-issue workflow](project-workflow.md) supply the surrounding
fork, review, release and handoff discipline.
