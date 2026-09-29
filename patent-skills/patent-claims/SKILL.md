---
name: patent-claims
description: "Claim drafting workflow: planner designs the claim architecture (subject-matter types, independent/dependent layering, fallback positions against the prior-art chart, design-around resistance) → user approves the layout at a gate → executor drafts the claim set → reviewer checks clarity, antecedent basis, and support. Use for 权利要求撰写, 独权从权布局, claim set drafting, turning a disclosure into claims, or stress-testing claims against prior art. Also triggered as /patent-claims."
---

# Claim drafting workflow

Turn an approved disclosure (and prior-art chart, if any) into a layered, reviewed claim set. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — disclosure path, prior-art paths, layout, output paths, constraints. Never say "as discussed".
- One case, one folder: reuse the case's existing folder if there is one; otherwise default to `patent<NNN>/` — NNN is a 3-digit zero-padded sequence: scan the workspace for existing `patent*` folders and use max+1 (first case = `patent001`); the user naming another location wins. Pipeline paths below are relative to the case folder.
- Claim scope is a business decision dressed as a drafting exercise: the layout gate (step 3) is where the user decides how wide to reach and how much to keep in reserve — never trade scope away silently while drafting.
- No feature may appear in a claim that the disclosure's embodiments cannot support.
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language; claims follow the target jurisdiction's language (default Chinese).

## Pipeline

1. **Inputs**: locate `disclosure.md` and, if run, `prior-art/report.md` + `prior-art/claim-chart.md`. If the disclosure does not exist, ask the user for the technical solution directly. If the target jurisdiction is not recorded anywhere in the case, confirm it with the user now — it decides the two-part form, and which subject-matter categories (e.g. storage medium / program product) are available.
2. **Layout — dispatch `planner`** → `claims/claims-layout.md`
   Subject-matter mix (method / apparatus / system / storage medium — each type protects against a different infringer); the independent claim's necessary-feature set (as broad as the embodiments support); the dependent-claim fallback ladder (each rung answering a specific reference in the chart); design-around resistance notes; and a one-line purpose for every claim.
3. **GATE — user approves the layout** (AskUserQuestion: approve / adjust). This fixes the protection scope — renegotiating it after drafting is expensive.
4. **Draft — dispatch `executor`** → `claims/claims.md`
   Each independent claim carries the full necessary-feature set from the approved layout; each dependent claim adds exactly one further limitation over the claim it depends on. Two-part form (前序部分 + 特征部分, "其特征在于") is the default for improvement-type inventions; a single-part claim is acceptable for pioneering inventions or forms unfit for the two-part style, with a one-line reason noted. Proper antecedent basis (every "所述X" has an earlier introduction); single-sentence, single-meaning drafting; no fuzzy quantifiers (约 / 大约 / 等) unless technically essential.
5. **Review — dispatch `reviewer`**
   Focus: clarity; antecedent basis; every independent claim complete in its essential features and only one independent claim per subject-matter category; no claim referring to the description or drawings (no "如图1所示"); dependency graph correct; every claim supported by the disclosure's embodiments; unity of invention.
6. **Fix — dispatch `executor`**; max 3 rounds. If P0s remain after round 3, stop and report the open issues to the user.
7. **Deliver**: claim set path + scope summary; suggest the next step (`/patent-draft`).
