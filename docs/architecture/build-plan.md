# Build plan

## Waves
| Wave | Contains |
|---|---|
| 1 | Spikes for the top assumptions, spec and schema, `sp check`, `sp index`, fixtures and demo store, CI guardrails |
| 2 | Session boot in Claude Code end to end, including GitHub setup: the template every other screen copies |
| 3 | Skill modes on chat and Cowork, log, handoffs, proof, decisions, design, Notion backend, store Action |
| 4 | Edge cases, dogfood, launch kit and release |
| 5 | Every coding tool (ADR-0017 to ADR-0020): schema 1.1, instruction blocks, portable skill, installer and setup, local MCP server, per-tool tests, reposition |

### WP-01: Spikes for A1, A2 and A7
Wave: 1
Depends on: none
- Why: the three riskiest assumptions decide whether US-10, US-06 and US-03 are buildable as written.
- Do: in `spikes/` (thrown away): (1) link a test repo with `design/tokens.json` in Claude Design and check whether the import uses it; (2) from claude.ai chat with the GitHub connector, read a file and create a new file in a private test repo inside one skill run; (3) a SessionStart hook that prints 6,000 characters and a check that Claude can quote it.
- Read model: none
- Targets: none
- Columns touched: none
- Migrations: none
- Out of scope: any production code.
- Done when: results written into assumptions.md with date and evidence; ADR-0011 updated if A1 fails.

### WP-02: Spec, schema files and `sp check`
Wave: 1
Depends on: none
- Why: every other package reads and writes the same contract.
- Do: write SPEC.md from data-architecture.md; generate schema/fields.json and schema/lookups.json; build sp/model.py (flat frontmatter parse and emit) and sp/check.py with the secret patterns from ADR-0007.
- Read model: Store check
- Targets: Rows per read; Secrets committed to a store
- Columns touched: every table (validation only)
- Migrations: none
- Out of scope: index generation.
- Done when: fixtures/small passes, 12 broken fixtures fail with path, field and allowed values.

### WP-03: `sp index` serve layer
Wave: 1
Depends on: WP-02
- Why: boot and lists depend on pre-built serve files (ADR-0004, ADR-0005).
- Do: generators for index/boot/{surface}.md, index/project/{slug}.md, projects, proof, tags, handoffs, rules, builds; header line; `next:` footers; caps from read-models.md.
- Read model: Session boot, Chat recall, Proof lookup, Handoff inbox, Project detail, Rules
- Targets: Boot file size per surface; `sp index` on a 1,000 project store
- Columns touched: index_build.*
- Migrations: none
- Out of scope: the Action workflow (WP-11).
- Done when: perf fixture indexes under 5 s, all boot files under 8,000 characters, page chains valid.

### WP-04: Fixtures and demo stores
Wave: 1
Depends on: WP-02
- Why: staging for every later package (ADR-0009).
- Do: `sp fixtures --perf --seed 42` per test-data.md; fixtures/small by hand; create private `samepage-demo` repo and push.
- Read model: none
- Targets: Projects per store at month 12; Ship events per store at month 12
- Columns touched: every table (generated data)
- Migrations: none
- Out of scope: Notion demo page (WP-10).
- Done when: counts match test-data.md exactly.

### WP-05: Public repo CI guardrails
Wave: 1
Depends on: WP-02
- Why: guardrails.md must fail merges from the first PR.
- Do: one workflow running every rule in guardrails.md plus Python 3.9 and 3.13 tests.
- Read model: none
- Targets: SKILL.md length; Infra cost per user per month
- Columns touched: none
- Migrations: none
- Out of scope: release packaging.
- Done when: a PR violating each rule fails with a named rule.

### WP-06: Session boot in Claude Code, end to end (template)
Wave: 2
Depends on: WP-01, WP-03, WP-04
- Why: the most-used screen; its structure is copied by every other screen.
- Do: `sp init --backend github` (Setup screen, US-01); `sp boot --surface code` with repo matching and 3 s pull budget; plugin with hooks.json (SessionStart, timeout 3 s) and session-start.sh wrapping output in the data block; config file.
- Read model: Setup, Session boot
- Targets: SessionStart hook duration; Time to first working boot; Public stores created by samepage
- Columns touched: store_meta.*, profile.*, profile_link.*, preference.*
- Migrations: none
- Out of scope: chat, Notion.
- Done when: on a clean Mac, plugin install plus `sp init` plus a new session shows the demo boot in under 10 minutes; offline boot shows cached files with age.

