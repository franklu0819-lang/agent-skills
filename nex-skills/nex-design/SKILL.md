---
name: nex-design
description: "Two-stage design: three distinct visual directions explored in parallel for the user to pick, then the chosen direction developed into a hi-fi interactive prototype. Deliverable is design confirmation — visual language and interaction flow — NOT development: no production wiring, no real data, no API integration. Use when the user asks for a page design, UI mockup, prototype, interaction-flow check, or visual exploration before development starts. Also triggered as /nex-design."
---

# Design workflow (explore → hi-fi → confirm)

Two stages with a user gate between them: first pick a visual direction, then develop it into a confirmable prototype. This is a design gate before development — the deliverable is the confirmed design, not product code. Track progress with TodoWrite.

## Hard boundaries (enforced in every dispatch)

- **Prototype only**: static or lightly interactive (click-through navigation, hover states, realistic placeholder content). No real data fetching, no API/state wiring, no persistence, no error handling of real services.
- **Isolated sandbox**: build under `docs/develop/design/<slug>/` (e.g. standalone HTML files or sandbox routes that ship nowhere) — never modify production source files. Prototypes are disposable; confirmed designs are rebuilt properly by `/nex-dev`.
- **Design system**: Stage A may explore freely; Stage B must reconcile the chosen direction with the project's existing design conventions (tokens, component styles) where they exist.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — goal, spec path, sandbox path, design requirements, direction choice (Stage B), and the no-development constraint above. Never say "as discussed".
- Subagent concurrency follows the user-level AGENTS.md cap: at most 3 simultaneously; batch beyond that.
- Communicate with the user in the user's language.

## Pipeline

### Stage A — visual direction exploration

1. **Brief — main agent frames three directions** (no dispatch)
   From the request + spec: define 3 distinct visual directions (e.g. A: minimal/utilitarian, B: bold/editorial, C: warm/approachable — grounded in the product's audience and any existing brand), each with a one-paragraph rationale: typography stance, color mood, density, component shape language.
2. **Build boards — dispatch `executor` × 3 in parallel** (within the concurrency cap)
   Each direction becomes a low-fi style board in the sandbox: one screen showing typography scale, color palette, buttons/inputs/cards, and one representative content section — enough to *feel* the direction, not a full page. Render each to a PNG under `docs/develop/design/<slug>/stage-a/`.
3. **GATE — user picks a direction** (AskUserQuestion with the three board paths)
   User may mix ("B's palette with A's density") — record the remix and hand it to Stage B as the chosen direction. Max 1 rebuild round if all three miss; then report.

### Stage B — hi-fi prototype & acceptance

4. **Hi-fi prototype — dispatch `executor`**
   Develop the chosen direction into a full hi-fi interactive prototype in the sandbox: all screens of the flow, click-through navigation, designed states (empty/loading/error/success as the spec requires). Reconcile with existing design conventions; any conflict between direction and conventions is surfaced in the delivery note, not silently resolved. Render every screen to PNGs under `docs/develop/design/<slug>/stage-b/`.
5. **Visual & interaction acceptance — dispatch `vision`**
   Pass the Stage B screenshot paths + the request/spec + the designed state list. vision judges visual quality (layout, integrity, readability) and interaction logic (flow vs the spec's journey, state coverage, affordances) per its contract.
6. **Design-system consistency — dispatch `reviewer`**
   Pass the sandbox path + the chosen direction + any existing design-convention docs. Checks: does the prototype honor the project's design tokens/component styles where they exist; is the visual language internally consistent across screens; plus the standing development-creep check (real API calls, production files touched, state management added). No code-quality review (nothing production-bound exists yet).
7. **Fix loop — dispatch `executor`** with vision + reviewer issue lists (design-fidelity fixes only); re-render, re-check; max 3 rounds, then report what remains.
8. **GATE — user confirms the design** (AskUserQuestion: approve / adjust; adjustments loop back to step 4 within budget)
9. **Deliver**
   Chosen direction + rationale, confirmed design summary, final screenshot paths, sandbox path. State explicitly: the prototype is throwaway; the confirmed design (visual language + interaction flow) is implemented properly by `/nex-dev` (which consumes the spec and design artifacts, not the sandbox code).
