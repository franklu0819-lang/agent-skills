---
name: nex-dev
description: "SDD+TDD bidirectional development workflow: inputs are the product spec AND the user-confirmed design (prototype/screenshots from /nex-design) → spec with testable acceptance criteria (user-approved) → failing tests derived from the spec (red) → minimal implementation to green → dual review (code quality + spec fidelity + design fidelity) → spec reconciliation when reality contradicts the spec. Use for feature development, bug fixes (red = failing repro test, green = the fix), refactors, or any non-trivial code change. Also triggered as /nex-dev."
---

# Development workflow (SDD × TDD)

Inputs: the product spec AND the confirmed design. For UI-facing work, do not develop from the spec alone — run /nex-design first and bring its confirmed output (screenshots + interaction flow) here; implementing UI without a confirmed design is spec-gate skipping by another name. The spec drives the tests; the tests drive the implementation; discoveries flow back into the spec. The spec file remains the single source of truth after delivery. Track progress with TodoWrite. Never skip the spec gate; never write implementation before failing tests exist.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — goal, spec file path, design artifacts (screenshot paths / prototype path) when UI-facing, constraints. Never say "as discussed".
- Communicate with the user in the user's language.

## Pipeline

1. **Intake — check design readiness before planning**
   Identify whether the change is UI-facing. If yes: require the confirmed design from /nex-design (screenshots under `docs/develop/design/<slug>/` + interaction notes). Missing → stop and direct the user to /nex-design first (API/logic-only changes skip this). If a spec already exists (e.g. from /nex-specs), pass its path for refinement instead of starting over. If an approved architecture doc exists under `docs/develop/arch/`, pass its path too.
2. **Spec (SDD) — dispatch `planner`**
   Pass the design artifacts along with the request. Have planner file the working spec to `docs/develop/specs/<slug>-spec.md` with scope and **testable acceptance criteria** — every criterion must be verifiable by at least one test; UI criteria reference the confirmed design (layout, states, flows), not invented specifics. Open questions flagged. If planner judges the change trivial, it says so — offer the user a ceremony-free path at the gate.
3. **GATE — user approves the spec** (AskUserQuestion: approve / adjust / drop).
4. **Red (TDD) — dispatch `executor`**, tests first
   Pass the spec path + design artifacts. executor derives tests from the acceptance criteria — unit tests for logic, E2E for user-facing flows (chrome-devtools by default, asserted against the confirmed design's flows/states) — runs them, and confirms each fails **for the right reason** (assertion failure, not setup/syntax errors). No implementation code yet. Report the failing-test list mapped to acceptance criteria.
5. **Coverage check (SDD → TDD direction)**
   Verify every acceptance criterion maps to at least one failing test. Gaps go back to executor before implementation proceeds.
6. **Green (TDD) — dispatch `executor`**
   Implement the minimum that turns every test green, following repo conventions and matching the confirmed design for UI work; refactor only within scope. If a criterion or the design turns out wrong or unimplementable, STOP that item and report a **spec/design defect** instead of hacking around it (TDD → SDD/design feedback direction).
7. **Dual review — dispatch `reviewer`**
   Pass the diff + spec path + design artifacts + test list. Three gates: (a) code quality per repo conventions; (b) spec fidelity — every acceptance criterion covered by a meaningful assertion, no untested criterion, no coverage theater; (c) design fidelity (UI work) — rendered result matches the confirmed design's layout, states, and flows.
8. **Fix loop — dispatch `executor`** for P0/P1 (code, test, or design-fidelity gaps); re-run the suite; max 3 rounds, then report what remains. If blocked by a suspected unrelated bug, dispatch `oracle` for diagnosis — the fix decision is the user's.
9. **Spec reconciliation (TDD → SDD closure)**
   Spec defects surfaced in steps 6-8 get folded back into the spec file so it matches what was actually built; every spec change is listed in the final report.
10. **Deliver**: change summary + full test results (green) + spec path + design artifacts used + spec changes made.
