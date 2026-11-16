# Maintenance checks

[CI](../.github/workflows/ci.yml) checks public sources, runs three essential
unit test files (16 checks), compiles the native game from a fresh checkout
and compares all five resulting files with the 1.0.0 hashes.
No original ROM, private inputs, emulator or firmware is required.

```sh
make ci-verify
make verify
```

`make source-check` inspects Git index blobs after selective staging. Private
research paths, binary cartridges/archives, symlinks/conflicts, non-UTF8 content
and original disassemblies are rejected. The two README images are reviewed,
path/hash-bound exceptions. Native Z80 source and static textual build data
are versioned under `src/game/`.

Actions are pinned, permissions are read-only and checkout does not persist
credentials. CI uploads the build/test logs and the five generated game files;
it never mutates releases or the shared project board.

Artifact identity, emulator play, manual audio review and physical hardware
remain separate evidence classes. Changed game bytes require a new reviewed
baseline and release; never replace the existing 1.0.0 files.

Track maintenance in [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
and follow [the delivery workflow](project-workflow.md). Preserve unrelated
games, items and shared project fields.
