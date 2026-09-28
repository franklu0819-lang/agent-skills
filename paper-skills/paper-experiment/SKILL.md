---
name: paper-experiment
description: "Paper experiment workflow: planner designs the experiments (hypotheses, variables, baselines, datasets, metrics, ablations, stats plan) → user approves → executor implements reproducible config-driven experiment code and runs it → data-analyst analyzes results into publication-ready figures/tables → reviewer checks the evidence honestly supports the claims. Use for designing, running, or analyzing paper experiments, 实验设计/跑实验/结果分析, or turning results into paper figures. Also triggered as /paper-experiment."
---

# Paper experiment workflow

Design, run, and analyze the experiments that back a paper's claims. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — research questions, experiment design, code/data paths, constraints. Never say "as discussed".
- One paper, one folder: experiment records and results live in `docs/paper/<slug>/experiments/`; experiment code lives in the project repo (e.g. `experiments/`, `src/`), not in docs.
- Reproducibility is part of the result: config-driven runs, fixed seeds, recorded environments, saved raw outputs. A result that cannot be rerun is not a result.
- Honesty over beauty: no cherry-picked runs, no silently dropped conditions, no axis tricks. Negative results are recorded and reported, not hidden.
- Independent steps run in parallel (dispatch in the same message).
- Communicate with the user in the user's language.

## Pipeline

1. **Inputs**: read `docs/paper/<slug>/proposal.md` for the research questions and hypotheses (if missing, ask the user to state the claims the experiments must support). Inventory what already exists: datasets, baseline implementations, compute.
2. **Design — dispatch `planner`** → `docs/paper/<slug>/experiments/design.md`
   Per experiment: which hypothesis it tests; independent/dependent variables; baselines and why they are the right comparison; datasets and splits; metrics with success thresholds; ablations; statistical testing plan; compute/time budget and a prioritized order.
3. **GATE — user approves the design** (AskUserQuestion: approve / adjust).
4. **Implement — dispatch `executor`**
   Build the experiment code in the project repo: config-driven entry points, fixed seeds, pinned/recorded environment, structured raw outputs (JSON/CSV) under `docs/paper/<slug>/experiments/runs/<run-id>/`. Validate the full pipeline with a small smoke run before any full run.
5. **Run — dispatch `executor`**
   Execute runs in the approved order (long jobs in the background). Record per run: config, seed, log, output location. Failed or diverging runs are documented in `runs/README.md`, not deleted.
6. **Analyze — dispatch `data-analyst`** → `docs/paper/<slug>/experiments/analysis/`
   Aggregate runs, apply the statistical plan from the design, produce publication-quality figures and tables — each with a one-line takeaway stating which hypothesis it supports, refutes, or leaves inconclusive.
7. **Review — dispatch `reviewer`**
   Focus: do the results actually support the hypotheses; are figures honest (error bars, scales, all approved conditions shown); does every claimed contribution in the proposal now have evidence or a recorded gap.
8. **Fix — dispatch `executor`**: extend/rerun experiments or fix the analysis; max 3 rounds.
9. **Deliver**: hypothesis-by-hypothesis verdict (supported / refuted / inconclusive) + analysis paths; suggest the next step (`/paper-draft`).
