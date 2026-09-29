---
name: patent-oa
description: "Office-action response workflow: planner maps every OA objection and cited reference to a response strategy (argue / amend / delete / divisional) → user confirms the strategy at a gate, especially scope concessions → executor drafts the observation letter and amendment pages → reviewer verifies every objection is answered and every amendment stays within the original disclosure. Use for 答复审查意见, OA答复, 意见陈述书, overcoming 新颖性/创造性/客体 rejections, or handling a received 审查意见通知书. Also triggered as /patent-oa."
---

# Office-action response workflow

Turn a received office action into a verified, point-by-point response with amendments. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — the OA text (or its file path), the current application and claim file paths, the confirmed strategy, output paths. Never say "as discussed".
- One case, one folder: reuse the case's existing folder if there is one; otherwise default to `patent<NNN>/` — NNN is a 3-digit zero-padded sequence: scan the workspace for existing `patent*` folders and use max+1 (first case = `patent001`); the user naming another location wins. Pipeline paths below are relative to the case folder; each OA round gets its own subfolder `oa/<n>/`.
- Two hard constraints: every amendment must have basis in what the application as filed records (explicit text, or content directly and unambiguously derivable from it), and every argument must stand on the application's own content or verifiable public knowledge — no invented technical effects to argue inventiveness.
- Never misquote the examiner or a cited reference; rebut what they actually say.
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language; the response follows the jurisdiction's language.
- Deadline watching stays with the user/attorney — always restate the deadline printed in the OA itself, never a self-computed one.

## Pipeline

1. **Inputs**: collect the office action verbatim (paste or file) → `oa/<n>/oa-received.md` (n = the round number; continue the existing sequence if earlier rounds exist). Locate the current claims — for round ≥2 that is the previous round's `oa/<n-1>/claims-amended.md`, not the original `claims/claims.md`. Ask the user for the as-filed text if the attorney's filed version may differ from the local drafts; the as-filed text is the sole authority for amendment basis (the OA's own quotations are a good witness of it).
2. **Strategy — dispatch `planner`** → `oa/<n>/response-plan.md`
   Per objection: classify it. CN default taxonomy — eligible-subject-matter A25 / not-a-technical-solution A2.2 (the usual attack on software/algorithm cases; strategy is argue technical character or amend in technical features), novelty/inventiveness A22, insufficiency A26.3, lack of support or clarity A26.4, missing essential features R20.2, unity A31, amendment beyond original scope A33, formal issues. For a non-CN office action, build the jurisdiction's equivalent mapping first (e.g. US 101/102/103/112). For each cited reference: what it actually discloses vs. the distinguishing features. Pick a strategy per objection — argue (three-step rebuttal), amend (merge a dependent claim / add a feature / narrow a range), delete subject matter, or file a divisional — and price every concession in lost scope.
3. **GATE — user confirms the strategy** (AskUserQuestion): especially any claim-narrowing amendment and any abandoned subject matter.
4. **Draft — dispatch `executor`**
   `oa/<n>/amendments.md`: per amendment — original text → amended text → its verbatim basis quote plus location in the as-filed text (section/paragraph; line numbers of the local file if that is what the user works from — official page/line mapping is the attorney's job on the filing version). `oa/<n>/claims-amended.md`: the amended claim set, clean version followed by a marked-up version (strikethrough for deletions, underline for additions) — this file becomes the current claims for the next round. `oa/<n>/observation.md`: the point-by-point response letter — quote each objection, state what was amended where, then argue; arguments confined to the application's content and verifiable common knowledge.
5. **Verify — dispatch `reviewer`**
   Every objection has a response; every amendment traced to an as-filed basis quote; amended claims still clear and supported; the letter's characterization of each cited reference matches the record; tone professional, no examiner-bashing.
6. **Fix — dispatch `executor`**; max 3 rounds. If P0s remain after round 3, stop and report the open issues to the user.
7. **Deliver**: response + amendments + amended claims paths; restate the OA's printed deadline and hand the actual filing to the user/attorney.
