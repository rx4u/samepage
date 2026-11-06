# Scope

## v1 must-haves
| Feature | Stories | Value (1-5) | Effort (S/M/L) | Data it needs |
|---|---|---|---|---|
| Store spec (SPEC.md + schema) | all | 5 | S | all entities |
| `sp` CLI: init, check, index, log, boot | US-01, US-03, US-05, US-13 | 5 | M | all entities |
| GitHub store template with index Action | US-01, US-06 | 5 | S | index_build |
| Claude Code plugin: SessionStart boot, Stop nudge, /sp commands | US-03, US-05, US-08, US-09, US-11 | 5 | M | project, handoff, ship_event |
| One skill `samepage` for chat, Cowork and Code, GitHub backend | US-04, US-06, US-07, US-08, US-12, US-14, US-15 | 5 | M | all entities |
| Notion backend (templates + skill reference) | US-02 and every read and write story | 4 | M | all entities |
| Design pointers and Design handoff capture | US-10, US-11 | 4 | S | design_asset |
| Demo store with synthetic data and perf check | US-13 | 4 | S | all entities |
| Launch kit: README, demo gif, install in one line | none (adoption) | 5 | S | none |
| Tool field and roles (schema 1.1, ADR-0017) | US-16, US-17 | 4 | S | ship_event, decision, design_asset, handoff, tool |
| Portable skill, `sp context` instruction blocks, `sp mcp` local server (ADR-0018) | US-16, US-17, US-19 | 5 | M | all read models |
| `install.sh` and `sp setup` for codex, cursor, copilot, gemini, windsurf, claude-desktop (ADR-0020) | US-18 | 4 | M | none |
| One-line install: the site's `/install` piped to `sh` runs `sp start`, no questions (ADR-0024) | US-18 | 4 | S | none |
| `sp link` and `sp sync`: rules and decisions shared both ways between two local GitHub stores (ADR-0023) | US-15 | 4 | S | none |

## Cut from v1
| Feature | Why cut | Revisit when |
|---|---|---|
| Two-way sync between a GitHub store and a Notion store | Doubles the write paths and creates conflicts. Users pick one backend. | 50 issues or discussions ask for it |
| Writes from Claude Design | No evidence Claude Design runs skills or connectors (A1, A16) | Anthropic documents connectors or skills in Claude Design |
| Hosted MCP server for the store | Adds infra, auth and cost; breaks "zero infra". The local stdio `sp mcp` (ADR-0018) is in v1; nothing remote is | A surface appears that cannot use GitHub or Notion connectors |
| ChatGPT | Accepts only remote HTTPS MCP servers; no login to test (ADR-0019, owner decision 2026-11-06) | ChatGPT supports local MCP or free-plan GitHub reads, and 10 issues ask |
| Rules or handoffs aimed at one tool | Roles cover the need; per-tool targets multiply inboxes (ADR-0017) | 10 issues ask |
| Tested ticks for Codex, Cursor, Copilot, Gemini CLI, Windsurf | No owner logins (2026-11-06); adapters ship as community-tested | A maintainer or contributor runs the Phase 3 checklist and records it |
| Team stores (several people, one store) | Permissions and conflict model not designed | 3 teams ask, with a concrete workflow |
| Importing claude.ai memory or chat history | Native export formats change; distilled entries are the point | A stable export format exists |
| Windows-native hook script | Plugin hook uses POSIX shell and python3 | 10 Windows issues; then ADR for a Node or PowerShell hook |
| Semantic search over entries | Needs embeddings or a server | Stores over 2,000 events report recall misses |

## Later phases
| Phase | Features | Trigger to start |
|---|---|---|
| 1.1 | Store migration helper from an existing Notion database with a field map | 2 weeks after launch |
| 2 | Team stores with per-member write logs | Revisit condition above |

## Parking rules
A parked feature's code stays, gets no new work, and is hidden if broken.
