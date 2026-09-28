# Search-channel status (tested fallbacks)

Last field-tested: 2026-09-27 (patent01 round). This file is a living snapshot — channels rot; when a round finds something changed, update this file with the date. The rule that never changes: a blocked channel goes into the report's limitations section, never silently dropped.

## Reachable (primary workhorses)

| Channel | What it gives | How / notes |
|---|---|---|
| Google Patents per-patent pages | CN/US/EP/WO 著录、全文、法律状态、引用链 | Search UI & XHR API time out; per-patent pages reachable via server-side readers (web_reader / Exa / r.jina.ai). Live index lags recent US grants (~post-2026-06 B-numbers 404) — fall back to an auxiliary source for existence, keep the GP URL as canonical |
| Justia (justia.com) | US full-text Boolean search | Good discovery channel when GP search is down |
| Exa (web_search_exa / web_fetch_exa) | Semantic patent & paper discovery, server-side fetch | Strong for "concept-level" queries where Boolean fails |
| PatSnap Eureka pages | CN patent 著录 + abstract, reachable without login | Chinese applicant names verifiable here (caught a one-character applicant-name error that拼音-identical English masked) |
| X技术网 (xjishu.com) | Re-hosted CNIPA publication text incl. claims mirrors | Passes its human-check then serves full text. ⚠ Verification-wall 200 responses are identical for fabricated application numbers — a 200 proves nothing; existence needs a second channel, publication dates need official confirmation before filing |
| arXiv API (export.arxiv.org) | Versions, dates, authors, abstracts | Direct connection more reliable than via proxy; `id_list=` batches many IDs in one call — use it to bulk-backfill authors before publishing |
| ACL Anthology | Venue metadata + PDFs | Landing page carries volume/month/location — quote it rather than "conference, date unchecked" |
| r.jina.ai | Server-side fetch fallback | Reachable when local curl is blocked; distinguishes local-network issues from dead links |
| Conference sites (CIDR, USENIX…) | Accepted-paper lists | Direct fetch works |

## Blocked / limited (record as limitation, don't grind on)

Espacenet (HTTP 403 to automated access) · WIPO PatentScope (JS app; server fetch returns loader placeholder) · Google Patents search UI/XHR (timeout) · CNIPA portal / incoPat / 智慧芽 (login-walled — best-effort via mirrors, never guess contents) · 知网 (login wall) · DBLP (anti-bot) · OpenReview (403) · Google Scholar (connection failure) · Semantic Scholar / OpenAlex (429 rate limits) · Tavily (quota).

## Environment notes

- Non-`.cn` curl requests go through the local proxy `http://127.0.0.1:7890` (`.cn` direct); arXiv API often works better direct.
- URL triage during verification: dead link / timeout (retry once via another channel) / content mismatch are three different findings — only content mismatch implicates the citation's truth.
- Discrimination test for mirror sites: request a fabricated ID; if the mirror returns the same page shape, its 200s carry no existence evidence.
