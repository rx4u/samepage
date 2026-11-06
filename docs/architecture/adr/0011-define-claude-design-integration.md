# ADR-0011: Define the Claude Design integration

Status: accepted
Date: 2026-11-06
Deciders: Claude (architect), agent call

## Context
Claude Design is one of the four surfaces. Third-party guides (claudefa.st, skills-hub.ai, June 2026) report that Claude Design can link a codebase and import a design system, that it reads W3C-format tokens from a repo, and that it exports a "Send to Claude Code" handoff bundle. No source found says Claude Design runs skills or calls connectors. INFERRED: everything above comes from third-party sources, not Anthropic documentation.

## Options

### Option A: Design reads the product repo's tokens; the store keeps pointers; Code logs Design handoffs; chat exports a design brief to paste into Design
- Pros: uses only what Claude Design is reported to do; works today; no writes from Design needed.
- Cons: Design does not see the owner's rules or decisions automatically; a paste step remains.
- Price: 0 USD.

### Option B: Wait for Claude Design to support skills or connectors
- Pros: full read and write later.
- Cons: launches without one of the four surfaces.
- Price: 0 USD, launch delay.

## Decision
Option A for v1, conditional on spike WP-01. If WP-01 shows Claude Design cannot import tokens from a linked repo, US-10 drops the import step and keeps the pointer plus the design brief export, and the README says so.

## Non-goals
Generating or editing design tokens.

## Consequences
- Gets easier: honest launch claims about Claude Design.
- Gets harder: the Design experience is one step less automatic than Code.
- Follow-up tasks: WP-01 spike, WP-13 design modes.

## Implementation plan
- Affected paths: skills/samepage/references/design.md, plugin/commands/sp.md
- Pattern to follow: design_asset rows point to files; they never copy token values.
- Pattern to avoid: claiming Design reads the store.
- Config and env changes: none.

## Verification
- [ ] WP-01 result recorded in assumptions.md with date and screenshots
- [ ] A design brief exported for the demo project pastes into Claude Design and produces a design using the stated tokens

## Revisit when
Anthropic documents skills or connectors in Claude Design.

## More information
- 2026-11-06: claude.ai/design shows that standalone Claude Design moves into Claude on 2026-12-14. Revisit this ADR after the move: if Design inside Claude runs skills or connectors, Design gains direct store reads and writes.
