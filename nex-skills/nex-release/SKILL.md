---
name: nex-release
description: "Release workflow: executor prepares the release (version bump, changelog, green build + tests + E2E pass driven by chrome-devtools) without deploying → reviewer runs a release gate (E2E green, migrations, env vars, secrets, rollback path) → user approves → executor ships → smoke check → PSI gate for web apps (Performance ≥ 90, Accessibility/Best Practices/SEO = 100). Use when the user wants to release, deploy, or publish a version. Also triggered as /nex-release."
---

# Release workflow

Prepare → gate → user approval → ship → smoke → PSI gate (web apps). Never deploy before the approval gate; for web apps the release is not done below the PSI bar. Track progress with TodoWrite.

## Dispatch rules

- Sub-agents start fresh: every dispatch must be self-contained — version target, changes included, repo release conventions. Never say "as discussed".
- Communicate with the user in the user's language.

## Pipeline

1. **Prepare — dispatch `executor`**
   Version bump per repo convention, changelog entry, full build + tests green, and an E2E pass green. E2E defaults to chrome-devtools MCP: open the running app in Chrome, walk the key user flows, verify rendered behavior (not just status codes), and check console errors and failed network requests. If the repo has its own E2E suite, run it as well — both must be green. Report which flows were exercised and which were not; never silently skip. Explicitly: NO deploy yet. Report the checklist.
2. **Release gate — dispatch `reviewer`**
   Pass the release diff + changelog + E2E run results. Gate list: E2E not green, key flows not exercised, or results not reported; missing migrations, new env vars/secrets undocumented, breaking changes unflagged, rollback path unstated.
3. **Fix loop — dispatch `executor`** for P0/P1; max 3 rounds.
4. **GATE — user approves the release**
   Present version, changes, E2E status, risks, rollback plan (AskUserQuestion: ship / hold).
5. **Ship — dispatch `executor`**
   Deploy/publish strictly per the repo's documented release process. If none is documented, stop and ask the user for the procedure — never improvise a deploy.
6. **Smoke — dispatch `executor`** (or run directly if trivial): verify the deployment is alive — health check + one key flow.
7. **PSI gate (web apps) — dispatch `executor`**
   Only when the release target is a web application. Run a PageSpeed Insights / Lighthouse audit against the **deployed** URL: chrome-devtools `lighthouse_audit` covers Accessibility / Best Practices / SEO; for the Performance score use the PSI API (`curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=<url>"`) or `npx lighthouse <url> --output=json --chrome-flags="--headless"` when the URL is not publicly reachable. Pass bar: **Performance ≥ 90, and Accessibility / Best Practices / SEO = 100 each**. Record all category scores plus the failing audit items.
   On failure treat every miss as P0: dispatch `executor` to fix the flagged items, redeploy per the release process, re-audit — max 3 rounds. Still below bar → stop and escalate to the user (keep fixing / roll back / accept with justification). The release is not done below the bar.
8. **Deliver & record**
   File a release record (version, changes, E2E results, reviewer verdict, smoke results, PSI scores) to `docs/develop/release/<version>/record.md`, then deliver: release notes + smoke results + PSI scores + version identifier.
