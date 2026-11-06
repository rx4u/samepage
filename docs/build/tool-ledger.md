# Tool ledger (WP-23)

One row per real run of the Phase 3 checklist in a tool. A tool gets a "tested" tick in the README only with a passing row here (owner answer Q1, 2026-11-06). Other tools are listed as community-tested.

| Date | Tool | Tool version | OS | Adapter | Boot | Log (preview, confirm) | Handoff picked up | Result | By |
|---|---|---|---|---|---|---|---|---|---|
| 2026-11-06 | Claude Code | 2.1.318 | Linux (cloud container) | plugin: SessionStart hook and `/samepage:sp log` | Pass: profile, rules and open handoff in context | Pass: dry run shown, written after yes, `tool: claude_code`, `surface: code` | Pass: listed as "from chat via claude_ai" | Pass | agent run, headless `claude -p` |
| 2026-11-06 | Claude Code (as MCP client) | 2.1.318 | Linux (cloud container) | MCP: `sp mcp --tool claude_code` | Pass: `boot` tool returned the profile | Pass after fix B44 (preview first reached the model as a bare token); write without `confirm` refused | n/a | Pass | agent run |
| 2026-11-06 | Gemini CLI | 0.67.0 | Linux (cloud container) | MCP config from `sp setup gemini` | Not run: no login | Not run: no login | Not run | Partial: `gemini mcp list` shows Connected after fix B45 (PYTHONPATH was blocked) and after trusting the folder | agent run |
| 2026-11-06 | Codex CLI | 0.167.0 | Linux (cloud container) | MCP config from `sp setup codex` | Not run: no login | Not run: no login | Not run | Partial: `codex mcp list` parses config.toml and shows samepage enabled | agent run |
| 2026-11-06 | GitHub Copilot CLI | 1.0.106 | Linux (cloud container) | MCP config from `sp setup copilot` | Not run: no login | Not run: no login | Not run | Partial: `copilot mcp list` shows samepage under User servers | agent run |

How to add a row: run the checklist for the tool, fill one line, and link any issue found in the Result column.

Partial rows prove the config a tool reads is valid; they do not earn a tick. Claude Desktop, claude.ai chat and Cowork need a run on Raja's Mac (phase3-checklist.md, steps 2 and 3).
