# Builder check

Run: 2026-11-06, reader: cold read (deliberate, documents only; no subagent because none was requested)

| # | Question (quoted line) | Group | Resolution |
|---|---|---|---|
| B1 | prd US-03: "plus the section for the project ... under 2,000 tokens total" vs targets: 2,000 tokens is the boot file alone | Agent call | Agent call: boot file 2,000 tokens (8,000 chars) plus project file 1,500 tokens (6,000 chars). US-03 and targets.md updated. |
| B2 | data-architecture: "general handoffs use the reserved project slug `general`". Who creates it, and does it show in boot and proof? | Agent call | Agent call: setup creates project `general` (type other, status active); excluded from boot project lists, projects pages and proof. Added to data-architecture.md and read-models.md. |
| B3 | read-models Rules: "Page size: 50, single page". What if a store has over 50 active rules? | Agent call | Agent call: `sp check` fails above 50 active rules in total and warns above 20 for one surface. Added to read-models.md. |
| B4 | Rule order is "Created asc" in the Notion query but unstated for GitHub boot files | Agent call | Agent call: rules are ordered created_at ASC, id ASC on every surface and backend. Added to read-models.md. |
| B5 | Proof lookup: GitHub "Shipped = project has at least one ship_event; archived projects are included" vs Notion "Status in [shipped, active]" | Agent call | Agent call: Notion Projects gets a rollup property "Last shipped" (max of Ship Events Occurred); proof filters "Last shipped is not empty" and sorts by it. Serve-only property, not in the contract. read-models.md and data-architecture.md updated. |
| B6 | Log entry: "project upsert: project.status_id". When does logging change project status? | Agent call | Agent call: an event of kind shipped or launched sets status to shipped when it is idea, active or unknown, and sets shipped_on if empty; it never changes parked or archived. Added to read-models.md. |
| B7 | surface lookup includes `design`, but Claude Design cannot read the store (ADR-0011). Can a handoff go to design? | Agent call | Agent call: to_surface `design` is rejected by `sp check` and the skill in v1; the design brief export is used instead. Added to data-architecture.md. |
| B8 | Store Action "commit only `index/`" to the default branch. What if the user protects the branch? | Agent call | Agent call: the store template ships with no branch protection; README says protection must allow the Action to push or the index will not rebuild. Added to system-design.md. |
| B9 | `sp log` from Code "commits and pushes". What if the local clone is behind or dirty? | Agent call | Agent call: `sp` runs `git pull --rebase` before writing; on conflict it stops, prints the conflicting path and writes nothing. Added to read-models.md. |
| B10 | Where does the `sp` command live on the user's machine? | Agent call | Agent call: no PATH install. The plugin bundles `sp/`; hooks and `/sp` commands call `python3 -m sp` from the plugin root. Setup is `/sp init` inside Claude Code. Added to system-design.md. |
| B11 | Session boot: "Notion: not run from the hook". What does a Notion user see at session start? | Agent call | Agent call: for a Notion store the hook prints one line telling Claude to run the skill's Notion boot before the first task. Added to read-models.md. |
| B12 | Filenames use `{id8}`. What if two uuids share 8 characters? | Agent call | Agent call: the writer regenerates the uuid if the path exists; `sp check` fails on duplicate ids. Added to data-architecture.md. |
| B13 | Cowork can run locally or in the cloud. Which surface code and path apply? | Agent call | Agent call: both use surface `cowork` and the connector path, same as chat. Added to read-models.md. |
| B14 | "repo_url normalised https URL without .git". What about SSH remotes and case? | Agent call | Agent call: `git@host:owner/repo.git` becomes `https://host/owner/repo`, host lowercased, owner and repo lowercased, trailing `.git` and `/` removed. Added to data-dictionary.md. |
| B18 | data-architecture: "YAML frontmatter holds every column". How are `_id` foreign keys named and valued in a file? | Agent call | Agent call: key naming rule added to data-architecture.md (B18), found while starting WP-02. |
| B19 | read-models Chat recall: "Same sections as Session boot" vs its column list, which has no ship_event columns | Agent call | Agent call: chat and cowork boot files follow the column list, no recent ships; proof lookup serves shipped work. |
| B20 | read-models Session boot: "repo match via project_repo", but no serve file holds that index and readers may not walk raw folders | Agent call | Agent call: `index/repos.md` added to the serve files. |
| B21 | system-design: plugin under `plugin/`, CLI under `sp/`, but an installed plugin only carries its own folder | Agent call | Agent call: the repo root is the plugin (B21 in system-design.md). |
| B15 | prd Open questions: "Final public name" | User call | User: samepage, CLI `sp` (ADR-0010 accepted 2026-11-06). |
| B16 | ADR-0013: repo owner account | User call | User: personal account rx4u (ADR-0013 accepted 2026-11-06). |
| B17 | WP-16: migrate the maintainer's existing Notion registry or start fresh | User call | User: migrate, keep the old database read-only for 2 weeks (WP-16 updated). |

| B22 | read-models header `schema {version}`: the sp version or the store's? A chat reader needs the store's to know if it may write 1.1 keys | Agent call | Agent call: the header carries the store's schema_version (read-models.md paging conventions). |
| B23 | data-architecture "Readers tolerate unknown keys" vs `sp check` rejecting unknown keys, with a sha-pinned Action running an older sp | Agent call | Agent call: `since` markers; writers emit a key only on stores at that version; check fails newer keys (data-architecture.md, Schema evolution). |
| B24 | MCP spec 2026-07-28 drops `initialize`; older clients still send it | Agent call | Agent call: `sp mcp` is dual-era (system-design.md, Tool adapters). |

