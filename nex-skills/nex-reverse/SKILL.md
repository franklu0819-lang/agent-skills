---
name: nex-reverse
description: "Reverse-engineering: reconstructs the as-built architecture and database design from the code, recovers per-module behavior specs and human docs, and builds the test catalog, all consistency-reviewed. Use when the user wants to recover a legacy project's architecture, database/ER design, specs, test cases, or documentation from existing code. Also triggered as /nex-reverse."
---

# Reverse-engineering workflow

The code is the source of truth; documents are the product — architecture and database design included. Never invent what the code does not have. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — target paths, output paths, conventions. Never say "as discussed".
- Persistence is decided here, not by the agents: as-built architecture and database design file to `docs/develop/arch/<slug>/` (same home and format as forward /nex-arch, so /nex-dev always looks in one place); module specs file to `docs/develop/specs/`; the test catalog files to `docs/develop/test/`; human docs → `docs/` top level.
- Independent work runs in parallel (batch dispatches).
- Communicate with the user in the user's language.

## Pipeline

1. **Survey — dispatch the built-in `Explore` agent**
   Repo map: entry points, modules and responsibilities, tech stack, test framework + how to run the suite, database layer (schema / migrations / ORM models), existing docs and their staleness.
2. **GATE — user confirms scope & per-doc disposition** (AskUserQuestion)
   Document set to produce: as-built architecture + database design, per-module specs, test catalog, README / module / API docs. For large repos, select modules instead of all. Then present the disposition table built from the survey — one row per existing doc and one per missing doc:
   - Existing doc → **migrate** (move into the docs/ layout below this project, mapping to its stage folder) / **refresh in place** (stay put, content rewritten from code) / **replace** (write fresh in the new layout, retire the old) / **keep untouched**;
   - Missing doc → **backfill** (produce it in the layout) / **skip**.
   Default suggestion per row: migrate if only its location is wrong, refresh if only its content is stale, replace if both, backfill for important gaps (README, specs for core modules). Carry the choices into steps 4-9.
3. **As-built architecture & database — dispatch `researcher`**
   Pass the survey findings. researcher returns in-message: actual components & responsibilities (vs. any documented intent), dependencies and data flow, the real data model (entities, tables, columns, key indexes), and notable drift or risks — schema vs ORM mismatch, missing indexes for hot query patterns. Read-only, no files.
4. **File the as-built design — dispatch `planner` twice, in parallel**
   - `docs/develop/arch/<slug>/architecture.md` — components, dependencies, data flow, headed "as-built (reversed from code)"; drift notes included.
   - `docs/develop/arch/<slug>/database.md` — ER, tables/columns/constraints, actual indexes and the query patterns they serve, migration state.
5. **Reverse specs — dispatch `planner` per module** (parallel batches)
   Module behavior as **testable acceptance criteria**, using the architecture doc's module boundaries; explicit "inferred — verify" marks where the code is ambiguous → `docs/develop/specs/<module>-spec.md`.
6. **Test catalog — dispatch `executor`**
   Run the test suite, inventory every test (name → module → what it actually asserts), map to the reversed acceptance criteria, produce the coverage matrix + missing-case list → `docs/develop/test/catalog-<slug>.md`.
7. **Organize & human docs — dispatch `planner` per document** (parallel batches)
   Apply the disposition table first: execute migrations (move files into the docs/ layout, fixing internal links), then README (what/why/how to run), module docs, API docs from routes/schemas → `docs/` top level, backfills into their stage folders, and retire old copies as chosen. Refresh-in-place docs get rewritten at their existing path from the reversed facts; docs marked keep-untouched are not modified and not cited as current. Empty legacy folders are removed after migration.
8. **Consistency review — dispatch `reviewer`**
   Every artifact against the code. P0 = document contradicts code; also: invented behavior, architecture/database docs mismatching actual schema or dependencies, test-catalog mapping wrong, stale info presented as current. Layout checks: migrated files actually in their stage folders, no orphaned copies left in legacy locations, retired docs not lingering beside replacements, links not broken by moves.
9. **Fix loop — dispatch `executor`** for P0/P1 (document files only); max 3 rounds.
10. **Deliver**
     File list (`docs/develop/specs/` + `docs/develop/arch/` + `docs/develop/test/` + `docs/`), a migration table (old path → new path per moved doc), backfill summary (what was produced for which gap), coverage-gap summary, drift summary. Suggest `/nex-dev` on selected gaps — note that `/nex-dev` can now consume the recovered design docs the same way as a forward-designed project.
