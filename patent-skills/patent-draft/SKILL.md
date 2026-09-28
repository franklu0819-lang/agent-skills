---
name: patent-draft
description: "Patent application drafting workflow: executor drafts the full specification (technical field, background, summary mirroring the claims, detailed embodiments covering every claim feature and variant), abstract, and figure notes → reviewer checks term consistency, claim support, and embodiment coverage → user-approved filing draft. Use for 专利申请文件撰写, 说明书撰写, 撰写专利申请, assembling the CN/US/PCT application package around an approved claim set. Also triggered as /patent-draft."
---

# Patent application drafting workflow

Assemble a complete, internally consistent application draft around the approved claim set. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — claims path, disclosure path, output paths, constraints. Never say "as discussed".
- One case, one folder: reuse the case's existing folder if there is one; otherwise default to `docs/business/patent/<case-slug>/` (a project AGENTS.md or the user naming another location wins). Pipeline paths below are relative to the case folder.
- The specification is the only reservoir later amendments may draw from: every claim feature needs embodiments covering its full claimed range and its variants now — after filing, anything not written can no longer be added.
- Terminology discipline: one concept, one term, everywhere — claim wording appears in the specification verbatim.
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language; the application follows the target jurisdiction's language (default Chinese).

## Pipeline

1. **Inputs**: locate `claims/claims.md` and `disclosure.md` (a claim set is required — if missing, suggest `/patent-claims` first). Confirm the target jurisdiction's drafting conventions: for CN, the standard sections 技术领域 / 背景技术 / 发明内容 / 附图说明 / 具体实施方式; for any other jurisdiction, first dispatch `researcher` to fetch the official drafting rules (e.g. US MPEP §608 / PCT Guide) and follow those instead.
2. **Draft — dispatch `executor`** → `application/`
   `description.md`: 技术领域; 背景技术 grounded in `prior-art/report.md` if it exists (factual defects, no disparagement, and never disclosing the invention itself); 发明内容 mirroring every claim verbatim plus its effects; 附图说明; 具体实施方式 with at least one complete embodiment per independent claim, variant/alternative embodiments for every feature, and consistent reference signs. `abstract.md` (≤300 characters, no commercial puffery). `figures-notes.md`: the figure list with what each drawing must show, and the designated 摘要附图 (abstract figure) chosen from them with a reason — the actual drawings stay with the user/designer. `claims.md`: a verbatim copy of the approved claim set, completing the package.
3. **Review — dispatch `reviewer`**
   Focus: term consistency across all documents; every claim supported and appearing verbatim; every dependent-claim feature covered by an embodiment; figure references consistent; abstract within its length limit and matching the designated abstract figure; no fuzzy wording; background free of the invention's own content.
4. **Fix — dispatch `executor`**; max 3 rounds. If P0s remain after round 3, stop and report the open issues to the user.
5. **GATE — user approves the filing draft** (AskUserQuestion: approve / adjust).
6. **Deliver**: file manifest under `application/` (description, abstract, figure notes, claims copy); remind the user the final package needs a patent attorney's review, and the actual filing stays with them — never submit on their behalf.
