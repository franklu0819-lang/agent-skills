---
name: nex-roadmap
description: "Roadmap suggestion workflow: reads ONLY existing project docs (docs/ tree) and product research reports — never source code — then proposes the top 5 features to build next, priority-ranked with explicit rationale. Use when the user wants next-step feature suggestions, a roadmap proposal, or a what-to-build-next decision grounded in existing specs/plans/research. Also triggered as /nex-roadmap."
---

# Roadmap suggestion workflow

Documents and research in, a ranked feature proposal out. Hard constraint: **never read source code** — product judgment here is grounded in specs, plans, reports, and research only. Reading code is refused even when it seems helpful. Track progress with TodoWrite.

## Dispatch rules

- Every dispatch must state the no-code constraint explicitly: pass file paths of docs/reports and forbid opening any source file; code may be referenced only by what the documents themselves say about it.
- Persistence is decided here, not by the agents: the proposal files to `docs/develop/specs/roadmap-YYYY-MM-DD-<slug>.md`.
- Communicate with the user in the user's language.

## Pipeline

1. **Inventory — main agent surveys the docs tree** (no dispatch; Read/Glob only)
   Collect what exists: specs (docs/develop/specs/), business plans (docs/business/), research reports, marketing campaign results, ops incident reports. Note gaps honestly — an empty category is itself input ("no research exists" shapes confidence).
2. **External research — dispatch `researcher`** (only if fresh market input is missing; skip if docs/business/ research is recent and sufficient)
   Web research on: comparable products' feature sets, frequently requested capabilities in this product category, where competitors differentiate. Report in-message (no file output needed for this step). Same no-code constraint.
3. **Draft — dispatch `planner`**
   Pass the doc inventory (paths + one-line summaries) + researcher findings. Ask for the top 5 features to build next. planner delivers in-message: each feature as one entry with — what it is (one sentence), priority rank, rationale citing its evidence (which spec/plan/report/research finding supports it), target users affected, rough effort band (S/M/L), and dependencies on other items. Evidence must come from documents/research only.
4. **Challenge — dispatch `reviewer`**
   Pass planner's proposal + the source doc paths. Attack on: unsupported rankings (priority not backed by cited evidence), features contradicting what the specs/plans actually say, double-counting (two items that are really one feature), missing an obvious high-value item the documents clearly support. Same no-code constraint.
5. **GATE — user reacts to the ranked list** (AskUserQuestion: adopt as roadmap input / adjust priorities / swap items)
   Adjustments loop back to planner once if needed.
6. **File & deliver**
   File the final ranked proposal (5 features, rationale, evidence links, effort bands, dependencies) to `docs/develop/specs/roadmap-YYYY-MM-DD-<slug>.md`; deliver the ranked list in-message with the file path. Suggest next steps: `/nex-specs` on the chosen feature, `/nex-dev` to implement it.
