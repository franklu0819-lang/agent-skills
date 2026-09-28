---
name: paper-draft
description: "Paper drafting workflow: planner produces a section outline with a claim→evidence map (user-approved) → executor drafts section by section using experiment outputs and the verified literature as the only evidence pool → reviewer checks argument support and citation accuracy per section. Use for writing a paper first draft, 论文初稿, or specific chapters/sections (intro, method, experiments, discussion, 学位论文章节). Also triggered as /paper-draft."
---

# Paper drafting workflow

Draft a paper section by section from an approved outline, with every claim backed by evidence. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — outline, section spec, input file paths, constraints. Never say "as discussed".
- One paper, one folder: all artifacts live in `docs/paper/<slug>/`.
- Numbers and results may only come from experiment/analysis artifacts; citations may only come from the verified literature matrix. No invented data, no unverified references.
- Independent sections can be drafted in parallel (dispatch in the same message).
- Communicate with the user in the user's language; the paper's language follows the venue/degree requirement.

## Pipeline

1. **Inputs**: locate the proposal and literature review under `docs/paper/<slug>/` (if missing, ask the user for the paper's thesis and key references). Confirm the structure convention — IMRaD for journal/conference papers, the school's template for degree theses — and the language.
2. **Evidence first**
   If experiments were run, use the figures/tables under `docs/paper/<slug>/experiments/analysis/`. If the paper reports experiments but none exist yet, suggest `/paper-experiment` before drafting — prose written ahead of evidence invites invented numbers. For data-only papers (surveys, public datasets), dispatch `data-analyst` on the real data → `docs/paper/<slug>/assets/`.
   Every number later cited in prose must trace to one of these artifacts.
3. **Outline — dispatch `planner`** → `docs/paper/<slug>/outline.md`
   Per section: the claims it makes, the evidence for each (which figure/table/citation), length budget, and a contribution↔section mapping so nothing promised in the abstract goes unsupported.
4. **GATE — user approves the outline** (AskUserQuestion: approve / adjust). Fixing structure here is far cheaper than after drafting.
5. **Draft — dispatch `executor`** per section → `docs/paper/<slug>/draft/<nn>-<section>.md`
   Follow the outline's claims; cite only verified references; reference figures/tables by artifact name.
6. **Review — dispatch `reviewer`** per drafted section
   Focus: every claim has evidence, numbers match the artifacts, citations real, and the argument flows across section boundaries.
7. **Fix — dispatch `executor`**; max 3 rounds per section.
8. **Deliver**: draft paths + completion summary; suggest the next step (`/paper-revise`).
