# ADR-0021: Host the landing page as static files on Vercel

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
WP-24 asks for a landing page. ADR-0001 rules out a hosted server for user data; a marketing page holds no user data, so the question is only where static files live and what they may load. GitHub Pages needs a repo setting changed by hand; Raja's Vercel account is reachable from the build session and is his default host.

## Options

### Option A: One static HTML page in `site/`, deployed to Vercel
- Pros: no build step, no framework, no dependency (ADR-0012 holds); deployable from the session; Raja's usual host.
- Cons: a second place to keep copy in step with the README.
- Price: 0 USD (Vercel Hobby).

### Option B: GitHub Pages from `site/`
- Pros: same repo, same host as the code.
- Cons: Pages must be switched on in repo settings by hand; a deploy workflow adds a third-party action to pin.
- Price: 0 USD.

### Option C: Next.js site
- Pros: Raja's app stack.
- Cons: a package.json, a build, and dependencies for one page.
- Price: 0 USD.

## Decision
Option A. `site/index.html` with inline CSS and a few lines of inline JavaScript (tabs and copy buttons), brand assets copied from `docs/brand/`, and `og.png`. The page loads nothing at runtime except Google Fonts (Inter Tight, Inter, JetBrains Mono, with system fallbacks). No analytics, no cookies, no forms, no tracking. Black and white only (docs/brand/README.md). Tool status on the page follows the README table, which follows the tool ledger (WP-23): a tool shows Tested only with a passing ledger row.

## Non-goals
A custom domain (Raja's call, added in Vercel when bought), a docs site, analytics.

## Consequences
- Gets easier: one HTML file to edit; redeploy is one call.
- Gets harder: README, page and release notes must change together when copy or tool status changes.
- Follow-up tasks: switch a tool to Tested on the page in the same commit as its README tick.

## Implementation plan
- Affected paths: site/, scripts/guardrails.py (site/*.html joins the em dash scan).
- Pattern to follow: copy and claims on the page match README.md.
- Pattern to avoid: any third-party script, tracker or form.

## Verification
- [x] Renders at 1280 px and 390 px with no horizontal scroll, light and dark
- [x] No console errors once hosted
- [x] guardrails pass with site/ scanned

## Revisit when
The page needs more than one screen of docs, or a custom domain is bought.

## More information
