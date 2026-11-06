# Assumptions

## Register
| # | Assumption | Category | Impact | Uncertainty | Risk |
|---|---|---|---|---|---|
| A3 | Users keep logging after week one when logging is drafted for them and nudged | User behaviour | 5 | 4 | 20 |
| A1 | Claude Design imports a design system from a linked GitHub repo's W3C tokens file (VERIFIED 2026-11-06) | Integration | 4 | 0 | 0 |
| A4 | Multi-surface builders feel the context gap enough to install a plugin, upload a skill and create a store | Business | 5 | 3 | 15 |
| A12 | Anthropic does not ship native cross-surface memory that covers projects, ships and handoffs before 2027-03-01 | Business | 4 | 3 | 12 |
| A17 | A proof-and-handoffs pitch earns stars in a crowded "context OS" category | Business | 4 | 3 | 12 |
| A2 | claude.ai chat, inside one skill run, can read a file and create a file in a private repo through the GitHub connector | Integration | 5 | 2 | 10 |
| A16 | Claude Design cannot run skills or connectors, so it cannot read the store directly | Integration | 3 | 3 | 9 |
| A6 | python3 is present on target machines (macOS with Xcode Command Line Tools, Linux) | Technical feasibility | 3 | 3 | 9 |
| A11 | Users accept a separate private repo or Notion page for their store | User behaviour | 3 | 3 | 9 |
| A15 | A Claude Design "Send to Claude Code" bundle in a Code session exposes a title or link the skill can record | Integration | 2 | 4 | 8 |
| A19 | Active builders lose 15 to 30 minutes a day re-establishing context (prd.md) | User behaviour | 2 | 4 | 8 |
| A9 | Notion connector is usable inside Claude Code when signed in with the claude.ai account | Integration | 3 | 2 | 6 |
| A13 | Flat frontmatter (no nesting) is enough for every entity | Technical feasibility | 3 | 2 | 6 |
| A8 | 2,000 tokens is enough boot context to change answers on every surface | User behaviour | 3 | 2 | 6 |
| A7 | SessionStart hook stdout is added to Claude Code's context (VERIFIED 2026-11-06) | Technical feasibility | 4 | 0 | 0 |
| A14 | Most early users are on macOS or Linux | User behaviour | 2 | 2 | 4 |
| A18 | Launch date 2026-12-01 (ASSUMPTION in prd.md) | Business | 2 | 2 | 4 |
| A10 | Store Action stays within GitHub's free private-repo minutes | Scale | 2 | 1 | 2 |
| A21 | Agents in Codex, Cursor, Copilot, Gemini CLI and Windsurf follow the instruction-file block and load context at session start | Integration | 4 | 4 | 16 |
| A22 | The MCP config paths and formats in system-design.md are current for each tool (checked 2026-11-06 from vendor docs) | Integration | 4 | 3 | 12 |
| A23 | MCP clients accept a stdlib server that negotiates the protocol versions listed in sp/mcp.py | Technical feasibility | 4 | 2 | 8 |
| A24 | Users without Claude logins find samepage useful with adapters marked community-tested | Business | 3 | 4 | 12 |

## Top 3
1. **A3: users keep logging.** We assume this because drafting from the session makes a log take about 30 seconds and the Stop hook reminds them. False if, among 5 testers, fewer than 3 log 5 or more entries in their second week.
   - Test: dogfood plus 5 target users using the WP-08 build for 2 weeks; count entries per person per week with `sp stats`.
   - Deadline: 2026-11-27, before launch (WP-15). If false, launch leads with Code boot and handoffs, and logging moves to a "weekly review" flow.
   - Owner: Raja
2. **A1: Claude Design imports tokens from a linked repo.** We assume this because two third-party guides from June 2026 describe it. False if a linked test repo's `design/tokens.json` does not change Claude Design's output.
   - Test: WP-01 spike with a test account and a test repo.
   - Deadline: 2026-11-11, before WP-13 starts in wave 3.
   - Owner: Raja (needs a Claude Design session)
3. **A4: the pain is strong enough to install.** We assume this because six open feature requests on anthropics/claude-code ask for it and two community repos exist. False if fewer than 3 of 5 target users complete setup when offered.
   - Test: offer the WP-06 build to 5 multi-surface builders; record setup completion and time.
   - Deadline: 2026-11-20, before wave 4.
   - Owner: Raja

