---
name: Frostbite task
about: A scoped porting, infrastructure or validation task
title: ''
labels: ''
assignees: ''
---

## Goal and scope

Describe the observable outcome, exclusions and dependencies. The supplied Atari
ROM governs mechanics; presentation adaptations must be stated separately.

## Ready

- [ ] Acceptance criteria and reference inputs are identified.
- [ ] Dependencies are delivered; unresolved behavior has an explicit research task.
- [ ] Before implementation: dedicated `Frostbite — ISSUE #N` fork and project7 `In progress`.

## Done

- [ ] Own acceptance criteria pass; commands, source commit and hashes are linked.
- [ ] Automated, manual emulator and physical evidence are distinguished.
- [ ] Focused reviewed PR integrated; durable handoff and successor recorded.
- [ ] If a new testable ROM is delivered: versioned prerelease, exact tested ROM,
      SHA-256/source commit, limitations, next work and concrete human test steps.

## Tracking

Type: Task/Bug/Feature/Enhancement. Priority: P0/P1/P2. Size: XS/S/M/L/XL.
Estimate: hours including validation, with assumptions. Dependencies: issue links.
Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Milestone: reuse the established assignment; currently none.

Use existing labels; record unavailable type/priority labels explicitly. Agents
write `.github/issues/frostbite/<slug>.md` before publishing and keep it aligned.
For new cataloged issues, review `.github/project.json` before using tracking helpers.
