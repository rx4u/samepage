# ADR-0017: Adopt surfaces as roles, with a tool field

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
samepage v1.0 names four surfaces (code, chat, cowork, design) and each one meant one Claude product. The v1.0 launch scope (docs/build/everyone-plan.md) adds coding tools from other vendors: Codex, Cursor, GitHub Copilot, Gemini CLI and Windsurf, plus Claude Desktop. Two questions follow: which boot file and handoff inbox does Cursor read, and how does a reader tell that a decision came from Codex rather than Claude Code.

Owner answers recorded 2026-11-06: Raja has no logins for Codex, Cursor, Copilot, Gemini CLI or Windsurf, so only Claude tools can be tested before launch (Q1). ChatGPT is left out of the launch (Q2, ADR-0019). The pitch leads with Claude, and other tools are adapters marked community-tested (Q3, ADR-0018).

## Options

### Option A: Keep the four surface codes as roles; add an optional `tool` lookup on rows that record where they came from
- Pros: boot files, handoff inboxes and rule scopes stay four, so the serve layer, budgets and the Notion 4-query boot do not change; a handoff to `code` is picked up by whichever coding tool opens next; existing stores stay valid.
- Cons: a rule cannot be limited to one tool; readers see the tool only where it is printed.
- Price: 0 USD.

### Option B: One surface code per tool (cursor, codex, ...)
- Pros: rules and handoffs can target one tool.
- Cons: one boot file and one inbox per tool (10 or more), a handoff to "Cursor" is missed when the user opens Codex, the surface lookup changes meaning (a breaking change, major version).
- Price: 0 USD, about 3 days more work and a migration.

## Decision
Option A.
- `surface` means the job a tool does: `code` (any coding agent), `chat` (any chat assistant), `cowork`, `design`. The codes do not change.
- New lookup `tool`: claude_code, claude_ai, claude_desktop, cowork, claude_design, codex, cursor, copilot, gemini_cli, windsurf, other. Codes are snake_case like every other lookup (client_site, picked_up). There is no chatgpt code (ADR-0019); `other` covers any unlisted tool.
- New optional columns: `ship_event.tool_id`, `decision.tool_id`, `design_asset.tool_id` (file key `tool`) and `handoff.from_tool_id` (file key `from_tool`). Handoffs still go to a role (`to_surface`); there is no `to_tool`. Rules stay scoped by surface only.
- Default role per tool, used when a writer is given a tool and no surface: claude_code, codex, cursor, copilot, gemini_cli, windsurf to `code`; claude_ai and claude_desktop to `chat`; cowork to `cowork`; claude_design to `design`; other has no default and needs a surface.
- Schema version 1.1 (minor, additive). Columns added in 1.1 carry `-- since 1.1` in the DDL and `"since": "1.1"` in schema/fields.json. Writers (`sp`, the skill, `sp mcp`) write `tool` and `from_tool` only when the store's `store.md` says `schema_version` 1.1 or higher; `sp check` fails a 1.0 store that carries them. This keeps every 1.0 store valid under the sha-pinned store Action (ADR-0016), whose older `sp check` rejects unknown keys.
- New stores (`sp init`, the template repo) start at 1.1. A 1.0 store upgrades by setting `schema_version: 1.1` in store.md and bumping the Action's pinned sha in the same commit (SPEC.md, "Upgrade a store").
- Serve files show the tool on handoff lines only (`from chat via claude_ai`), where it tells the reader who left the brief. Boot budgets do not change.

## Non-goals
Per-tool rules, per-tool handoff targets, tool detection from environment variables (tools do not document stable ones; the tool is passed explicitly by each adapter).

## Consequences
- Gets easier: adding a tool is one lookup code and one adapter, no serve-layer change.
- Gets harder: two places hold provenance (surface and tool); the default-role table must stay in sync with the lookup.
- Follow-up tasks: WP-18 (schema and writers), Notion setup adds a "Tool" select to Ship Events, Decisions and Design Assets and "From tool" to Handoffs; `sp export` maps them.

## Implementation plan
- Affected paths: docs/architecture/data-architecture.md, schema/*.json (via `python3 -m sp schema`), sp/__init__.py, sp/schema.py, sp/check.py, sp/write.py, sp/log.py, sp/handoff.py, sp/index.py, sp/export.py, sp/init.py, commands/sp.md, skills/samepage/references/entry-schema.md, skills/samepage/references/notion-backend.md, store-template/store.md, SPEC.md, tests.
- Pattern to follow: one `--tool` flag on every write command, validated against the lookup; the writer drops it (with a note) when the store is 1.0.
- Pattern to avoid: inferring the tool from environment variables or process names.
- Config and env changes: `SAMEPAGE_TOOL` may set the default `--tool` for a shell (adapters set it; the user never needs to).

## Verification
- [ ] A 1.0 store with no tool keys passes `sp check`; the same store with a `tool` key fails with a message naming schema 1.1
- [ ] `sp log ship --tool cursor` on a 1.1 store writes `tool: cursor`; on a 1.0 store it writes no tool key and prints one note
- [ ] fixtures/small passes unchanged; a 1.1 fixture case with every tool key passes

## Revisit when
Users ask for rules or handoffs aimed at one tool (10 issues), or a tool needs a role that is none of the four.

## More information
- 2026-11-06: answers to the plan's three open questions given by Raja in the build session: no logins for non-Claude tools, leave ChatGPT out, Claude first with other tools community-tested.
