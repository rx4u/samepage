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

## Cut from v1
| Feature | Why cut | Revisit when |
|---|---|---|
| Two-way sync between a GitHub store and a Notion store | Doubles the write paths and creates conflicts. Users pick one backend. | 50 issues or discussions ask for it |
| Writes from Claude Design | No evidence Claude Design runs skills or connectors (A1, A16) | Anthropic documents connectors or skills in Claude Design |
| Hosted MCP server for the store | Adds infra, auth and cost; breaks "zero infra" | A surface appears that cannot use GitHub or Notion connectors |
| Team stores (several people, one store) | Permissions and conflict model not designed | 3 teams ask, with a concrete workflow |
| Importing claude.ai memory or chat history | Native export formats change; distilled entries are the point | A stable export format exists |
| Windows-native hook script | Plugin hook uses POSIX shell and python3 | 10 Windows issues; then ADR for a Node or PowerShell hook |
| Semantic search over entries | Needs embeddings or a server | Stores over 2,000 events report recall misses |

## Later phases
| Phase | Features | Trigger to start |
|---|---|---|
| 1.1 | Store migration helper from an existing Notion database with a field map | 2 weeks after launch |
| 1.2 | Codex, Cursor and other agent adapters reading the same GitHub store | 300 stars or a contributor PR |
| 2 | Team stores with per-member write logs | Revisit condition above |

## Parking rules
A parked feature's code stays, gets no new work, and is hidden if broken.
