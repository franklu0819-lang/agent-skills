---
name: nex-specs
description: "Product spec: turns an idea or feature request into a reviewed PRD-style spec (user stories, scope, priorities, acceptance criteria, milestones) filed to docs/develop/specs/ and approved by the user. Use when the user describes a product idea and wants requirements clarified before design or development. Also triggered as /nex-specs."
---

# Product spec workflow

Turn a raw idea into a reviewed, user-approved requirements spec. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — goal, relevant file paths, constraints. Never say "as discussed".
- Communicate with the user in the user's language.

## Pipeline

1. **Context first** — if a product already exists, note where its docs/code live (quick Explore or direct Read); planner needs this.
2. **Spec — dispatch `planner`**
   Pass the idea + product context. Have planner file the spec to `docs/develop/specs/prd-YYYY-MM-DD-<slug>.md` with: user stories (each with acceptance criteria), in-scope / out-of-scope, priorities, milestones, open questions.
3. **Review — dispatch `reviewer`**
   Pass the spec path. Focus: logic closed-loop, every story has verifiable acceptance criteria, scope conflicts, missed edge personas.
4. **Fix — dispatch `executor`** for P0/P1 issues; max 3 rounds.
5. **GATE — user approves the spec** (AskUserQuestion: approve / adjust).
6. **Deliver**: spec path + summary; suggest the next step (`/nex-design` or `/nex-dev`).
