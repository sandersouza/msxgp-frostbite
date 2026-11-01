# Issue13 independent review and disposition

One fresh read-only whole-branch review examined
`b0d8fe206f46106e20ba5b3df43297667b3c08f3` through
`1cafa0e04832c1d3530a89a842149f378a0f2cf5`, using the approved plan/spec,
every Review Focus item and the execution ledger. It ran25 targeted tests,
inspected actual positive logs and reproduced the guard control flow with Tcl.
No critical/runtime gameplay finding or deferred minor was reported.

## Important finding: a failed guard could write success

The reused native/paced fatal handlers requested `exit 1` but returned normally.
Their finish procedures could then write `complete:true` and issue bare `exit`.
openMSX21 queues shutdown and resets its exit code for that later bare request;
the [official implementation](https://github.com/openMSX/openMSX/blob/RELEASE_21_0/src/Reactor.cc#L756-L768)
confirms the behavior. Complete CPU/RAM rows could therefore coexist with a
false success after heap, stack, slot or interrupt failure. Positive logs were
hashed but their fatal markers were not rejected by the final sealer.

The reviewer found no fatal marker in126 selected positive native/paced/stress
logs or either selected microproof log. This demonstrates an acceptance defect,
not observed candidateB memory corruption. Dense benchmark final guards already
propagate errors through `require_movement`.

The parent graded this Important and performed one fix pass. Actual Tcl finish
procedures now propagate a fatal error after requesting exit; valid EOF paths
return explicitly. A positive-log audit rejects fatal markers in every selected
controlled/native/paced/stress/micro proof while preserving intentional negative
logs. The test first reproduced ten final-guard false successes and the missing
positive-log API, then passed all scenarios plus the complete303-test suite.
The first shim needed realistic used-stack bytes to avoid an unrelated hex
stack-min JSON representation; corrected RED results isolated the actual defect.

No ROM build input, original catalog helper, target instruction or ROM byte
changes in this fix. The previous unfinished serial seal was stopped; a fresh
complete final audit ran successfully with the repaired committed producer
`7cbcf7bdb31a6b83bd605da3b6688b5ef82cd489`. Final integration/release still waits
for the remaining delivery checks.

After the fix, all818 full phases, the regular alternating native route and
NTSC/layout1/width1 route, and advanced one-player exhaustion/restart
PAL/layout1/width1 route pass with freshly captured repaired-harness evidence.
PAL peak remains71081/71364. A separate explicit exploratory heap-fault probe in
actual openMSX reports `FLOE_NATIVE_FAIL heap-guard` and leaves no success receipt;
all128 selected positive logs pass the new fatal-marker rejection. The negative
probe changes only ignored instrumentation and retains the exact candidate ROM.

## Behaviors set aside and owner dispositions

- Definitive HUD/art/audio/attract stays #14, with limitations disclosed; do not
  represent this silent synthetic diagnostic as completed presentation.
- Manual-emulator and physical compatibility remain pending owner observations;
  automatic success does not supply either evidence class.
- The loop microproof stops at the unchanged fallback entry. Guard rejection
  preserves entry state; integrated phases/routes separately exercise the
  program. Do not claim exhaustive execution of every slow-body input.
- Complete-game acceptance and legacy removal remain later issues, including
  #17. This issue cannot delete preserved Seaquest material.
- Seal, CI, merged-main reproduction and release downloads are delivery gates
  retained by the parent, not waived by the code-review verdict.

The final verdict was “With fixes.” The single Important fix is verified by
RED→GREEN tests and the green full suite; no second review is requested.
