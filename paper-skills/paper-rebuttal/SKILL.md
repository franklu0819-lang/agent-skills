---
name: paper-rebuttal
description: "Point-by-point response to peer review: every reviewer comment mapped to a response strategy (extra experiments and disagreements confirmed with the user first), response letter drafted and promised manuscript edits applied. Use when responding to peer review comments, 审稿意见回复, writing a rebuttal/response letter, or preparing a revised resubmission. Also triggered as /paper-rebuttal."
---

# Rebuttal workflow

Turn received review comments into a verified point-by-point response and a revised manuscript. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — comment list, manuscript paths, strategy, constraints. Never say "as discussed".
- One paper, one folder: rebuttal artifacts live in `paper<NNN>/submission/`.
- Never promise in the letter what the manuscript does not contain; never fabricate a new experiment or number to appease a reviewer — if evidence is missing, say what will be done and what cannot.
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language; the letter's language follows the venue.

## Pipeline

1. **Inputs**: collect the review comments from the user (paste or file) and save them verbatim to `paper<NNN>/submission/reviews-received.md`. Locate the current manuscript.
2. **Strategy — dispatch `planner`** → `paper<NNN>/submission/rebuttal-plan.md`
   For each comment, numbered per reviewer: classify it (fatal flaw / major / minor / misunderstanding), pick a strategy (new experiment, clarification, text revision, polite disagreement backed by evidence), list the manuscript edits it requires, and estimate effort.
3. **GATE — user confirms the strategy** (AskUserQuestion): especially any extra experiments to run and any polite disagreements.
4. **Draft — dispatch `executor`**
   Write `paper<NNN>/submission/response-letter.md` — point-by-point: quote the comment, respond, name exactly where the manuscript changed. Apply all promised edits to the manuscript.
5. **Verify — dispatch `reviewer`**
   Every comment has a response; every promised edit is actually present in the revised manuscript (diff check); tone stays professional; no overpromising.
6. **Fix — dispatch `executor`**; max 3 rounds.
7. **Deliver**: response letter + revised manuscript paths + summary of what each reviewer received.
