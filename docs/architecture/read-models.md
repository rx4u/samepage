# Read models

There is no web UI. A screen is a moment on a surface where the store is read or written: a hook run, a skill mode or a `sp` command. Each has one read contract per backend.

Agent calls that apply to every screen:
- B4: rules are ordered created_at ASC, id ASC on every surface and backend.
- B13: local and cloud Cowork both use surface `cowork` and the connector path, same as chat.
- B2: the reserved project `general` never appears in boot project lists, projects pages or proof.

Paging conventions, used by every list below:
- GitHub: the index builder writes pre-sorted pages of 20 rows (`{name}-1.md`, `{name}-2.md`). Rows inside a page are sorted by the screen's sort key DESC, then id DESC. The page footer line `next: {file}` is the cursor; no footer means last page. This is keyset paging computed at write time. Readers never skip into a list by row count.
- Notion: `page_size` 20 (never above 50), `start_cursor` from the previous response's `next_cursor`, explicit `sorts` with a tie-break on `created_time`.
- Every serve file starts with a header line: `built: {iso time} from {commit_sha8} schema {version}`. Agent call (B22): `{version}` is the store's own `store_meta.schema_version` (from store.md), not the version of the `sp` that built it, so a reader that reads only a boot file knows whether it may write 1.1 keys (B23).
- Since 1.1 every write screen records `tool` (or `from_tool` on handoffs) when the store is 1.1 or higher and the writer knows its tool (ADR-0017).

