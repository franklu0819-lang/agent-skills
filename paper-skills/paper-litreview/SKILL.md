---
name: paper-litreview
description: "Systematic literature review via multi-query search and snowballing; produces a topic-clustered narrative review, citation matrix, and gap analysis, with every citation verified real and reachable. Use for 文献综述, related-work sections, surveying prior art, or building the reference pool for a paper or thesis. Also triggered as /paper-litreview."
---

# Literature review workflow

Build a verifiable literature review for a paper or thesis. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — goal, topic scope, file paths, constraints. Never say "as discussed".
- One paper, one folder: reuse the existing `paper<NNN>/` if the paper exists; otherwise create the next `paper<NNN>` folder (3-digit zero-padded, max+1).
- Citation integrity is the core risk of LLM-assisted reviews: every reference in the final review must resolve to a real, reachable source. No placeholder or "plausible-looking" references, ever.
- Web research degrades gracefully: if the search backend is unavailable or quota-exhausted, query publisher APIs directly (arXiv, ACL Anthology, Crossref, DBLP, Semantic Scholar) via WebFetch/curl — they need no search quota.
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language; the review's language follows the paper's.

## Pipeline

1. **Setup — confirm scope with the user**: topic, time window, must-cover venues, language. If a proposal exists at `paper<NNN>/proposal.md`, align the review with its research questions.
2. **Search — dispatch `researcher`** (parallel dispatches per theme cluster)
   If `literature/scouting.md` exists (from `/paper-proposal`), use its papers as seeds; otherwise snowball from seed papers the user names. Multi-keyword queries plus forward/backward snowballing. Collect candidates with title / authors / year / venue / DOI-or-URL / one-line takeaway → `paper<NNN>/literature/candidates.md`, ending with a "Corrections to scouting.md" section for any seed record that does not check out — fast scout reports contain errors, and every downstream doc inherits them.
3. **Synthesize — dispatch `executor`**
   Dedupe, cluster by theme, then write `paper<NNN>/literature/review.md` (narrative per cluster: evolution, comparison, disagreements) and `matrix.md` (paper × method / data / result / limitation table). End with a gap section mapping each gap to the paper's research questions.
4. **Verify — dispatch `reviewer`**
   Check EVERY citation: DOI/URL resolves, title-authors-year-venue match what the text claims. Flag any citation that cannot be verified — treat it as fabricated until proven otherwise. Also review cluster logic and coverage balance.
5. **Fix — dispatch `executor`**: remove or repair unverified citations first, then P0/P1 issues; max 3 rounds. The fix is authorized to apply the named corrections back into `scouting.md` so the error stops propagating.
6. **GATE — user approves the review** (AskUserQuestion: approve / adjust).
7. **Deliver**: review + matrix paths; suggest the next step (`/paper-draft`).
