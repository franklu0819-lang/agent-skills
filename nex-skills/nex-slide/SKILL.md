---
name: nex-slide
description: "Slide production workflow: gathers source material from documents, websites, images, and videos → plans the deck outline → executor builds the PPTX per fixed brand style (red #dc3545 + white theme, 【星网天合】 brand mark in the top-right of every slide) → judge runs per-page visual acceptance → fix loop → user confirms. Use when the user wants a presentation/PPT/slides built from existing material. Also triggered as /nex-slide."
---

# Slide production workflow

Turn source material (docs / web pages / images / videos) into a branded PPTX. The brand style is fixed: red + white primary palette with the 【星网天合】 mark top-right on every slide. Track progress with TodoWrite.

## Brand style (fixed — do not re-extract)

- **Palette**: brand red `#dc3545` (extracted 2026-09-01 from https://www.nexhome.cn CSS — the site's sole red token, used on all red buttons; the site's "primary" token is blue, red is the brand accent) + white as the base. Red carries emphasis, titles, key data; white carries the canvas. Use this value as-is; do not re-extract from the site.
- **Brand mark**: 【星网天合】 fixed in the top-right corner of every slide (including cover and closing).

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — material paths, deck outline, brand style block above (copy it into the dispatch verbatim), output path. Never say "as discussed".
- Use the built-in `pptx` skill (document-skills plugin) for building; use the built-in `judge` agent for per-page visual acceptance — it exists for exactly this deliverable type.
- Persistence is decided here, not by the agents: the deck + per-run assets file to `docs/business/<slug>-slides/` unless the user names another location.
- Communicate with the user in the user's language.

## Pipeline

1. **Material gathering — main agent + dispatch `researcher` as needed**
   Collect from what the user named: local documents (Read), web pages (WebFetch — cite the URL per extracted fact), images (Read the image files; describe what they show), videos (extract keyframes or read any transcript; otherwise note the gap honestly). Produce a material digest: key points, data, quotable statements, each with its source. Ask the user for missing essentials rather than inventing content.
2. **Outline gate — main agent presents the outline** (AskUserQuestion: approve / adjust)
   Slide-by-slide outline: title, 3-5 bullets or one chart/table per slide, where each image goes, target slide count.
3. **Build — dispatch `executor`**
   Pass the material digest + approved outline + the Brand style block + output path. executor uses the `pptx` skill to build the deck; every slide must follow the palette and carry the 【星网天合】 mark top-right. Real content from the digest only — no invented data; charts must reflect the digest's numbers exactly.
4. **Visual acceptance — dispatch the built-in `judge` agent**
   Render pages to PNG, pass the image paths + the outline + brand requirements. judge verdicts per page: layout, palette compliance (red+white, no off-theme colors), brand mark present top-right, chart correctness, text fit.
5. **Fix loop — dispatch `executor`** with judge's failing pages; max 3 rounds, then report what remains.
6. **GATE — user flips through the deck** (approve / request changes; changes loop back to step 3 within budget)
7. **Deliver & record**
   Deliver the PPTX path + per-slide thumbnails; file a build record (source material, outline, brand red used, judge summary) alongside the deck.
