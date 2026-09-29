---
name: nex-arch
description: "Technical architecture workflow: survey existing structure → researcher proposes architecture (components, tech-selection trade-offs, data flow, data-model draft) → user picks the direction at a gate → planner files the architecture doc and database design doc → reviewer gates closure and consistency → fix loop. Use when the user wants system or module architecture design, technology selection with a durable record, or database/ER/schema design. Feeds /nex-dev, which implements against the approved architecture. Also triggered as /nex-arch."
---

# Architecture & database design workflow

Decide how the system is built and record why. The output feeds `/nex-dev`. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — requirement or spec paths, existing-structure pointers, output paths. Never say "as discussed".
- Persistence is decided here, not by the agents: one design effort, one folder — everything files to `docs/develop/arch/<slug>/` (shared with /nex-reverse's as-built designs, so /nex-dev always looks in one place).
- Communicate with the user in the user's language.

## Pipeline

1. **Survey — dispatch the built-in `Explore` agent** (skip for greenfield projects with no code)
   Existing module structure, current schema and migrations, frameworks in use, constraints worth respecting.
2. **Architecture proposal — dispatch `researcher`**
   Pass the requirement (or approved spec path) + survey findings. researcher returns in-message: component breakdown, technology-selection comparison table (dimensions × candidates, with the conditions under which the recommendation flips), data flow, a data-model draft (entities + key relations), and the top risks. Read-only — no files.
3. **GATE — user picks the direction** (AskUserQuestion)
   Present the key bets: component split, chosen stack, data-model shape. Adjustments go back to researcher.
4. **File the design docs — dispatch `planner` twice, in parallel**
   - `docs/develop/arch/<slug>/architecture.md`: components & responsibilities, chosen stack with rationale (lightweight ADR — options considered, why the winner, flip conditions), data flow, cross-cutting concerns (auth, errors, config).
   - `docs/develop/arch/<slug>/database.md`: entities & ER, table definitions (columns, types, constraints), indexes with the query patterns they serve, migration strategy.
5. **Review — dispatch `reviewer`**
   Pass both doc paths + the requirement/spec. Gate list: architecture not closed-loop, decisions without stated rationale or flip conditions, contradiction with the spec, database design missing indexes for the stated query patterns or missing a migration path.
6. **Fix loop — dispatch `executor`** for P0/P1 (document files only); max 3 rounds.
7. **Deliver**
   Both file paths + a summary of key decisions. Note that `/nex-dev` should receive the architecture doc path so implementation follows it.
