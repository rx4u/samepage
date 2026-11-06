# ADR-0001: Choose distribution and hosting

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
samepage must reach Claude Code, claude.ai chat, Cowork and Claude Design. The goal is GitHub stars, which depends on a short install and no account to create. Every hosted component adds cost, auth and a reason not to try it.

## Options

### Option A: No hosting. Claude Code plugin, uploadable skill zip, store template repo
- Pros: zero cost per user; nothing to keep online; one install command per surface; the user owns all data.
- Cons: chat writes depend on the user's connectors; the index needs a GitHub Action in the user's repo.
- Price: 0 USD per month for the maintainer and for users within GitHub free Action minutes.

### Option B: Hosted MCP server that fronts the store
- Pros: one endpoint for every surface; could index and search server-side.
- Cons: auth, hosting, uptime and a privacy story for other people's work data; a stranger must trust the maintainer's server.
- Price: about 5 to 25 USD per month at small scale (Vercel or Fly plus a database), growing with users.

## Decision
Option A. Ship three artifacts per release: the Claude Code plugin (with the skill bundled), `samepage.skill` for upload in claude.ai, and the `store-template` repo.

## Non-goals
Does not decide where the public repo lives (ADR-0013) or its name (ADR-0010).

## Consequences
- Gets easier: trust, cost, launch ("no server, your data in your repo").
- Gets harder: features that need a server (search across stores, team stores).
- Follow-up tasks: WP-11 store Action, WP-15 release packaging.

## Implementation plan
- Affected paths: .claude-plugin/, hooks/, commands/, skills/, store-template/, dist/
- Pattern to follow: every runtime piece runs on the user's machine, in the user's GitHub Actions, or inside Claude through connectors.
- Pattern to avoid: any network call to a maintainer-owned endpoint.
- Config and env changes: none.

## Verification
- [ ] CI check fails if any file references a maintainer-hosted URL other than the repo itself
- [ ] A fresh macOS machine reaches first boot with only git, gh and the plugin installed

## Revisit when
A surface the product must support cannot use GitHub or Notion connectors.

## More information
