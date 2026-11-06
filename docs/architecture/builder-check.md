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
| B15 | prd Open questions: "Final public name" | User call | User: samepage, CLI `sp` (ADR-0010 accepted 2026-11-06). |
| B16 | ADR-0013: repo owner account | User call | User: personal account rx4u (ADR-0013 accepted 2026-11-06). |
| B17 | WP-16: migrate the maintainer's existing Notion registry or start fresh | User call | User: migrate, keep the old database read-only for 2 weeks (WP-16 updated). |

## Open user calls
