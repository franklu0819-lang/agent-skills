---
name: nex-growth
description: "Growth/operations workflow: data-analyst baselines current metrics → planner drafts the campaign/content plan → user approves at a gate → executor produces copy and assets → reviewer fact-checks tone and overpromising. Use for marketing campaigns, content production, launch announcements, or operations planning. Also triggered as /nex-growth."
---

# Growth / operations workflow

Baseline → plan → approve → produce → fact-check. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — product context, audience, goal, relevant file paths. Never say "as discussed".
- One campaign, one folder: pick a campaign slug up front (e.g. `2026-09-launch`); the plan, baseline, copy, and later results all live together in `docs/marketing/<slug>/`.
- Communicate with the user in the user's language.

## Pipeline

1. **Baseline — dispatch `data-analyst`**
   Current relevant metrics (traffic, conversion, retention — whatever the data sources hold) → report to `docs/marketing/<slug>/baseline.md`. Skip with a note if no data exists yet.
2. **Plan — dispatch `planner`**
   Pass the baseline report + campaign goal + audience, and name the output path. Have planner file the campaign plan to `docs/marketing/<slug>/plan.md` with goals, audience, channels, key messages, content list (naming each item's target file in the same campaign folder), schedule, success metrics.
3. **GATE — user approves the plan** (AskUserQuestion: approve / adjust).
4. **Produce — dispatch `executor`**
   Produce the copy/assets per the plan, filing each item in the campaign folder exactly as the plan names it; follow the product's existing voice and terminology.
5. **Fact-check — dispatch `reviewer`**
   Focus: factual claims, overpromising, tone/audience fit, terminology consistency.
6. **Fix loop — dispatch `executor`** for P0/P1; max 3 rounds.
7. **Deliver**: campaign folder path + content summary; remind to measure with `data-analyst` after the campaign window closes → `docs/marketing/<slug>/results.md`.