### WP-07: Skill core: chat and Cowork recall, rules
Wave: 3
Depends on: WP-06
- Why: chat is the surface that hurts most today.
- Do: SKILL.md with mode table and never-do rules; references/github-backend.md; boot mode reading `index/boot/{surface}.md` in one call; rules mode (US-15); trigger tests.
- Read model: Chat recall, Rules
- Targets: Reads per boot, GitHub store; SKILL.md length
- Columns touched: preference.*
- Migrations: none
- Out of scope: log, handoff, design modes.
- Done when: on the demo store, a new chat answers "what am I working on?" from one file read, and a code-only rule does not appear in chat.

### WP-08: Log entry from Code and chat, Stop nudge
Wave: 3
Depends on: WP-07
- Why: the store is only useful if entries go in (A3).
- Do: `sp log` and `/sp log` with drafting from `git log -20 --oneline`; skill log mode with confirmation and sha-checked writes; tag creation; Stop hook printing one nudge line when there are commits today and no entry today.
- Read model: Log entry
- Targets: Index rebuild after a push
- Columns touched: ship_event.*, project.*, tag.*, project_tag.*
- Migrations: none
- Out of scope: decisions and design assets.
- Done when: US-05 and US-06 pass on the demo store, including the read-only fallback.

### WP-09: Handoffs both directions
Wave: 3
Depends on: WP-07
- Why: the chat-to-Code link is the second headline feature.
- Do: skill handoff mode; `/sp handoff`, `/sp handoff done`; inbox in boot.
- Read model: Handoff inbox
- Targets: Rows per read
- Columns touched: handoff.*
- Migrations: none
- Out of scope: notifications outside Claude.
- Done when: US-08 and US-09 pass on the demo store.

### WP-10: Notion backend
Wave: 3
Depends on: WP-07
- Why: second backend (ADR-0002).
- Do: references/notion-backend.md with every query from read-models.md; setup creating eight databases (US-02); notion-template/ docs; `sp export --from notion`; Notion demo page from the perf fixture.
- Read model: Setup, Chat recall, Log entry, Proof lookup, Handoff inbox, Decision record, Project detail, Rules, Design pointer
- Targets: Reads per boot, Notion store
- Columns touched: every table through Notion properties
- Migrations: none
- Out of scope: sync with GitHub stores.
- Done when: US-02, US-04, US-06 and US-07 pass on the Notion demo page.

### WP-11: Store template and index Action
Wave: 3
Depends on: WP-03
- Why: chat writes need a rebuild.
- Do: store-template/ with folders, store.md and `.github/workflows/index.yml` (check, then index, then commit only `index/`, skip its own commits, timeout 3 min, pinned actions).
- Read model: Store check
- Targets: Index rebuild after a push; Store Action minutes per month; Silent index failures
- Columns touched: index_build.*
- Migrations: none
- Out of scope: the CLI itself.
- Done when: a chat write to the demo store shows in index/boot/chat.md within 90 s; a broken file fails the job and leaves the old index.

### WP-12: Proof, project detail and decisions
Wave: 3
Depends on: WP-07
- Why: proposals and settled decisions are the main value for chat.
- Do: proof mode with tag AND over up to 3 tags; project mode with archive; decision mode with supersede.
- Read model: Proof lookup, Project detail, Decision record
- Targets: Rows per read
- Columns touched: project.status_id, project.archived_at, project.updated_at, decision.*
- Migrations: none
- Out of scope: proposal writing itself.
- Done when: US-07, US-12 and US-14 pass on the demo store.

### WP-13: Design pointer, Design handoff capture, design brief
Wave: 3
Depends on: WP-01, WP-07
- Why: Claude Design is the fourth surface (ADR-0011).
- Do: design mode; `/sp log design`; design brief export (profile voice, project one-liner, accepted decisions, approved design_system pointer) formatted for pasting into Claude Design; references/design.md.
- Read model: Design pointer, Design handoff capture
- Targets: Rows per read
- Columns touched: design_asset.*
- Migrations: none
- Out of scope: editing tokens.
- Done when: US-10 and US-11 pass, adjusted by the WP-01 result.

### WP-14: Edge cases and error states
Wave: 4
Depends on: WP-08, WP-09, WP-11
- Why: concurrent writes and offline sessions are normal for multi-surface users.
- Do: sha conflict retry once then ask; stale index warning; offline boot; slug collisions; archive instead of delete; rules over the cap warning.
- Read model: Session boot, Log entry, Project detail
- Targets: Silent index failures
- Columns touched: none new
- Migrations: none
- Out of scope: new features.
- Done when: every edge case in fixtures/small has a passing test or a recorded manual check.

