# Frostbite approved backlog

The owner approved the design and autonomous execution on 2026-10-31. Issue #1
started in its dedicated forked chat; GitHub project statuses are live authority.
Estimates remain revisable as research proceeds. Priority P2 and native
Task type are recorded in the bodies because priority labels/types are unavailable.
Project #7 stores Status, Priority, Size and Estimate. No milestone was invented.

| Issue | Title | Dependencies | Size | Hours |
| --- | --- | --- | --- | ---: |
| [#1](https://github.com/sandersouza/msxgp-frostbite/issues/1) | Preserve the copied baseline and establish Frostbite issue/chat workflow | None | S | 3 |
| [#2](https://github.com/sandersouza/msxgp-frostbite/issues/2) | Identify the original ROM revision, region and measured cadence | #1 | S | 3 |
| [#3](https://github.com/sandersouza/msxgp-frostbite/issues/3) | Reconstruct and annotate the Atari 2600 disassembly and state map | #2 | L | 12 |
| [#4](https://github.com/sandersouza/msxgp-frostbite/issues/4) | Specify original gameplay contracts and edge-case probes | #3 | M | 8 |
| [#5](https://github.com/sandersouza/msxgp-frostbite/issues/5) | Bootstrap a reproducible macOS toolchain and MSX1 ROM scaffold | #1 | M | 8 |
| [#6](https://github.com/sandersouza/msxgp-frostbite/issues/6) | Configure original-free CI and GitHub project tracking | #1, #5 | M | 5 |
| [#7](https://github.com/sandersouza/msxgp-frostbite/issues/7) | Capture independent deterministic Atari traces and comparison oracles | #3, #4, #5 | L | 14 |
| [#8](https://github.com/sandersouza/msxgp-frostbite/issues/8) | Benchmark worst-case SCREEN 2 rendering and sprite allocation | #5, #7 | L | 12 |
| [#9](https://github.com/sandersouza/msxgp-frostbite/issues/9) | Extract Frostbite graphics and map MSX1 coordinates and palette | #3, #8 | M | 8 |
| [#10](https://github.com/sandersouza/msxgp-frostbite/issues/10) | Port native input, jumping, air control and floe transport | #7, #8, #9 | L | 16 |
| [#11](https://github.com/sandersouza/msxgp-frostbite/issues/11) | Port ice floes, reversal costs, igloo construction and temperature | #10 | L | 14 |
| [#12](https://github.com/sandersouza/msxgp-frostbite/issues/12) | Port hazards, fish, bear and original collision semantics | #11 | L | 16 |
| [#13](https://github.com/sandersouza/msxgp-frostbite/issues/13) | Port scoring, progression, reserves and all game variations | #12 | L | 14 |
| [#14](https://github.com/sandersouza/msxgp-frostbite/issues/14) | Reproduce Frostbite HUD, PSG event timing and attract flow | #9, #13 | L | 12 |
| [#15](https://github.com/sandersouza/msxgp-frostbite/issues/15) | Validate 50/60 Hz cadence, input latency and full-density budgets | #6, #14 | L | 12 |
| [#16](https://github.com/sandersouza/msxgp-frostbite/issues/16) | Run full-game differential regression and hardware acceptance | #15 | L | 16 |
| [#17](https://github.com/sandersouza/msxgp-frostbite/issues/17) | Remove Seaquest legacy and package a reproducible Frostbite release | #16 | M | 8 |

Estimates include implementation and validation effort, not elapsed delivery dates.
Reverse-engineering discoveries may require splitting issues and revising estimates.

First implementation: issue #1, through a dedicated forked Frostbite chat after
the owner's design approval. Move each item to In progress when its chat starts work.
The planning chat stops editing the shared checkout when ownership is transferred.
