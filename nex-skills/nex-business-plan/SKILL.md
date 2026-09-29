---
name: nex-business-plan
description: "Business plan: parallel market research and data baseline, synthesized into a plan, then adversarial fact-check and a revised final. Use when the user wants a business plan, a go/no-go evaluation of a product idea, monetization strategy, or market-entry analysis. Also triggered as /nex-business-plan."
---

# Business plan workflow

Produce an evidence-backed business plan for a product or idea. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — goal, relevant file paths, constraints. Never say "as discussed".
- One plan, one folder: pick a slug up front; research, baseline, and the plan all live in `docs/business/<slug>/`.
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language.

## Pipeline

1. **Research + data, in parallel**
   - `researcher`: market landscape, competitors, target users, pricing precedents → report to `docs/business/<slug>/research.md`.
   - `executor`: only if real data exists to ground the plan (existing product metrics, datasets) → report to `docs/business/<slug>/baseline.md`; otherwise skip and note the gap.
2. **Synthesize — dispatch `planner`**
   Pass both report paths + the original idea, and name the output path. Have planner file the business plan to `docs/business/<slug>/plan.md` covering problem & market, target users, offering, monetization, go-to-market, key assumptions, risks, phased milestones with verifiable criteria.
3. **GATE — direction check**
   Present the plan's key bets and assumptions to the user (AskUserQuestion: proceed / adjust). If direction is off, send adjustments back to planner.
4. **Fact-check — dispatch `reviewer`**
   Pass the plan path + research report paths. Focus: factual accuracy, unsupported assumptions, overpromising.
5. **Revise — dispatch `executor`** to fix P0/P1 issues in the plan file; max 3 fix rounds.
6. **Deliver**: conclusions + top remaining risks to the user; link the final plan path.