## Wave 5 top risks (ADR-0017 to ADR-0020)
- **A21: agents follow the block.** No owner login exists for those tools (2026-11-06), so this cannot be tested before launch by the owner. Test: any contributor or tester with one tool runs the WP-23 checklist; one passing run per tool flips its README tick. Deadline: open, accepted as a launch risk in writing by Raja's answer Q3 (community-tested). Owner: Raja.
- **A22: config paths.** Test: WP-21 tests pin the documented shapes; recheck vendor docs at each release. Deadline: each release. Owner: maintainer.
- **A23: protocol acceptance.** Test: tests/test_mcp.py drives the handshake; Claude Desktop (owner has it) is the first real client in WP-23. Deadline: WP-23. Owner: Raja.

## Accepted risks
- A24: adapters ship as community-tested (owner decision 2026-11-06). Recovery cost: 0; ticks are added as ledger rows land.
- A2: chat writes through the connector. TESTED 2026-11-06 (WP-01): claude.ai chat read SPIKE.md on rx4u/samepage, but the write returned `403 Resource not accessible by integration`. Verified on github.com/settings/installations: the Claude app (used by Claude Code) is installed, the GitHub app behind the claude.ai chat connector is not. INFERRED from a public troubleshooting note (epik-agent/Epik issue 336): chat writes need that connector app installed on the repo owner's account, then a new conversation. Consequence: setup must include that install step, and the US-06 read-only fallback is required. Retest after install.
- A12: native memory arrives. Recovery cost: reposition on proof, decisions and handoffs; 2 days of README and skill changes.
- A16: Design reads nothing from the store. Already the v1 design (ADR-0011). Recovery cost: 0.
- A20 (observed 2026-11-06 on claude.ai/design): a banner reads "Claude Design is moving on December 14. Move your projects to Claude to keep working on them." Standalone Claude Design folds into claude.ai before samepage launches. Consequence: the Design surface will run inside claude.ai, where skills and connectors exist, so A16 may stop holding. ADR-0011 must be revisited once the move lands; v1 keeps the repo-tokens plus handoff design until then.
- A1: PASS 2026-11-06 (WP-01). With rx4u/samepage linked as the codebase and the design system set to None, Claude Design read design/tokens.json on branch spike/wp01 when the prompt named file and branch, and produced a pricing card using exactly those tokens: magenta #C026D3, square corners, paper #F5F5F0. Checked visually from a screenshot. It also read the README on main for copy. Note: the branch had to be named in the prompt; the codebase picker shows no branch choice.
- A6, A14: Python and POSIX availability. Recovery cost: a Node or PowerShell hook, 3 days.
- A11: separate store. Recovery cost: support a `context/` folder inside an existing repo, 2 days.
- A15: Design bundle contents. Recovery cost: user types the title, 0.5 day.
- A9: Notion in Code. Recovery cost: document "Notion stores boot in Code through the skill on first use", 0.5 day.
- A13: flat frontmatter. Recovery cost: new child table per nested need, 1 day each.
- A8: boot size. Recovery cost: raise the cap by ADR, 0.5 day.
- A7: hook stdout. VERIFIED 2026-11-06 (WP-01): a 5,965 character SessionStart hook output was recalled at both ends by Claude Code 2.1.318 in headless mode. Closed.
- A10: Action minutes. Recovery cost: rebuild only on changed folders, 0.5 day.
- A17: crowded category. Mitigated by ADR-0010 rename and a demo that shows chat citing Code work. Recovery cost: relaunch content, 2 days.
- A18, A19: dates and time-loss estimate are planning numbers. Recovery cost: 0.

## Constraints
- Anthropic trademark: no "claude" or "anthropic" in the name or skill id. Addressed by: ADR-0010.
- GitHub API rate limit for connectors (about 5,000 requests per hour per user). Addressed by: one-read boot, ADR-0004.
- Notion API rate limit (about 3 requests per second). Addressed by: 4-query boot cap, targets.md.
- GitHub free Actions minutes for private repos (2,000 per month). Addressed by: targets.md cost row.
- claude.ai skill and connector availability depends on the user's plan. Addressed by: README requirements section in WP-15.
- Claude Code SessionStart hooks run under a timeout the plugin sets. Addressed by: 3 s budget, ADR-0001 and WP-06.
