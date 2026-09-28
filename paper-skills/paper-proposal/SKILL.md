---
name: paper-proposal
description: "Paper proposal workflow: researcher scouts the field and gaps → planner drafts the research proposal (questions, hypotheses, method, contributions, work plan) → adversarial review of novelty and feasibility → user-approved proposal. Use when starting any paper or thesis: choosing a topic, defining research questions, writing a research proposal, 开题报告, or evaluating whether an idea is publishable. Also triggered as /paper-proposal."
---

# Paper proposal workflow

Turn a rough paper idea into a reviewed, user-approved research proposal. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — goal, relevant file paths, constraints. Never say "as discussed".
- One paper, one folder: pick a slug up front; all paper artifacts live in `docs/paper/<slug>/`.
- Academic integrity is non-negotiable: no fabricated data, results, or citations. Anything unknown is reported as unknown.
- Web research degrades gracefully: if the search backend is unavailable or quota-exhausted, query publisher APIs directly (arXiv, ACL Anthology, Crossref, DBLP, Semantic Scholar) via WebFetch/curl.
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language; the paper's language follows the venue/degree requirement.

## Pipeline

1. **Setup — confirm with the user**: paper type (journal / conference / degree thesis), target venue or school requirements, language, timeline. Pick the slug → `docs/paper/<slug>/`.
2. **Scout — dispatch `researcher`**
   Field state of the art, active groups, recent trends, candidate gaps → `docs/paper/<slug>/literature/scouting.md`. This is fast reconnaissance to position the idea, not a full survey (that is `/paper-litreview`).
3. **Proposal — dispatch `planner`**
   Pass the idea + scouting report + venue/degree requirements. Output `docs/paper/<slug>/proposal.md`: research questions (specific and answerable), hypotheses, method & experiment design (data, baselines, metrics), expected contributions — each mapped to how it will be validated, related-work positioning, work plan with milestones, risks.
4. **Review — dispatch `reviewer`**
   Pass the proposal path. Focus: novelty against the scouting report, feasibility (data, compute, skills, time), overclaiming, method validity.
5. **Fix — dispatch `executor`** for P0/P1 issues; max 3 rounds. If the review traced an issue to a factual error in `scouting.md`, fixing that record is in scope — otherwise the error survives into the literature review.
6. **GATE — user approves the proposal** (AskUserQuestion: approve / adjust).
7. **Deliver**: proposal path + summary; suggest the next step (`/paper-litreview`, or `/paper-experiment` to start designing experiments).
