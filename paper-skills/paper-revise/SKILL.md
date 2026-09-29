---
name: paper-revise
description: "Paper revision workflow: reviewer simulates peer review (novelty, method soundness, clarity, presentation) → user picks which issues to fix at a gate → executor applies revisions → reviewer verifies each chosen issue is actually resolved. Use for polishing a draft before submission, 论文修改, incorporating advisor feedback, or raising a paper to a target venue's bar. Also triggered as /paper-revise."
---

# Paper revision workflow

Run a simulated peer review over an existing draft, then fix what the user chooses. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — draft paths, revision goal, issue list, constraints. Never say "as discussed".
- One paper, one folder: reviews are filed to `paper<NNN>/reviews/`; the draft is edited in place.
- Revision strengthens what is there — it must not fabricate evidence, inflate claims, or massage numbers to look better.
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language.

## Pipeline

1. **Inputs**: locate the draft (files under `paper<NNN>/draft/` or paths from the user). Confirm the revision goal with the user: general polish, addressing advisor comments, or aiming at a specific venue's bar. If there are advisor/reviewer comments, save them verbatim to `paper<NNN>/reviews/feedback-received.md`.
2. **Simulated review — dispatch `reviewer`** → `paper<NNN>/reviews/YYYY-MM-DD-review.md`
   Review as a skeptical peer reviewer across four dimensions — novelty, method soundness, clarity, presentation. Output numbered issues, each with severity (P0 fatal / P1 major / P2 minor), location, and a concrete fix suggestion; end with a per-dimension verdict. Merge any advisor comments into the same numbered list.
3. **GATE — user picks priorities** (AskUserQuestion, multiSelect): fix now / defer / disagree-with-reason.
4. **Revise — dispatch `executor`**: apply the chosen fixes in place; append a change log to the review file (issue → what changed → where).
5. **Verify — dispatch `reviewer`**: confirm each chosen issue is actually resolved and no new issues were introduced; update the change log verdicts.
6. **Deliver**: revised draft path + residual (deferred) issue list; suggest the next step (`/paper-submit`).
