# Port native input, jumping, air control and floe transport

Planning ID: P10. Status: In review; canonical automated evidence frozen; independent review and its material auditor fix complete; final CI, integration and release readbacks remain pending.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/10

## Goal

Deliver source-equivalent Bailey movement on native Z80.

## Scope

Audit reusable translation machinery and remove Seaquest-address shortcuts; preserve flags/BCD/update order; implement keyboard/joystick adapters, Reset/Select and source-cadence sampling; compare takeoff/landing, steering, boundaries and transport.

## Dependencies and readiness

Dependencies: [P07 / #7](https://github.com/sandersouza/msxgp-frostbite/issues/7), [P08 / #8](https://github.com/sandersouza/msxgp-frostbite/issues/8), [P09 / #9](https://github.com/sandersouza/msxgp-frostbite/issues/9).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

Native state matches independent source scenarios including held/diagonal/conflicting inputs and transitions; negative controls work; measured active-play renderer/input timing remains within budget.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 16 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).

## Frozen implementation evidence

Native post-visible phase, raw MSX input and the256KiB ASCII16 movement diagnostic are implemented. Contacts and graphics remain explicitly diagnostic; natural/full-game proof is not claimed. See docs/native-movement.md, references/native-result.json and docs/releases/v0.0.3-movement.md.

Exact ROM producer:64c2cec6d37e5b988b0b86bc1d57836dbe43498a. ROM SHA-256:31bb62e4886c8baf361584ce6a140fc05e34c77be15642780e23ad5d5fdb9f82. Frozen private package:outputs/movement/issue10-final. Generic4497/specialized1793 CPU cases,1354 genuine-device cases per path, eleven240-frame pixel/native/guard/cadence captures and six targeted faults passed. Minimum measured margins:NTSC10736/PAL1227cycles. These finite fixtures do not certify all future states.

Public CI remains original-free. Manual emulator, subjective audio/palette, expanded-slot and physical acceptance remain pending. Close/Done only after the reviewed delivery is integrated and its exact release assets are downloaded and verified.

Independent review found one material delivery-auditor gap, now fixed in fa128da: complete required raw-file sets and hashes, OMR/mirror/profile binding, and actual failure stage/cause verification. All three review reproductions reject; 174 host tests pass. The separate immutable integrity supplement leaves original runtime/capture producer and ROM bytes unchanged; public summary:references/native-integrity-result.json.
