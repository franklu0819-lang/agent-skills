---
name: nex-docs-tidy
description: "Docs audit workflow: survey the docs/ tree against the workflow conventions and produce a layout health report (structure compliance, staleness, orphans/duplicates), user picks dispositions at a gate, executor applies the approved moves/marks/retirements. Content is NOT verified against code (that is /nex-reverse's job) and lifecycle state is NOT judged (a finished campaign looks the same as an active one — that call is the owning workflow's/user's). Use when the user wants to tidy the docs layout or get a periodic structural health check. Also triggered as /nex-docs-tidy."
---

# Docs tidy workflow

Read-only layout check first, act only on approval. Two hard boundaries: never judge whether document content matches the code (that is /nex-reverse's job), never judge lifecycle state (whether a campaign/release is finished — that needs business context; flag at most, never conclude). Track progress with TodoWrite.

## Dispatch rules

- The tidy report is produced by the main agent itself (pure structure checking — no subagent needed); `executor` is dispatched only for the approved write phase.
- Persistence is decided here, not by the agents: the tidy report files to `docs/develop/ops/YYYY-MM-DD-docs-tidy.md`.
- Communicate with the user in the user's language.

## Pipeline

1. **Survey — dispatch the built-in `Explore` agent**
   Full inventory of the `docs/` tree: every file's path, type (spec/plan/report/design/marketing/doc), last-modified date, and internal links.
2. **Tidy report — main agent analyzes** (no dispatch)
   Reference layout (the software-development docs layout; the project's AGENTS.md or its workflow skills may declare other layouts — those override or extend this, e.g. additional top-level folders from non-dev workflows are legitimate, not violations):
   ```
   docs/
   ├── business/<slug>/        # business plans (research · baseline · plan), <slug>-slides/ decks
   ├── develop/
   │   ├── specs/              # PRDs, working specs, module specs, roadmaps
   │   ├── arch/<slug>/        # architecture.md · database.md (forward + as-built)
   │   ├── design/<slug>/      # UI prototype screenshots
   │   ├── test/               # test catalogs / coverage matrices
   │   ├── release/<version>/  # release records
   │   └── ops/                # incident records, tidy reports
   ├── marketing/<campaign>/   # one folder per campaign
   └── *.md                    # README, architecture overview, module docs, API refs, deployment guides
   ```
   Three check categories against that reference (or the project's declared layout):
   - **Structure compliance**: files outside their conventioned stage folders; folder names not matching the `<slug>` / `<campaign>` / `<version>` pattern; files at the docs root that belong in a stage folder. If the project declares no layout and no nex-* output exists, state that plainly and limit the check to orphans/duplicates only.
   - **Staleness**: specs/plans not touched for a long time (by last-modified date and doc-internal references like "planned for Q2"); reported as facts ("untouched since March"), never as conclusions ("outdated").
   - **Orphans & duplicates**: files nothing links to and no workflow claims; near-duplicate pairs (same topic, divergent locations).
   Each finding gets a suggested disposition: move / mark-archived / retire / merge / leave.
3. **GATE — user picks dispositions** (AskUserQuestion, batched per category)
   Approve / adjust each suggested action. Default is "leave" for anything uncertain — tidy never deletes content without explicit approval.
4. **Apply — dispatch `executor`**
   Execute only the approved actions: move files into correct stage folders (fixing internal links), add a brief `archived: true` note + date to archived items' frontmatter or title, retire superseded copies as approved. Explicitly forbidden: deleting anything not explicitly approved, editing document body content beyond the archived marker.
5. **Deliver & record**
   Write the tidy report (findings, approved actions, what was applied, what was left) to `docs/develop/ops/YYYY-MM-DD-docs-tidy.md`; deliver a summary + the report path.
