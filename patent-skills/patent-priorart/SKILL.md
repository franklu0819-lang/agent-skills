---
name: patent-priorart
description: "Prior-art search workflow: researcher runs systematic multi-query patent & literature search (classification codes + keywords, snowballing) → executor builds the feature comparison chart and novelty/inventiveness assessment → reviewer verifies every cited reference is real and reachable → user-approved report. Use for 现有技术检索, 专利查新, novelty search, 专利检索分析, deciding whether an idea is patentable, or checking what the claims must distinguish from. Also triggered as /patent-priorart."
---

# Prior-art search workflow

Build a verifiable novelty/inventiveness assessment for a technical solution. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — the technical solution (or disclosure path), search scope, file paths, constraints. Never say "as discussed".
- One case, one folder: reuse the case's existing folder if there is one; otherwise default to `docs/business/patent/<case-slug>/` (a project AGENTS.md or the user naming another location wins). Pipeline paths below are relative to the case folder.
- Citation integrity is the core risk of LLM-assisted searching: every reference must carry a resolvable URL (checked, with access date) — a patent number via Google Patents or Espacenet, a paper via DOI. References with no resolvable URL are treated as unverified. No plausible-looking phantom references, ever.
- The assessment reports what the found references actually disclose — overstating the prior art kills the case as surely as missing it.
- Independent steps run in parallel (dispatch in the same message) — but parallel writers never share one output file.
- Communicate with the user in the user's language; the report's language follows the user's.

## Pipeline

1. **Setup — confirm scope with the user**: the technical solution (from `disclosure.md` if it exists, else the user's description), target jurisdiction, and the expected filing/priority date (the cutoff — only publications predating it count as prior art). Decompose the solution into technical features and save the confirmed decomposition → `prior-art/features.md` (the row axis of everything downstream).
2. **Search — dispatch `researcher`** (parallel dispatches per feature cluster, one output file each)
   Queries in Chinese and English with IPC/CPC classification codes + keywords, across Google Patents and Espacenet (both index CN publications and are resolvable — use them as the canonical mirrors for CN documents); WIPO PatentScope, arXiv, IEEE/ACM as applicable; CNIPA's own portal and 知网 are best-effort only (login walls — never block on them, never guess their contents). Forward/backward snowball from seed documents. Each cluster writes `prior-art/candidates-<cluster>.md`: publication number / applicant / publication date / resolvable URL + access date / the specific passages that matter.
3. **Assess — dispatch `executor`**
   Merge the candidate files, then build `prior-art/claim-chart.md`: each feature from `features.md` × the closest references, citing the exact disclosing passage, each reference tagged with its publication date vs. the cutoff and its role (X — novelty-destroying alone / Y — combinable for inventiveness / A — background only; an E-type conflicting application also compares singly and only for novelty). Then `prior-art/report.md`: novelty (does any single reference disclose all features?), inventiveness (three-step test: closest prior art → distinguishing features → objective technical problem → whether the prior art as a whole gives a teaching/suggestion toward them), and a conclusion — file as-is / strengthen the distinguishing features / drop it — with reasoning.
4. **Verify — dispatch `reviewer`**
   Check EVERY citation: the URL resolves, and the cited passage actually says what the chart claims. Treat any unverifiable citation as fabricated until proven otherwise. Also check the feature decomposition and the three-step reasoning.
5. **Fix — dispatch `executor`**: remove or repair unverified citations first, then P0/P1 issues; max 3 rounds. If P0s remain after round 3, stop and report the open issues to the user.
6. **GATE — user approves the report** (AskUserQuestion: approve / adjust).
7. **Deliver**: report + chart paths; suggest the next step (`/patent-claims` — the chart feeds the fallback ladder).
