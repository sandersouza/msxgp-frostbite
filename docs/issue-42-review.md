# Issue42 architectural checkpoint review

Independent read-only review covered3d75f48..1c25578, including O/P/Q builders,
runtime paths, ownership and reports. The reviewer found no runtime/bank/RAM
blocker in the selected bounded experiments.19 focused tests passed during the
review; inspected Q-E ROM, source scenes, route hashes and native component
actual/expected buffers matched.

## Important finding and correction

The aggregator accepted complete/count-only physical-owner and scene receipts
without binding every proof to the selected ROM and raw artifacts. An explicit
scene suffix could therefore combine Q-C component proofs with Q-E routes.
The current evidence was correct, but future reports could falsely qualify a
candidate. The shared-owner receipt also omitted ROM identity.

The fix requires exact ROM/count/protection flags; hashes every declared scene
artifact, including ownership/timing; binds physical-owner proof to the primary
probe receipt and capture/band/pool/fill buffers; and authenticates the original
route/probe before reauditing. New immutable v2 owner receipts and bound reports
preserve all original receipts/reports. Existing buffers were reaudited without
rerunning emulators. All measured records and aggregates remain identical.

Negative host tests first failed, then passed. A controlled actual-evidence
regression also reproduced the old reporter accepting mixed Q-C/Q-E proof;
the hardened reporter rejects it before publishing a report. The deliberately
invalid historical output stays under a clearly named ignored regression root.
The complete host suite passes531 tests. No second reviewer was dispatched;
the single correction pass follows the executing-plans review workflow.

## Rulings on explicitly unreviewed acceptance

- Canonical public build/reproduction remains incomplete. Keep the PR draft and
 do not select a human ROM; assuming completion would misstate reproducibility.
- Original speed, unobserved natural levels and timing tails remain open.
 Bounded automated results do not satisfy final timing/full-game acceptance;
 treating them as complete could ship slow or untested scenarios.
- Human emulator, listening and physical hardware checks have not occurred.
 Keep them unclaimed; assuming them would substitute automation for owner tests.
- Future renderers reading old actor keys require a decoder or eager keys.
 The selected floe-first profile remains the enforced scope; extending it without
 that work would make its metadata contract invalid.
- Native Excel remains untested. The workbook passed artifact rendering, formula,
 input-sensitivity and saved XML checks; native-app behavior remains a limitation.

No deferred minor findings were reported. This is an internal checkpoint review,
not release, integration or original-speed acceptance.
