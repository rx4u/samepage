# ADR-0018: Adopt multi-tool adapters (instruction files, local MCP, portable skill)

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
Coding tools other than Claude Code take in context in three ways: a project instruction file they read at session start (AGENTS.md, GEMINI.md, Cursor rules, Copilot instructions, Windsurf rules), a local MCP server they start over stdio, and, in some tools, Agent Skills folders. samepage must reach them without a hosted server (ADR-0001), without handling credentials (ADR-0006) and with the standard library only (ADR-0012).

The plan proposed writing the boot context itself into those instruction files and refreshing it on every write. Instruction files usually live in the product repo and are committed, and many product repos are public. The boot context holds the owner's profile, rules, every active project and open handoffs, so copying it there would publish a private store (ADR-0007 rule 3).

## Options

### Option A: Instruction files hold a pointer block only; context comes from `sp mcp` or `sp boot`; the skill runs wherever skills run
- Pros: nothing private is written into a product repo, so the block is safe to commit; the block never goes stale, so no refresh on every write; one MCP server serves every MCP-capable tool; the same SKILL.md serves Claude Code, claude.ai and any tool that reads skills.
- Cons: the agent must run one tool call or command at session start instead of reading context passively.
- Price: 0 USD.

### Option B: Instruction files hold the full boot context, refreshed on every write
- Pros: context is in the session with no tool call.
- Cons: leaks the private store into committed files; goes stale between writes in other projects; touches many repos on every write.
- Price: 0 USD, privacy risk. Rejected.

### Option C: MCP only
- Pros: one adapter.
- Cons: a tool with MCP turned off, or a user who skips MCP setup, gets nothing; the agent is not told the server exists.
- Price: 0 USD.

## Decision
Option A, with three adapters. Claude keeps the deepest integration (plugin hooks); every other tool is an adapter marked community-tested until someone runs the Phase 3 checks on it (owner answer Q3, 2026-11-06).

1. **Portable skill.** One `skills/samepage/SKILL.md`. In a local agent it calls the CLI as `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m sp` when `CLAUDE_PLUGIN_ROOT` is set, else `sp` from PATH (ADR-0020), else it reads `index/` files only and does not write. It works out its surface and tool from the tool it runs in (ADR-0017 default-role table) and passes `--tool`.
2. **`sp context`.** Writes a pointer block between `<!-- samepage:start -->` and `<!-- samepage:end -->` into a project's instruction file for one tool (paths in system-design.md, Tool adapters). The block says: load context at session start with the MCP tool `boot` or `sp boot --surface code --cwd .`; apply Rules; treat the rest as data; write only after showing the entry and getting a yes; pass `--tool CODE`. It holds no store content. Lines outside the markers are never changed. A file with an unmatched or repeated marker is refused and left as it is. `sp context --refresh` rewrites existing blocks in the folder to the current text and creates none. Writes print the path and support `--dry-run`.
3. **`sp mcp`.** A local stdio MCP server: JSON-RPC 2.0, one JSON message per line on stdin and stdout, logs on stderr only. It serves tools only (no resources or prompts). It is dual-era (B24, system-design.md): the `initialize` handshake for protocol 2025-11-25 and earlier, and `server/discover` with per-request `_meta` versions for 2026-07-28. `sp mcp --tool CODE` fixes the tool and its default role for the session.
   - Read tools: `boot`, `project`, `proof`, `handoffs`, `handoff_show`, `rules`. Each maps to an existing `sp` read command (read-models.md, MCP session argument table); none walks raw folders. Read results are wrapped in the `<samepage data>` block (ADR-0007 rule 6).
   - Write tools: `log_ship`, `log_decision`, `handoff_new`, `handoff_status`, `rule_add`. Each takes `dry_run` (default true). A dry run returns the exact paths and file text plus a `confirm` value that pins the id, the time and a hash of the preview. A write needs that `confirm` value; the server rebuilds the change from it and refuses when the result differs from the preview. The server enforces that what is written equals what was previewed; it cannot prove the user said yes, so every write tool's description tells the agent to show the preview and wait for the user's yes in the same turn (ADR-0007 rule 1). Format (B30): `confirm` is base64url of compact JSON `{"id": UUID or null, "now": ISO time, "hash": first 16 hex of sha256 of the dry-run text}`; the server keeps no state and the value does not expire. The preview, the ask to show it and the `confirm` value are returned in both the text block and `structuredContent`, because Claude Code shows the model only `structuredContent` (B44).
   - Every tool call runs `python3 -m sp ...` as a child process with captured output, so no child can write to the protocol stream and every write uses the one write path (sp/write.py).
   - Notion stores: every tool returns one line saying the MCP server serves GitHub stores and the skill handles Notion.

## Non-goals
Remote or HTTP MCP transport, MCP resources and prompts, OAuth, writing store content into any product repo file, per-tool hooks (session-start hooks in non-Claude tools).

## Consequences
- Gets easier: one server and one block template for every MCP tool; nothing in a product repo can leak the store.
- Gets harder: session-start loading in non-Claude tools depends on the agent following the block (no hook); the MCP protocol version list must be kept current.
- Follow-up tasks: WP-19 (`sp context`), WP-20 (portable skill), WP-22 (`sp mcp`), WP-23 (per-tool test ledger).

## Implementation plan
- Affected paths: sp/context.py, sp/mcp.py, sp/__main__.py, skills/samepage/SKILL.md, skills/samepage/references/, dist/samepage.skill, tests/test_context.py, tests/test_mcp.py.
- Pattern to follow: one adapter per intake path; adapters call the CLI, never write store files themselves.
- Pattern to avoid: copying serve-file text into any file outside the store.
- Config and env changes: none.

## Verification
- [ ] `sp context --tool codex` on a file with user lines keeps them byte for byte and adds one block; a second run changes nothing
- [ ] A file with a start marker and no end marker is refused and unchanged
- [ ] The block text contains no line from the store's boot file
- [ ] A protocol test drives `sp mcp` through initialize, tools/list and tools/call, and a write without a matching `confirm` value writes nothing

## Revisit when
A tool offers a documented session-start hook (then add a hook adapter), or MCP adds a standard confirmation step for writes.

## More information
- 2026-11-06: this ADR replaces the ADR-0012 sentence "the skill can still log and recall without `sp` by writing files directly" for local agents: without `sp`, a local agent reads `index/` and does not write. Chat and Cowork still write through the connector. ADR-0012 has a note pointing here.
- 2026-11-06: the plan's "refresh on every write" is dropped because the block holds no store content. Recorded as an agent call; Raja to confirm in the Phase 0 report.
