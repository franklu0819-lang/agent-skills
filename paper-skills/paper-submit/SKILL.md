---
name: paper-submit
description: "Submission preparation workflow: researcher fetches the venue's author guide → executor builds the formatted manuscript (venue LaTeX template or docx, unified citation style, integrated figures) plus a cover letter → reviewer runs the pre-submission checklist (limits, anonymization, reference closure, declarations) → user approves the package. Use when preparing a paper for submission, 投稿格式化, fitting a journal/conference template, or writing a cover letter. Also triggered as /paper-submit."
---

# Submission preparation workflow

Assemble a venue-compliant submission package without actually submitting. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — draft paths, venue requirements, output paths, constraints. Never say "as discussed".
- One paper, one folder: the package lives in `docs/paper/<slug>/submission/`.
- The reference list is built only from verified sources; formatting must not silently drop or rename references.
- Web research degrades gracefully: if the search backend is unavailable or quota-exhausted, fetch venue pages directly (publisher site, arXiv, ACL Anthology) via WebFetch/curl.
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language; the manuscript's language follows the venue.

## Pipeline

1. **Setup**: confirm the target venue with the user. If the author guide is not at hand, dispatch `researcher` to fetch it: template, citation style, word/page limits, figure limits, anonymity (single/double-blind), declaration requirements (ethics, funding, AI-use policy).
2. **Build — dispatch `executor`** into `docs/paper/<slug>/submission/`
   Merge the draft into the venue LaTeX template (or produce docx per the guide); unify the citation style (GB/T 7714 / APA / IEEE / venue-specific); integrate and renumber figures/tables; generate the reference list from the verified literature matrix only; write `cover-letter.md` (contributions, fit to venue, originality/no-overlap statement). Use the document-skills pdf/docx skills when a rendered document is needed.
3. **Checklist — dispatch `reviewer`** → `docs/paper/<slug>/reviews/submission-checklist.md`
   Template compliance; length and figure limits; blind-review anonymization; figure readability and numbering; reference closure — every in-text citation appears in the reference list and vice versa; required declarations present; complete file manifest.
4. **Fix — dispatch `executor`**; max 3 rounds.
5. **GATE — user approves the package for submission** (AskUserQuestion: approve / adjust).
6. **Deliver**: package paths + manifest. The actual portal upload stays with the user — never submit on their behalf.
