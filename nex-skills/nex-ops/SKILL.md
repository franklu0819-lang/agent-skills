---
name: nex-ops
description: "Ops/incident handling: root-cause diagnosis with an evidence chain, user picks the fix, minimal fix applied and verified, incident report filed. Use for production incidents, abnormal metrics, performance degradation, or maintenance tasks. Also triggered as /nex-ops."
---

# Ops / incident workflow

Diagnose with evidence → user picks the fix → minimal repair → verify → record. Never apply a fix before the user gate. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — incident description, symptoms, where to look, how to reproduce safely. Never say "as discussed".
- Safety first: diagnosing production must not make things worse; read-only probes unless the user authorizes otherwise.
- Communicate with the user in the user's language.

## Pipeline

1. **Diagnose — dispatch `researcher`**
   Pass the incident description + symptoms + pointers (logs, metrics, suspect commits). researcher returns an evidence chain + fix options with touch points and risks. If inconclusive, researcher reports what was ruled out + next probes.
2. **GATE — user picks the fix** (AskUserQuestion over researcher's options, including "gather more data first").
3. **Fix — dispatch `executor`**
   Apply the chosen fix minimally; verify with tests or a reproduction.
4. **Verify — dispatch `reviewer`**: fix correctness + no new risks introduced.
5. **Record** — write the incident report yourself (main agent) to `docs/develop/ops/YYYY-MM-DD-incident-<slug>.md`: timeline, root cause (researcher's evidence chain), fix applied (executor's changes), verification (reviewer's verdict), follow-ups.
6. **Deliver**: summary + report path + suggested preventive actions.
