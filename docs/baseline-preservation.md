# Supplied baseline preservation and provenance

## What was received

The owner supplied a local copy of the Seaquest development folder as a starting
point for Frostbite. At initial inspection only README.md was tracked in this
repository; the planning documents/issues were subsequently committed.
The supplied source, scripts, tests, reports, Makefile, license and workflow
files were mostly untracked. A local copy is not proof of any particular
upstream Seaquest commit; no upstream source revision is inferred.

Before changing supplied files, issue #1 preserved the complete working tree
outside this repository, excluding only the root .git directory. The archive
includes local original inputs, ignored generated results, tools, environment
files, directory modes and link targets. The initial Git commit/status are
recorded in its manifest. It is a local preservation artifact, not a release asset.

## External local snapshot

Location relative to the owner's home directory:

`Library/Application Support/Codex/Backups/frostbite/2026-10-31-pre-migration/`

| Artifact | Identity |
| --- | --- |
| baseline.tar | 7,672,637,440 bytes |
| Archive SHA-256 | f40e2592543a3283741e664fbf5ba0f2165e14fbd57f6f48d6ee0b905098609b |
| manifest.json SHA-256 | fd28446af742ba2958f0a3b4aa3c0f6c0bab077db4f97c1e7fbec25f847e77b1 |
| Initial source commit | bef4846d6b61bd733ba244ae77f9dfc1ec96b5eb |
| Entries | 7,141, including 6,452 regular files and 4 symlinks |
| Regular-file bytes | 7,659,977,426 |

The verification pass read every archived file, compared its SHA-256 against
the source manifest, checked file modes and symlink targets, and reread the
source files to confirm they had not changed during archival.
The local verification.json records the result. No extraction was needed to
establish member-content identity.

## Reversible local isolation

Inherited untracked source, tooling, tests, issue drafts, documentation and
reference reports now live under ignored `.legacy/seaquest/`, preserving their
relative paths. Inherited output folders moved there as well. The original
README, AGENTS.md, ignore rules and LICENSE were copied into that tree before
active guidance was changed.

A second pass verified 1,641 relocated/copied file entries against the external
manifest (1,637 moved and 4 copied). Local relocations.json records the paths
and operation. No inherited source or evidence was deleted. Empty working
directories left by the moves were removed; their original entries remain in
the archive.

These locations stay in the active checkout:

- `references/roms/frostbite.bin`: the supplied original ROM, still local/ignored.
- `.tools/` and `.venv/`: local caches/environment, preserved for later audit.
- `outputs/frostbite-planning/`: Frostbite research artifacts from planning.
- `LICENSE`: the supplied GPLv3 license text, byte-identical; committed unchanged.
- Approved Frostbite documents and issue copies already tracked by planning.

The copied Makefile, src/, scripts/, tests/ and workflow are no longer active
at the repository root. Their commands/results must not be represented as
working Frostbite tooling or acceptance. Issue #5 supplies the actual Frostbite
environment and diagnostic scaffold; issue #6 supplies its CI.

The canonical original ROM was rechecked after isolation:
4096 bytes; SHA-256
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
Only hashes and compact provenance are published here; original inputs,
full disassemblies and original-derived generated assets remain local.

## Recovery checklist

Restore into a fresh directory, never over a working checkout:

```sh
backup="$HOME/Library/Application Support/Codex/Backups/frostbite/2026-10-31-pre-migration"
shasum -a 256 "$backup/baseline.tar" "$backup/manifest.json"
restore_dir=$(mktemp -d /tmp/frostbite-baseline.XXXXXX)
tar -xpf "$backup/baseline.tar" -C "$restore_dir"
```

Compare the archive and manifest hashes with the table before extraction.
The restored tree is under `$restore_dir/frostbite/`. The root Git internals
were excluded; recover versioned history from this repository, not from the tar.
The local manifest supplies per-file hashes, modes, symlink targets and the
original status inventory for deeper checks. Treat the restored tree as
historical Seaquest material.

## Reuse and final cleanup gate

Audit provenance, dependency/license requirements and game-specific assumptions
for each selected file before reuse. Credit the Seaquest infrastructure where
retained; Atari/Activision original material is separately owned and is not
included in public source by this preservation step.

Do not reuse Seaquest reports as Frostbite proof. Preserve independent original
execution versus target comparisons, and distinguish automated, manual-emulator
and physical-machine evidence.

Issue #17 removes obsolete local legacy only after the Frostbite replacements
work and pass their required checks. This issue establishes preservation and
isolation; it does not assert gameplay, renderer, fresh-install or hardware
acceptance and does not produce a testable ROM.
