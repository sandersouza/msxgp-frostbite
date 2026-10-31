# Frostbite project instructions

## Target and authority

- Repository: sandersouza/msxgp-frostbite. Codex project: Frostbite.
- Standard-speed MSX1, 64 KiB RAM / 16 KiB VRAM, TMS9918-family VDP and built-in
  PSG; no expansions, turbo, disk or additional sound hardware.
- The supplied Atari 2600 Frostbite ROM is the gameplay authority. Preserve its
  mechanics exactly; document presentation adaptations separately.
- The owner approved the design and autonomous execution on 2026-10-31.
  Read the approved design, relevant local issue copy and handoff before work.

## One GitHub issue per forked chat

- Start every new issue in a separate forked chat within the Frostbite project,
  titled `Frostbite — ISSUE #<number>`. Reuse a matching active chat; avoid
  duplicates. Never implement the next issue in the previous issue's chat.
- Move its item in MSX Game Ports project #7 to `In progress` when work starts.
  Use a scoped `codex/<kind>/<number>-<slug>` branch and focused linked PR.
- Transfer the issue URL, goal, dependencies, branch/commit, pending-file
  ownership, exact artifact hashes, verified evidence, limitations and next
  actions. Keep a durable handoff under docs/handoffs/.
- Only one issue chat may edit the shared checkout. After handoff the old chat
  stops changing it. Verify the new chat's workspace and Frostbite project.
- Continue autonomously to a dependency-ready successor through another fork.
  Routine implementation and successor starts do not need another permission.
- Use `In review` while delivery checks/review remain pending. Close/Done only
  after that issue's own acceptance conditions pass and delivery is integrated.

## Testable-ROM releases

For EVERY new testable MSX ROM version, publish a versioned GitHub release,
using a prerelease during development. Attach the EXACT ROM tested, SHA-256
and source commit. This includes a useful diagnostic build, clearly identified
as diagnostic. A documentation-only change does not create a ROM release.

Release notes must state:
- Current implementation, checks performed and known limitations.
- Next planned work and relevant issues.
- Tests expected from the human: setup/mapper/controls, exact actions, expected
  results and feedback/evidence requested.

Run the relevant automated checks before publishing. Keep automated, manual
emulator and physical hardware evidence distinct. Never silently replace a
published version's binary; changed ROM bytes require a new version.

## Preserved copied material

The supplied Seaquest copy and its old evidence are local-only under ignored
.legacy/seaquest/, with a verified external snapshot. Read
docs/baseline-preservation.md before reusing or moving it.
No historical success is Frostbite proof. Audit selected infrastructure before
reuse; keep original ROMs, complete disassemblies and original-derived generated
assets local/ignored. Final legacy deletion belongs to issue #17 after working
replacement acceptance. Do not stage the local tree wholesale.

## Owner guidance and tools

- Use Obsidian skills only for coding work or when explicitly requested.
- Required agent guidelines live in Obsidian vault `personal`, folder
  `codex-instructions`. Read all `0-` guidelines for every work session and
  the specific guideline relevant to the task.
- Manage notes through the `obsidian` CLI and obsidian-cli skill. If the CLI
  cannot connect, try opening Obsidian; if unavailable after that, ask the owner.
- Consult `github-instructions` for GitHub work, `project-documentation` for
  relevant documentation work and `python-virtualenv` for environment work.
  Follow their current rules and established session decisions.
- English repository/GitHub content; Brazilian Portuguese user updates.
- Prefer the GitHub plugin where sufficient; use gh for project fields and
  capabilities the plugin lacks. Preserve unrelated board items/settings.

Read docs/project-workflow.md for tracking and release details.