### WP-15: Launch kit and release
Wave: 4
Depends on: WP-10, WP-12, WP-13, WP-14
- Why: stars come from the first impression.
- Do: apply the final name (ADR-0010) and owner (ADR-0013); README requirements section that states chat and Cowork writes need the claude.ai GitHub connector's app installed on the store owner's account, with the exact install path verified at release time (A2); README with a 60-second demo gif (ship in Code, proposal in chat cites it); "Works with native memory" section; release workflow building the plugin and `samepage.skill`, bumping `.claude-plugin/plugin.json` version on every release (Claude Code keeps a cached plugin until the version changes, seen in WP-06); a square PNG icon at `.claude-plugin/icon.png` (plugin directory check); 5 timed setup tests.
- Read model: none
- Targets: Time to first working boot
- Columns touched: none
- Migrations: none
- Out of scope: paid promotion.
- Done when: v1.0.0 tagged, install works from a clean machine, setup tests recorded.

### WP-16: Dogfood with the maintainer's own store
Wave: 4
Depends on: WP-10
- Why: the success metric "10 entries per week for 4 weeks" needs a real store, and launch posts need a real story.
- Do: migrate the maintainer's existing Notion projects registry into a samepage Notion store (decided 2026-11-06). Field map: Name to name, Status (ACTIVE, SHIPPED, PARKED, ARCHIVED, UNKNOWN) to the same codes lowercased, Type to type (`client site` to client_site, `idea` type to other with status idea), Description to one_liner (first 140 characters; the rest to problem), Live URL to live_url, Repo to repo_url, Entry ID to slug, Last Verified to last_verified_at, Notes to the page body. Keep the old database read-only for 2 weeks, then archive it.
- Read model: Setup, Log entry
- Targets: none
- Columns touched: project.*
- Migrations: one-off field map, run once
- Out of scope: publishing any of the maintainer's data.
- Done when: maintainer store passes `sp check` and boots on all surfaces.

### WP-17: One-click store and guided setup
Wave: 4
Depends on: WP-11, WP-15 (ADR-0016)
- Why: a stranger must be able to start from claude.ai alone, and stores must not wait on a release.
- Do: public template repo `rx4u/samepage-store-template` built by `scripts/make_template_repo.py` (placeholder profile `Your name`, built index, index Action); the Action pins the tool by commit sha; `sp init` prints the template link when the GitHub CLI is missing and `--use-existing` works with plain git and fills a placeholder profile; `dist/samepage.skill` committed and kept equal to the source by a test; skill setup mode guesses `LOGIN/samepage-store`, fills the profile and tests one write; README with two three-step paths and Notion last.
- Read model: Setup
- Targets: Time to first working boot
- Columns touched: profile.*, store.owner_handle
- Migrations: none
- Out of scope: Windows hooks, hosted setup.
- Done when: a repo made from the template passes `sp check` and rebuilds its index on the first edit; tests and guardrails pass.

### WP-18: Schema 1.1, tool field and roles
Wave: 5
Depends on: WP-17
- Why: every adapter records which tool wrote an entry, and old stores must stay valid (ADR-0017).
- Do: `tool` lookup and the four `-- since 1.1` columns in data-architecture.md; `sp schema` emits `since`; SCHEMA_VERSION 1.1; `sp check` fails a key newer than the store's version; `--tool` on every write command (default `SAMEPAGE_TOOL`), `--surface` defaulting to the tool's role and an explicit `--surface` winning (B31); writers drop 1.1 keys on 1.0 stores with the note `samepage: note: store is schema 1.0; tool not recorded` (B31); index header carries the store's version (B22); handoff lines show `via TOOL`; `sp init`, store-template and the template repo at 1.1; plugin commands pass `--tool claude_code`; entry-schema.md and notion-backend.md document the keys; `sp export` maps Tool columns.
- Read model: Log entry, Decision record, Design pointer, Handoff inbox, Session boot
- Targets: Schema compatibility; Boot file size per surface
- Columns touched: tool.*, ship_event.tool_id, decision.tool_id, design_asset.tool_id, handoff.from_tool_id, store_meta.schema_version
- Migrations: none (additive minor version; upgrade is a store.md edit plus an Action pin bump)
- Out of scope: per-tool rules or handoff targets.
- Done when: fixtures/small (1.0) passes unchanged; a 1.0 store with a `tool` key fails; `sp log ship --tool cursor` writes `tool: cursor` on 1.1 and drops it on 1.0; tests and guardrails pass.

### WP-19: `sp context` instruction blocks
Wave: 5
Depends on: WP-18
- Why: agents in other tools must be told samepage exists and how to use it, without store content in product repos (ADR-0018).
- Do: sp/context.py: block template per tool, marker-safe insert and replace, refuse unmatched or repeated markers, keep line endings, `--dry-run`, `--refresh` over the 5 known paths, Cursor `.mdc` frontmatter.
- Read model: Instruction file
- Targets: none
- Columns touched: none
- Migrations: none
- Out of scope: hooks in other tools.
- Done when: tests prove user lines are kept byte for byte, idempotence, refusal on broken markers, and no boot-file line in the block.

