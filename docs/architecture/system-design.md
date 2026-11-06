# System design

## Stack
| Layer | Choice | Why | Alternative rejected |
|---|---|---|---|
| Store format | Markdown files with flat YAML frontmatter (GitHub) or Notion databases | Human-readable, diffable, editable by hand, readable by every Claude surface through existing connectors | SQLite file (not readable from chat), JSON files (unfriendly to edit by hand) |
| CLI | `sp`, Python 3.9+ standard library only, single package | No install step beyond the plugin; python3 ships with git on macOS (Xcode CLT) and on Linux | Node CLI (Claude Code's native installer no longer guarantees Node), Go binary (release pipeline per OS) |
| Claude Code integration | Plugin: SessionStart hook, Stop hook, `/sp` commands, bundled skill | One install command; hooks inject boot context automatically | CLAUDE.md snippet only (no automatic pull, no commands) |
| chat and Cowork integration | The same skill uploaded as a .skill zip; GitHub or Notion connector for I/O | Skills and connectors are the supported extension points in claude.ai | Browser extension (fragile, off-platform) |
| Claude Design integration | Product repo linked in Claude Design for tokens; Design handoffs logged from Code | Uses what Claude Design documents today (A1) | Writing from inside Claude Design (no evidence it runs skills or connectors) |
| Index job | GitHub Action in the store template running `sp index` | Writes from chat need a rebuild nobody runs by hand | Rebuild from the skill in chat (many connector calls, slow, error-prone) |
| Validation | `sp check` with the spec in `schema/` | One command, same rules everywhere | JSON Schema plus a third-party validator (adds a dependency) |

## Hosting and regions
None. samepage runs nothing on a server. The public repo is hosted on GitHub. Each user's store is a private GitHub repo (GitHub region, user's plan) or a Notion page (Notion's region). The store Action runs on GitHub-hosted runners in the user's own account.

## Environments
| Env | Purpose | Data | Deploys from |
|---|---|---|---|
| local | Development of `sp`, skill and plugin | `fixtures/small` (20 projects) | Working tree |
| preview | Per-PR CI in the public repo | `fixtures/small` and `fixtures/perf` | Pull request |
| staging | Demo store repo `samepage-demo` that every surface reads during release testing | Production-sized synthetic (test-data.md) | main, on release tag candidate |
| production | Users' own stores | Real, private, never seen by the maintainer | Tagged release of the plugin, skill zip and store template |

## Background jobs
| Job | Schedule or trigger | Max duration | On failure |
|---|---|---|---|
| Store index rebuild (`sp index` in the store Action) | push to the store's default branch that touches anything outside `index/` | 3 min (target 90 s) | Job fails, GitHub emails the owner, previous index stays, `index/builds.md` records the error; boot shows "index stale" |
| Store check in the store Action | same push, before rebuild | 1 min | Job fails with the failing path and field; index is not rebuilt from an invalid store |
| Public repo CI | every PR and push to main | 10 min | Merge blocked |
| Release packaging | tag `v*` | 10 min | Release not published |

The rebuild Action ignores its own `index/` commits so it never loops. Agent call (B8): the store template ships without branch protection; the README says any protection must allow the Action to push, or the index will not rebuild.

Agent call (B10): `sp` is not installed on PATH. The plugin bundles `sp/`; hooks and `/sp` commands call `python3 -m sp` from the plugin root, and setup is `/sp init` inside Claude Code.

## External services
| Service | Used for | Timeout | Retry | Degraded behaviour |
|---|---|---|---|---|
| GitHub (git over HTTPS) | Pull and push the store from Code | 3 s for the boot pull; 30 s for push | 1 retry on push | Boot uses cached files; push failure keeps the commit locally and says so |
| GitHub connector in claude.ai | Read and write store files from chat and Cowork | connector default | 1 retry on sha mismatch only | Read fails: answer without context, say so in one line. Write fails: show the entry as a block with its path |
| Notion connector | Read and write a Notion store from any surface | connector default | 1 retry | Same as GitHub connector |
| GitHub Actions | Index rebuild | 3 min | GitHub's rerun | Stale index flagged at boot |

Never block a session start on a third party: the hook's whole budget is 3 s.

## AI usage
| Task | Model tier | Input cap | Cached by | Cost per call |
|---|---|---|---|---|
| Draft a ship event, decision or handoff from the session | The model already running the session | The current conversation plus `git log -20 --oneline` | Not cached; one draft per log | 0 USD extra; part of the user's own session |

samepage makes no API calls of its own and ships no API key handling. AI drafting happens only in log modes, at write time. Boot and recall never summarise; they print pre-built serve files.

## Secrets
None are created, read or stored by samepage. Git credentials stay in the user's git or gh setup; connector auth stays in claude.ai. `sp check` and GitHub push protection reject secret-looking content in the store. Agent instruction files in the repo never contain tokens.

## Dependencies
Approved list:
- Runtime: Python 3.9+ standard library, git, POSIX sh (hook), GitHub CLI `gh` (only for `sp init --backend github`).
- Store Action: `actions/checkout` pinned by commit sha, `actions/setup-python` pinned by commit sha.
- Distribution: Claude Code plugin marketplace manifest, GitHub Releases.
Anything not listed needs an ADR before it is added.

## Public repo layout
Agent call (B21): the repo root is the Claude Code plugin, so the installed plugin carries `sp/` and its hooks can run it with `python3 -m sp` from `${CLAUDE_PLUGIN_ROOT}`. A separate `plugin/` folder could not reach `sp/` without copying it at release.

```
README.md                     pitch, 60-second demo, install
SPEC.md               the store spec (entities, files, rules), versioned
schema/                       lookups.json, fields.json (the logical contract as data)
sp/                          Python package: init, boot, log, index, check, proof, export, migrate
.claude-plugin/               plugin.json, marketplace.json (the repo root is the plugin, B21)
hooks/                        hooks.json, session-start.sh, stop-nudge.sh
commands/                     sp.md (init, boot, check, log, handoff, proof)
skills/samepage/            SKILL.md, references/ (github-backend.md, notion-backend.md, setup.md, entry-schema.md, design.md)
store-template/               files for a new GitHub store, including .github/workflows/index.yml
notion-template/              setup instructions and property definitions for the eight databases
fixtures/                     small/ (hand-written), perf/ (generated)
docs/architecture/            this pack
dist/                         samepage.skill (built in release)
```