Run: 2026-11-06, wave 5 (ADR-0017 to ADR-0020), reader: cold-read subagent given only the documents, 20 items.

| # | Question (quoted line) | Group | Resolution |
|---|---|---|---|
| B25 | read-models MCP session: tools map to `sp project`, `sp rules`, `sp handoff show` that the docs do not list | Answered by the docs | Those commands exist (docs/build/wave3-contract.md, CLI interface); the MCP argument table now names each command. |
| B26 | WP-22 "tools/list with input schemas": no argument names | Agent call | Agent call: argument table in read-models.md, MCP session. |
| B27 | prd US-18 used `sp setup cursor`, a snippet-only (unverified) row | Agent call | Agent call: US-18 uses gemini; unverified rows print a snippet and exit 0. |
| B28 | prd Never do "any line outside the samepage entry" vs JSON re-serialising | Agent call | Agent call: other entries keep content and order; whitespace may be normalised (prd.md, ADR-0020). |
| B29 | ADR-0020 TOML block ends at "the next table header", which a `.env` subtable would be | Agent call | Agent call: block includes `[mcp_servers.samepage.*]`; env written inline (ADR-0020). |
| B30 | ADR-0018 `confirm` format, hash and state unstated | Agent call | Agent call: base64url JSON of id, now and a 16-hex sha256 of the preview; stateless; no expiry (ADR-0018). |
| B31 | WP-18 note text; `--tool` with a conflicting `--surface`; stores newer than sp | Agent call | Agent call: note `samepage: note: store is schema 1.0; tool not recorded`; explicit `--surface` wins; newer major fails (existing check), newer minor keys fail as unknown. |
| B32 | ADR-0018 block content only paraphrased; frontmatter placement | Agent call | Agent call: exact text in system-design.md, Instruction block; frontmatter above the start marker only on files sp creates. |
| B33 | system-design V/U rule: per cell or per row? | Agent call | Agent call: configs only; skill folders and instruction files are written for every listed path (ADR-0020). |
| B34 | Copilot: CLI config, VS Code config or both? | Agent call | Agent call: CLI always, VS Code when its User folder exists (ADR-0020). |
| B35 | Which python3 for the MCP entry; PATH for git in GUI apps; SAMEPAGE_HOME scope | Agent call | Agent call: `sys.executable`; env carries PATH and SAMEPAGE_HOME (ADR-0020). PYTHONPATH replaced by `sp_run.py` (B45). |
| B36 | ADR-0020 `SAMEPAGE_REF` default `main` runs unreleased code | Agent call | Agent call: keep `main` (same channel as the template pin and the README skill link, ADR-0016; no release exists yet); revisit after the first release (v1.1.0, B46). Flagged to Raja in the Phase 0 report. |
| B37 | `sp context --tool` takes setup names or codes; `--refresh` folder and tool | Agent call | Agent call: codes only; `--refresh` in `--cwd`, tool kept or inferred from path (read-models.md, Instruction file). |
| B38 | MCP error mapping | Agent call | Agent call: protocol faults are JSON-RPC errors; child exit other than 0 is `isError: true` (read-models.md). |
| B39 | targets 1 s p95 vs test at 2 s; does MCP boot pull | Agent call | Agent call: test asserts p95 of 20 calls under 1 s on a store with no remote; boot pulls like the hook; writes pull (B9). |
| B40 | ADR-0018 "enforced by the server" overclaims ADR-0007 rule 1 | Agent call | Agent call: reworded; the server enforces preview equals write; the user's yes stays the agent's job, stated in every write tool description. Flagged to Raja. |
| B41 | ADR-0018 "does not write" without sp vs ADR-0012 "writing files directly" | Agent call | Agent call: ADR-0018 replaces that sentence for local agents; note added to ADR-0012 More information. |
| B42 | data-dictionary tool_id read by Project detail vs ADR-0017 "handoff lines only" | Agent call | Agent call: tool is written, not printed, except handoff lines; dictionary fixed. |
| B43 | Is every MCP read result wrapped in the data block? | Agent call | Agent call: yes, every read tool result (ADR-0018). `sp boot` wraps its own output already. |
| B44 | Claude Code passes only `structuredContent` to the model, so a dry run whose preview sat only in the text block reached the user as a bare confirm token (found in a real client run, 2026-11-06) | Agent call | Agent call: a dry run puts `preview`, `ask` and `confirm` in `structuredContent` and the same text in the text block; the CLI line about `--id` and `--now` is left out of both (ADR-0018). |
| B45 | Gemini CLI refuses a `PYTHONPATH` override in an MCP server env, so the B35 entry never started there (found with Gemini CLI 0.67.0, 2026-11-06) | Agent call | Agent call: the entry runs `sys.executable sp_run.py mcp --tool CODE`; `sp_run.py` at the samepage root imports the package next to it, and `env` carries only PATH and SAMEPAGE_HOME (ADR-0020). Gemini CLI also starts MCP servers only in folders the user trusts; setup says so. |
| B46 | Plugin still 1.0.0 while skill and schema are 1.1, and Claude Code serves a cached plugin until its version changes | Agent call | Agent call (owner said "do it all from your end", 2026-11-06): plugin bumped to 1.1.0, so the first release is v1.1.0, matching the skill and schema 1.1. No release existed, so no user is skipped a version. |

## Open user calls
