---
name: patent-disclosure
description: "Patent disclosure workflow: mine invention points out of a rough idea, codebase, or design docs → executor drafts the technical disclosure (background, technical solution, effects, embodiments) → reviewer checks sufficiency of disclosure and invention-point sharpness → user-approved disclosure. Use when starting any patent: 技术交底书, 发明交底, mining patentable points from a feature/算法/系统设计, or preparing material to hand to a patent attorney. Also triggered as /patent-disclosure."
---

# Patent disclosure workflow

Turn a rough technical idea (or code, or design docs) into a reviewed, user-approved invention disclosure. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — goal, source-material paths, output paths, constraints. Never say "as discussed".
- One case, one folder: reuse the case's existing folder if there is one; otherwise default to `docs/business/patent/<case-slug>/` (a project AGENTS.md or the user naming another location wins). Pipeline paths below are relative to the case folder.
- A disclosure is judged by what a person skilled in the art can rebuild from it: no vague hand-waving where a concrete mechanism is needed, and no invented technical effects — every effect must trace to the source material or be marked "to be verified".
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language; the disclosure's language follows the target jurisdiction (default Chinese for CN filings).
- The output is a working draft for a patent professional — never present it as final legal work.

## Pipeline

1. **Setup — confirm with the user**: what the source material is (verbal description / code paths / design docs / a finished paper), the technical field, and the target jurisdiction (default CN). Pick the case slug → case folder.
2. **Mine — dispatch `executor`** → `invention-points.md`
   Read the source material and extract candidate invention points, each as a problem→means→effect triple, plus alternative embodiments and variants found in the material. Flag anything that is a pure business method or abstract idea with no technical character.
3. **Scout — dispatch `researcher`** (after mining; one dispatch covering all candidate points)
   For each candidate, a quick check of whether it is already commonplace (patents + literature), each with a verifiable source URL. Output → `scout.md` (one section per candidate: already-commonplace / plausibly new / unclear, with evidence). This is fast reconnaissance, not a clearance search — that is `/patent-priorart`.
4. **Draft — dispatch `executor`** → `disclosure.md`
   Inputs: the source material + `invention-points.md` + `scout.md`. Already-commonplace points are dropped or demoted to 背景技术 material per the user's call; everything else carries into the draft. Standard structure: 发明名称; 技术领域; 背景技术 (what exists, what is wrong with it — factual, no disparagement); 发明内容 (technical problem, the solution with every step/component written so a skilled person could implement it, beneficial effects tied to the means); 附图说明; 具体实施方式 (at least one complete embodiment per invention point, plus variants); 关键创新点与可替代方案.
5. **Review — dispatch `reviewer`**
   Focus: sufficiency of disclosure (could a skilled person reproduce it?), invention points stated sharply, effects actually supported by the means, unity of invention when several points coexist.
6. **Fix — dispatch `executor`** for P0/P1 issues; max 3 rounds. If P0s remain after round 3, stop and report the open issues to the user instead of delivering a broken draft.
7. **GATE — user approves the disclosure** (AskUserQuestion: approve / adjust).
8. **Deliver**: disclosure path + summary of invention points; suggest the next step (`/patent-priorart`, or `/patent-claims` directly if an attorney will run the search).