### WP-20: Portable skill
Wave: 5
Depends on: WP-18
- Why: one SKILL.md for every tool that reads skills (ADR-0018).
- Do: skill-workshop phases 3 to 7 on skills/samepage/: CLI resolution (plugin root, then `sp` on PATH, then read-only), surface and tool detection table, `--tool` on writes, 1.1 key rule from the boot header; rebuild dist/samepage.skill with scripts/package_skill.py.
- Read model: Chat recall, Log entry
- Targets: SKILL.md length
- Columns touched: none new
- Migrations: none
- Out of scope: new modes.
- Done when: tests/test_skill.py passes, dist matches source, SKILL.md under 500 lines.

### WP-21: `install.sh` and `sp setup`
Wave: 5
Depends on: WP-19
- Why: two commands from nothing to a connected tool (ADR-0020).
- Do: install.sh (git clone or pull into `$SAMEPAGE_HOME/tool`, shim, PATH hint); sp/setup.py for codex, cursor, copilot, gemini, windsurf, claude-desktop, claude-code (prints plugin command): MCP entry, skill copy, `sp context`, backups, parse-failure snippet, `--dry-run`, `--print`.
- Read model: Tool setup
- Targets: Time to first working boot
- Columns touched: none
- Migrations: none
- Out of scope: Windows, uninstall, package managers.
- Done when: tests with a temp HOME cover add, idempotent re-run, other entries kept, JSONC refusal, Codex TOML replace, unknown tool exit 2; install.sh test runs `sp --help` through the shim.

### WP-22: `sp mcp` local stdio server
Wave: 5
Depends on: WP-18
- Why: one intake path for every MCP-capable tool (ADR-0018).
- Do: sp/mcp.py: newline-delimited JSON-RPC 2.0, both protocol eras (B24: `initialize` with legacy version negotiation, `server/discover` and `_meta` versions for 2026-07-28), tools/list with input schemas and read-only hints, tools/call mapping to `sp` child processes, dry-run-then-confirm writes with a pinned id, time and preview hash, Notion one-liner, errors as tool results.
- Read model: MCP session
- Targets: Rows per read; MCP tool call time
- Columns touched: as the mapped write screens
- Migrations: none
- Out of scope: resources, prompts, HTTP transport.
- Done when: a protocol test drives initialize, tools/list, every read tool and the write flow on a temp store; a write without a matching confirm writes nothing; every stdout line parses as JSON.

### WP-23: Test in each tool (Phase 3)
Wave: 5
Depends on: WP-20, WP-21, WP-22
- Why: only tested tools get a tick (owner answer Q1, 2026-11-06).
- Do: run the per-tool checklist on Raja's Mac for Claude Code, claude.ai, Cowork and Claude Desktop; other tools only if a login becomes available; record each run in docs/build/tool-ledger.md.
- Read model: MCP session, Session boot, Chat recall
- Targets: Time to first working boot
- Columns touched: none
- Migrations: none
- Out of scope: fixing tool vendors' bugs.
- Done when: every tool in the README table has a ledger row with date, version and result.

### WP-24: Reposition and release v1.0.0
Wave: 5
Depends on: WP-23
- Why: launch copy must match what was tested (ADR-0018, ADR-0019).
- Do: README leads with Claude, adds a tool table (ticks only from the ledger, others "community-tested"), install section for other tools; new gif; landing page; release workflow run by Raja (`workflow_dispatch`, version 1.0.0).
- Read model: none
- Targets: Time to first working boot
- Columns touched: none
- Migrations: none
- Out of scope: ChatGPT (ADR-0019).
- Done when: release published and page live.

## Parallel work
Wave 5: WP-19, WP-20 and WP-22 can run in parallel after WP-18 (separate files: sp/context.py, skills/samepage/, sp/mcp.py); WP-21 needs WP-19 (setup calls `sp context`). All three add a subcommand to sp/__main__.py, so each adds one self-contained block.
Safe pairs in wave 1: WP-01 with WP-02; WP-03, WP-04 and WP-05 after WP-02 (separate folders: sp/index.py, sp/fixtures.py, .github/). Safe in wave 3: WP-09, WP-10, WP-11 and WP-12 in parallel (separate skill reference files and sp modules); WP-08 and WP-13 both touch commands/sp.md, so run them in sequence.

## Definition of done (every change)
- Meets the targets it touches, with before and after numbers in the PR
- Data dictionary and read model updated
- Perf fixture check passes (index time, boot size, page chains)
- Guardrails pass
- An ADR if it changes a layer, limit, dependency or rule
