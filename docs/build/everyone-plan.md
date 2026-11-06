# samepage for every AI: build plan (v1.0 launch scope)

Status: Phases 0 to 2 done and on main (2026-11-06). Phase 3: Claude Code passed, and Gemini CLI, Codex and Copilot CLI configs load (tool-ledger.md); Claude Desktop, claude.ai and Cowork wait for Raja's Mac run. Phase 4: README and plugin 1.1.0 done; v1.1.0 released 2026-11-06 (run by Raja); install.sh now installs the newest release tag. Open: Mac run for the Claude surfaces, About box, landing page.
Read with `docs/architecture/` (binding) and `CLAUDE.md`.

## Goal

One shared working context for every AI tool a person uses, not only Claude. Launch line: "Keep every AI on the same page." The name stays samepage. Claude keeps the deepest integration; every other tool is a first-class citizen.

Two promises that do not change: no hosted server, and samepage never handles tokens or credentials (ADR-0001, ADR-0006). The store stays a private GitHub repo of Markdown files.

## Design

### 1. Surfaces become roles, plus a tool field

- `surface` lookup means the job a tool does: `code` (any coding agent: Claude Code, Codex, Cursor, Copilot, Gemini CLI, Windsurf), `chat` (any chat assistant: claude.ai, ChatGPT), `cowork`, `design`.
- New optional key `tool` on entries that carry a surface (ship events, decisions, handoffs, rules if useful): lookup codes such as `claude-code`, `claude-ai`, `cowork`, `claude-design`, `codex`, `cursor`, `copilot`, `gemini-cli`, `windsurf`, `chatgpt`, `other`.
- Handoffs still go to a role: a handoff to `code` is picked up by whichever coding tool opens next.
- Existing stores stay valid (tool is optional). Schema version bump decided in Phase 0 (1.0 to 1.1 if keys change). Update SPEC.md, data-dictionary.md, schema/*.json via `python3 -m sp schema`.

### 2. One adapter per way a tool takes in context

| Adapter | Tools | What |
|---|---|---|
| Claude Code plugin (exists) | Claude Code | SessionStart boot, Stop nudge, `/sp` |
| Portable skill (exists, generalise) | claude.ai, Codex, Copilot, Gemini CLI | Same SKILL.md; remove the hard dependency on `${CLAUDE_PLUGIN_ROOT}`, call `sp` from PATH when the plugin root is absent |
| `sp context` (new) | Codex, Gemini CLI, Cursor, Copilot, Windsurf | Writes the boot context into `AGENTS.md`, `GEMINI.md`, `.cursor/rules/samepage.mdc`, `.github/copilot-instructions.md`, `.windsurfrules` inside a project, between `<!-- samepage:start -->` and `<!-- samepage:end -->` markers, never touching the user's own lines. Refreshed on every `sp` write and by `sp context --refresh` |
| `sp mcp` (new) | Cursor, Windsurf, Codex, Copilot, Gemini CLI, Claude Desktop | Local stdio MCP server, Python stdlib only (JSON-RPC 2.0 over stdin/stdout). Read tools: boot, project, proof, handoffs, rules. Write tools: log_ship, log_decision, handoff_new, handoff_status, rule_add; every write takes `dry_run` and returns the preview first (ADR-0007 confirm flow) |
| GitHub connector (exists) | claude.ai, ChatGPT | Read `index/boot/chat.md`. ChatGPT is read-only: it supports only remote HTTPS MCP servers, and a hosted server breaks the no-server promise |

### 3. Install for everyone

- `install.sh` (POSIX sh): clones or updates samepage into `~/.samepage/tool`, puts an `sp` shim in `~/.local/bin`, prints the next step. No sudo, no package manager.
- `sp setup <tool>` for `codex`, `cursor`, `copilot`, `gemini`, `windsurf`, `claude-desktop`, `chatgpt`: registers `sp mcp` in that tool's MCP config (or prints the exact snippet when the config path is not certain), installs the skill where the tool reads skills, and runs `sp context` for the current project. `chatgpt` prints the read-only project-instructions line.
- The Claude Code plugin install stays as it is. `sp init` and the template repo (ADR-0016) stay the way to create a store.

## Phases

| Phase | Work | Where | Done when |
|---|---|---|---|
| 0 Decide | ADR-0017 surfaces as roles plus tool field; ADR-0018 multi-tool adapters (context files, local MCP, portable skill); ADR-0019 ChatGPT read-only; ADR-0020 installer and `sp setup`. Update PRD, scope, users-and-roles, data-dictionary, read-models, system-design, guardrails, build-plan (new WPs) | cloud | ADRs accepted, docs consistent, builder-check passes |
| 1 Core | Schema change with tests; `sp context` with marker-safe writes and tests; portable SKILL.md (skill-workshop phases 3 to 7); `install.sh`; `sp setup` | cloud | tests and guardrails pass, CI green |
| 2 MCP | `sp mcp` stdio server, stdlib only, with a protocol test that drives it through initialize, tools/list and tools/call, and the dry-run-then-confirm write flow | cloud | protocol tests pass; works with the MCP inspector if available |
| 3 Test per tool | Real runs: Claude Code, claude.ai, Codex, Cursor, Copilot, Gemini CLI, ChatGPT (read-only) | Raja's Mac, Claude Code | each tested tool recorded in a ledger like `docs/build/wp14-edge-cases.md` |
| 4 Reposition | README for every AI (tested-tools table, only tools actually tested get a tick), new gif, landing page on Vercel, release v1.0.0 | cloud | release published, page live |

## Answers (Raja, 2026-11-06, recorded in ADR-0017 to ADR-0020)

1. No logins for Codex, Cursor, Copilot, Gemini CLI or Windsurf. Only Claude tools get a tested tick until someone runs the Phase 3 checklist on another tool.
2. Leave ChatGPT out of the launch (ADR-0019). This replaces the read-only proposal below.
3. Claude first; other tools are adapters marked community-tested (ADR-0018).

Phase 0 changes to this plan: instruction files get a pointer block with no store content, so they are safe to commit and are not refreshed on every write (ADR-0018). Tool codes are snake_case (claude_code, gemini_cli). `sp setup` writes configs only where the vendor path is verified; Cursor and Windsurf print a snippet until verified (system-design.md, Tool adapters).

## Open questions for Raja (asked 2026-11-06, answered above)

1. Which tools does Raja have logins for (Codex, Cursor, Copilot, Gemini CLI, Windsurf)? Only those get a "tested" tick.
2. ChatGPT read-only at launch: accepted? (Recommended: yes, keep the no-server promise.)
3. All tools equal in the pitch, with Claude as the deepest integration? (Recommended: yes.)

## State at handoff (2026-11-06)

- main at the latest commit on github.com/rx4u/samepage; CI green (Ubuntu 3.13, macOS system Python 3.9, guardrails).
- No release or tag yet. Raja runs Actions, release, Run workflow, version 1.0.0 when ready (the session proxy refuses tag pushes; the release workflow creates the tag).
- Template repo rx4u/samepage-store-template is public and marked as a template; stores pin the tool by commit sha (ADR-0016).
- Throwaway repo rx4u/samepage-template-check and branch spike/wp01 exist; Raja deletes them if he wants. Never delete them yourself.
- Brand: Chunky Cursor mark in docs/brand/ (black and white only). Open note: the #0a0a0a tile nearly vanishes on GitHub dark (#0d1117).
- Raja's own Notion store from WP-16 exists (private); his Projects Registry stays read-only until 2026-11-20.
- Not yet verified: Raja's own install on his Mac, chat writes after installing the Claude GitHub app (A2).