## Screen: Setup
- Stories: US-01, US-02
- First paint: the six profile questions, one at a time; no store reads except an existence check
- Query: GitHub `gh repo view {owner}/samepage-store --json name,visibility` (existence only). Notion: search for a page titled "samepage" owned by the user, page_size 5
- Columns: store_meta.backend_id, store_meta.owner_handle, backend.code
- Filters: none
- Page size: 5 for the Notion existence search; 1 for GitHub
- Counts: none
- Index: none needed; existence check by name
- On action: profile questions are asked only after the backend is chosen
- Writes: `sp init` creates store.md, profile.md, profile/links/*, rules/* from answers and pushes; Notion setup creates the eight databases and the Profile row. Writes store_meta.*, profile.*, profile_link.*, preference.*
- Code: `sp/init.py` and skill reference `references/setup.md`

## Screen: Session boot
- Stories: US-03, US-08, US-10, US-15, US-16
- First paint: Code session start. Prints profile, rules for code, the 10 most recently updated active projects, 5 latest ship events, open handoffs to code (max 5), then the current project's section if the git remote matches a project
- Query: GitHub (local clone) `sp boot --surface code` reads `index/boot/code.md`, then `index/project/{slug}.md` when `project.repo_url` equals the normalised `git remote get-url origin`. Notion: not run from the hook. Agent call (B11): for a Notion store the hook prints one line telling Claude to run the skill's Notion boot (the Chat recall queries with surface code) before the first task
- Columns: profile.display_name, profile.headline, profile.voice, preference.rule, preference.surface_id, preference.is_active, project.slug, project.name, project.status_id, project.one_liner, project.repo_url, project.updated_at, ship_event.summary, ship_event.occurred_at, handoff.title, handoff.from_surface_id, handoff.from_tool_id, handoff.to_surface_id, handoff.status_id, design_asset.kind_id, design_asset.status_id, design_asset.title, design_asset.tokens_repo_url, design_asset.tokens_path, decision.title, decision.status_id, index_build.commit_sha, index_build.started_at, index_build.status_id, store_meta.schema_version, surface.code, project_status.code
- Filters: preference is_active = true and (surface_id empty or = code); project status = active; handoff status = open and to_surface = code; project section decisions status = accepted
- Page size: fixed caps, no paging at boot: 20 rules, 10 projects, 5 ship events, 5 handoffs; project section 10 events, 10 decisions, 5 design assets
- Counts: open handoffs to code, shown as "and N more" when over 5
- Index: `index/boot/code.md` (built from project_status_updated, ship_event_recent, handoff_inbox, preference_active_surface); `index/project/{slug}.md` (built from ship_event_project_recent, decision_project_recent, design_asset_project_kind); repo match via project_repo
- On action: full handoff bodies load only when the user starts a handoff (Handoff inbox)
- Writes: none. If `git pull --ff-only` exceeds 3 s the hook uses the cached files and prints their age
- Code: plugin `hooks/session-start.sh` calling `sp boot`; output wrapped in a `<samepage data>` block labelled as data, not instructions. Other coding tools reach the same read through the MCP `boot` tool or `sp boot --surface code --cwd .` (MCP session screen, ADR-0018)

## Screen: Chat recall
- Stories: US-04, US-15
- First paint: chat or Cowork, first message that needs the owner's context. Same sections as Session boot for the chat or cowork surface, without a project section
- Query: GitHub `get_file_contents(index/boot/{surface}.md)` through the GitHub connector, one call. Notion: 4 queries: Profile (page_size 1), Rules (Active = true and Surface in [empty, surface], page_size 20, sort Created asc), Projects (Status = active, page_size 10, sort Last edited desc), Handoffs (Status = open and To = surface, page_size 5, sort Created desc)
- Columns: profile.display_name, profile.headline, profile.location, profile.bio, profile.voice, profile_link.label, profile_link.url, profile_link.sort_order, preference.rule, preference.surface_id, preference.is_active, project.slug, project.name, project.status_id, project.one_liner, project.updated_at, handoff.title, handoff.from_surface_id, handoff.from_tool_id, handoff.to_surface_id, handoff.status_id, surface.code, store_meta.schema_version
- Filters: as Session boot, with surface = chat or cowork
- Page size: 20 rules, 10 projects, 5 handoffs, 5 links
- Counts: open handoffs to this surface
- Index: `index/boot/chat.md`, `index/boot/cowork.md`; Notion sorts as listed
- On action: project detail loads only when the conversation names a project (Project detail)
- Writes: none
- Code: skill `SKILL.md` boot mode, references `github-backend.md` and `notion-backend.md`

## Screen: Log entry
- Stories: US-05, US-06
- First paint: a drafted entry shown to the user for confirmation, with the target file path (GitHub) or database (Notion)
- Query: the project row by slug: GitHub `projects/{slug}.md` (one read), Notion Projects filter Slug = {slug}, page_size 1
- Columns: project.id, project.slug, project.name, project.status_id, project.live_url, project.shipped_on, ship_event.kind_id, ship_event.summary, ship_event.proof_url, ship_event.metric_label, ship_event.metric_value, ship_event.metric_unit, ship_event.occurred_at, ship_event.surface_id, ship_event.tool_id, tag.slug, tag.label, event_kind.code, tool.code, store_meta.schema_version
- Filters: slug equality
- Page size: 1
- Counts: none
- Index: project slug is the filename (GitHub) and a unique property (Notion)
- On action: if the project does not exist, ask for name, type and one-liner, then create it. Agent call (B6): an event of kind shipped or launched sets project status to shipped when it is idea, active or unknown, and sets shipped_on if empty; it never changes parked or archived. Agent call (B9): before writing from Code, `sp` runs `git pull --rebase`; on conflict it stops, prints the conflicting path and writes nothing
- Writes: new `events/...` file or Ship Events row: ship_event.*; project upsert: project.status_id, project.shipped_on, project.updated_at, project.last_verified_at, project.live_url; new tags: tag.*, project_tag.*. GitHub from Code: `sp log` writes, runs `sp index`, commits and pushes. GitHub from chat: one create_or_update_file for the event, one for the project if changed; the store Action rebuilds the index
- Code: `sp/log.py`, skill log mode

## Screen: Proof lookup
- Stories: US-07
- First paint: up to 20 projects with at least one ship event, newest ship first: name, one-liner, role, outcome, latest event summary and date, proof_url or live_url, metric if any
- Query: GitHub `index/proof-1.md`; with tags, `index/tags/{slug}.md` per tag (max 3 tags). Notion: Projects filter "Last shipped" is not empty and Slug is not `general` and Tags contains each tag, sort Last shipped desc, page_size 20; then Ship Events filter Project in the returned ids, sort Occurred desc, page_size 50
- Columns: project.slug, project.name, project.type_id, project.one_liner, project.problem, project.role, project.outcome, project.live_url, project.shipped_on, project_tag.project_id, project_tag.tag_id, tag.slug, tag.label, ship_event.project_id, ship_event.kind_id, ship_event.summary, ship_event.proof_url, ship_event.metric_label, ship_event.metric_value, ship_event.metric_unit, ship_event.occurred_at, project_type.code, event_kind.code
- Filters: tag slugs (AND across up to 3 tags); "Shipped" = project has at least one ship_event; archived projects are included
- Page size: 20, keyset on (latest occurred_at, project id); tag index files hold up to 50 rows on one page so an AND of 3 tags is an intersection of at most 150 rows in the reader
- Counts: total matching projects, from the index header
- Index: `index/proof-{n}.md` from ship_event_recent; `index/tags/{slug}.md` from project_tag_by_tag
- On action: full project history loads only when the user picks one (Project detail)
- Writes: none
- Code: skill proof mode, `sp proof`

## Screen: Handoff inbox
- Stories: US-08, US-09
- First paint: open and picked-up handoffs to this surface, newest first: title, project, from surface and tool (`from chat via claude_ai`), created time. Since 1.1 a handoff to `code` is picked up by whichever coding tool opens next (ADR-0017)
- Query: GitHub `index/handoffs-{surface}-1.md`; full brief from `handoffs/{id8}.md` on pick-up. Notion: Handoffs filter To = surface and Status in [open, picked_up], sort Created desc, page_size 20
- Columns: handoff.id, handoff.project_id, handoff.from_surface_id, handoff.from_tool_id, handoff.to_surface_id, handoff.status_id, handoff.title, handoff.body, handoff.created_at, handoff.picked_up_at, handoff.done_at, project.slug, handoff_status.code, surface.code, tool.code
- Filters: Open = status open; In progress = status picked_up
- Page size: 20, keyset on (created_at, id)
- Counts: open count per surface, from the index header
- Index: handoff_inbox
- On action: body loads only when the user picks a handoff
- Writes: create sets every handoff column with status open; pick up sets handoff.status_id = picked_up and handoff.picked_up_at; close sets handoff.status_id = done or dropped and handoff.done_at
- Code: skill handoff mode, plugin command `/sp handoff`

## Screen: Design pointer
- Stories: US-10
- First paint: the project's design assets grouped by kind, approved first: title, status, tokens repo and path, source link
- Query: GitHub `index/project/{slug}.md` design section. Notion: Design Assets filter Project = id, sort Updated desc, page_size 20
- Columns: design_asset.id, design_asset.project_id, design_asset.kind_id, design_asset.status_id, design_asset.surface_id, design_asset.tool_id, design_asset.title, design_asset.source_url, design_asset.tokens_repo_url, design_asset.tokens_path, design_asset.updated_at, asset_kind.code, asset_status.code, tool.code
- Filters: kind; status approved shown before draft; superseded hidden
- Page size: 20, keyset on (updated_at, id)
- Counts: assets per kind
- Index: design_asset_project_kind
- On action: the skill never fetches the tokens file at recall; Code reads it from the product repo when building
- Writes: create sets every design_asset column; approve sets status_id and updated_at; a new approved design_system sets the previous approved one to superseded
- Code: skill design mode, `sp log design`

## Screen: Design handoff capture
- Stories: US-11
- First paint: a drafted design_asset of kind handoff_bundle from the Claude Design bundle in the current Code session, shown for confirmation
- Query: project row by slug, as Log entry
- Columns: design_asset.project_id, design_asset.kind_id, design_asset.title, design_asset.source_url, project.slug, asset_kind.code
- Filters: slug equality
- Page size: 1
- Counts: none
- Index: project slug filename or unique property
- On action: none
- Writes: design_asset.* with kind handoff_bundle, status approved, surface code
- Code: plugin command `/sp log design`

## Screen: Decision record
- Stories: US-12
- First paint: the drafted decision with title, reason and project, shown for confirmation; when superseding, the decision being replaced
- Query: GitHub `index/project/{slug}.md` decisions section (last 10); the superseded file by id. Notion: Decisions filter Project = id, sort Decided desc, page_size 10
- Columns: decision.id, decision.project_id, decision.status_id, decision.surface_id, decision.tool_id, decision.superseded_by_id, decision.title, decision.reason, decision.body, decision.decided_at, decision_status.code, tool.code
- Filters: Current = status accepted
- Page size: 10, keyset on (decided_at, id)
- Counts: accepted decisions per project
- Index: decision_project_recent
- On action: body loads only on request
- Writes: new decision with every column; superseding sets the old decision.status_id = superseded, decision.superseded_by_id and decision.updated_at
- Code: skill decision mode

## Screen: Project detail
- Stories: US-14
- First paint: one project's fields, its last 10 ship events, last 10 accepted decisions, approved design assets and open handoffs
- Query: GitHub `index/project/{slug}.md`. Notion: Projects filter Slug = slug (page_size 1), then Ship Events, Decisions and Design Assets each filtered by Project and page_size 10
- Columns: project.id, project.slug, project.name, project.status_id, project.type_id, project.one_liner, project.problem, project.role, project.outcome, project.live_url, project.repo_url, project.started_on, project.shipped_on, project.last_verified_at, project.archived_at, ship_event.summary, ship_event.occurred_at, ship_event.kind_id, ship_event.surface_id, decision.title, decision.reason, decision.decided_at, tag.slug, project_status.code, project_type.code
- Filters: slug equality
- Page size: 10 per child list; older items through the full lists on request
- Counts: events, decisions, design assets per project, from the file header
- Index: ship_event_project_recent, decision_project_recent, design_asset_project_kind
- On action: archive asks for confirmation
- Writes: archive sets project.status_id = archived, project.archived_at, project.updated_at
- Code: skill project mode

## Screen: Rules
- Stories: US-15
- First paint: active rules grouped by surface (all surfaces first), oldest first
- Query: GitHub `index/rules.md`. Notion: Rules filter Active = true, sort Created asc, page_size 50
- Columns: preference.id, preference.rule, preference.surface_id, preference.is_active, preference.created_at, surface.code
- Filters: Active; surface
- Page size: 50, single page. Agent call (B3): `sp check` fails above 50 active rules in total and warns above 20 for any one surface
- Counts: active rules per surface
- Index: preference_active_surface
- On action: none
- Writes: add sets every preference column; pause sets preference.is_active = false and preference.updated_at
- Code: skill rules mode

## Screen: Store check
- Stories: US-13
- First paint: pass or fail, then per-entity counts, BOOT size per surface, last build status, then each failure as path, field, problem, allowed values
- Query: `sp check` reads every file in the local clone; it is the only reader allowed to scan the whole store, and it runs on the maintainer's or owner's machine and in the store Action, never at boot or recall
- Columns: store_meta.schema_version, store_meta.backend_id, store_meta.owner_handle, store_meta.created_at, index_build.status_id, index_build.commit_sha, index_build.entry_count, index_build.boot_chars, index_build.error, index_build.started_at, index_build.finished_at
- Filters: `--only {entity}`
- Page size: failures print 50 at a time with `--page`; counts are complete
- Counts: rows per entity, failures per rule
- Index: index_build_recent for the last build
- On action: none
- Writes: none (index_build rows are written by `sp index`, not by check)
- Code: `sp/check.py`

## Screen: MCP session
- Stories: US-16, US-17
- First paint: a coding tool (Codex, Cursor, Copilot, Gemini CLI, Windsurf, Claude Desktop) starts `sp mcp --tool CODE`; `initialize` answers with server info and the tools capability; `tools/list` returns 11 tools; nothing reads the store until a tool is called
- Query: each read tool runs one `sp` read command as a child process: `boot` = Session boot (`index/boot/{surface}.md`, then `index/project/{slug}.md` on a repo match via `index/repos.md`); `project` = Project detail; `proof` = Proof lookup; `handoffs` = Handoff inbox; `handoff_show` = one `handoffs/{id8}.md`; `rules` = Rules. Each write tool runs one `sp` write command: `log_ship` = Log entry, `log_decision` = Decision record, `handoff_new` and `handoff_status` = Handoff inbox writes, `rule_add` = Rules write. Notion stores: every tool returns one line pointing to the skill
- Columns: tool.code, surface.code
- Note: tool.code and surface.code are the session's; each tool call returns exactly the columns of the screen it maps to, listed under that screen
- Filters: as the mapped screen; the session surface is the tool's default role (ADR-0017) unless the call names one
- Page size: as the mapped screen; `proof` and `handoffs` take `page` (default 1), which names a pre-built page file, never a row offset
- Counts: as the mapped screen
- Index: the serve files of the mapped screen; no new index
- On action: write tools default to `dry_run: true`. A dry run returns the paths, the file text and a `confirm` value (pinned id, pinned time, preview hash). A write call must carry that value; the server rebuilds the change from it and writes only when the rebuilt preview hashes the same (ADR-0007, ADR-0018)
- Writes: as the mapped write screens, with `tool` / `from_tool` set to the session tool on 1.1 stores
- Code: `sp/mcp.py`, `sp mcp`
- Agent call (B26), tool arguments. Each tool runs the command shown; every argument maps to the flag of the same name; `surface` defaults to the session role; write tools also take `dry_run` (boolean, default true) and `confirm` (string). Store reads use the local clone; `boot` pulls exactly as the hook does (3 s budget), writes pull per B9 (B39).

| Tool | Command | Arguments (required in bold) |
|---|---|---|
| boot | `sp boot --surface S --cwd DIR` | project_dir (the workspace path), surface |
| project | `sp project SLUG` | **slug** |
| proof | `sp proof [--tag T]... --page N` | tags (array, at most 3), page (default 1) |
| handoffs | `sp handoff list --surface S --page N` | surface, page |
| handoff_show | `sp handoff show ID8` | **id** |
| rules | `sp rules list` | none |
| log_ship | `sp log ship ...` | **project**, **kind**, **summary**, proof_url, metric_label, metric_value, metric_unit, occurred_at, tags, new_project_name, new_project_type, new_project_one_liner |
| log_decision | `sp log decision ...` | **project**, **title**, **reason**, body, supersedes |
| handoff_new | `sp handoff new ...` | **project**, **to** (code, chat or cowork), **title**, **body** |
| handoff_status | `sp handoff start`, `done` or `drop` ID8 | **id**, **action** (start, done, drop) |
| rule_add | `sp rules add ...` | **rule**, surface |

- Agent call (B38), errors: a malformed message or unknown method is a JSON-RPC error (-32700, -32600, -32601, -32602; -32022 for an unsupported protocol version); a child `sp` exit other than 0 returns a normal result with `isError: true` and the child's message as text.

## Screen: Instruction file
- Stories: US-19
- First paint: the path of the instruction file and the block that will be written, or "unchanged"
- Query: one read of the target file in the project folder (for example `AGENTS.md`); no store reads
- Columns: tool.code
- Filters: none
- Page size: 1 file per tool; `--refresh` reads at most the 5 known instruction paths in one folder
- Counts: none
- Index: none needed; fixed paths per tool (system-design.md, Tool adapters)
- On action: `--dry-run` prints and writes nothing
- Writes: only the lines between `<!-- samepage:start -->` and `<!-- samepage:end -->`, or a new block appended after the user's last line with one blank line between; a new file when none exists (Cursor and Windsurf files get their frontmatter above the start marker, only when sp creates the file). Exact block text: system-design.md, Instruction block. Never store content (ADR-0018)
- Agent call (B37): `--tool` takes tool codes (codex, copilot, gemini_cli, cursor, windsurf); a code with no instruction file exits 2 and lists the valid ones. `--refresh` works in `--cwd` (default the current folder) and keeps each block's tool, inferring it from the path when the block names none (AGENTS.md is codex). Exit 1 and no change on an unmatched or repeated marker
- Code: `sp/context.py`, `sp context`

## Screen: Tool setup
- Stories: US-18
- First paint: the planned changes for one tool: MCP config path and entry, skill folder, instruction file; or the snippet to paste when the path is not listed for this OS
- Query: one read of the tool's MCP config file and an existence check of its skills folder; no store reads
- Columns: tool.code, store_meta.backend_id
- Filters: none
- Page size: 1 config file
- Counts: none
- Index: none needed
- On action: `--dry-run` prints the plan and writes nothing; a config that does not parse is never changed
- Writes: the `samepage` entry in the tool's MCP config (backup `FILE.samepage-backup` before the first change), a copy of `skills/samepage/` in the tool's skills folder, and the Instruction file write. No store writes
- Code: `sp/setup.py`, `sp setup`, `install.sh`
