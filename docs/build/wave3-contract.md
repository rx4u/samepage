# Wave 3 contract (binding for WP-07 to WP-13)

Read with `docs/architecture/` (binding) and `SPEC.md`. This file fixes the interfaces between the four wave 3 work streams so they can be built in parallel. Change it only by a note to the integrator, never silently.

## Ownership (each stream edits only its files)

| Stream | WPs | Owns |
|---|---|---|
| A skill | WP-07, skill modes for 08, 09, 12, 13, sha-conflict edge case of 14 | `skills/samepage/SKILL.md`, `skills/samepage/references/github-backend.md`, `skills/samepage/references/entry-schema.md`, `skills/samepage/references/design.md`, `skills/samepage/references/setup.md`, `tests/test_skill.py` |
| B CLI | WP-08, 09, 12, 13 (CLI side), CLI edge cases of 14 | `sp/write.py`, `sp/log.py`, `sp/handoff.py`, `sp/proof.py`, `sp/brief.py`, `sp/rules.py`, new subcommands in `sp/__main__.py`, `hooks/stop-nudge.sh`, the Stop entry in `hooks/hooks.json`, `commands/sp.md`, `tests/test_write.py` |
| C store template | WP-11 | `store-template/` (including `store-template/.github/workflows/index.yml`), the template-copy step in `sp/init.py` `scaffold()`, `tests/test_template.py` |
| D Notion | WP-10 | `skills/samepage/references/notion-backend.md`, `notion-template/`, `sp/export.py`, the `export` subcommand in `sp/__main__.py`, `tests/test_export.py` |

`sp/__main__.py` is shared by B and D: add your subparsers and dispatch branches as separate, self-contained blocks so a merge is trivial.

## CLI interface (stream B builds it, stream A's skill calls it in Claude Code)

Every write command:
- Reads the store from `~/.samepage/config` (`SAMEPAGE_HOME` overrides), or `--store PATH`.
- Takes all values as flags. Never prompts. Claude drafts and confirms with the user before calling (ADR-0007).
- `--dry-run` prints the exact file path(s) and full file text it would write, then exits 0 without writing. The skill and `/sp` show this to the user as the confirmation step.
- Without `--dry-run`: `git pull --rebase -q` first if the store has a remote (B9; on conflict stop, print the path, write nothing), write the file(s), run `sp check` on the store (on errors: undo the write, print errors, exit 1), run `sp index`, `git add -A && git commit -m "samepage: <summary>"`, then `git push -q` if a remote exists (push failure keeps the commit and says so).
- Prints one line on success: `samepage: wrote <path>[, updated <path>]`.
- `--surface` defaults to `code`.

Commands:

```
sp log ship   --project SLUG --kind shipped|deployed|launched|milestone|metric|published --summary TEXT
              [--proof-url URL] [--metric-label L --metric-value N --metric-unit U] [--occurred-at ISO]
              [--new-project-name NAME --new-project-type TYPE --new-project-one-liner TEXT]   # creates the project first (US-05)
              [--tag SLUG]...                                                                   # adds tags to the project, creating tag files
sp log decision --project SLUG --title TEXT --reason TEXT [--body TEXT] [--supersedes ID]
sp log design   --project SLUG --kind design_system|screen_set|handoff_bundle|prototype --title TEXT
              [--status draft|approved] [--source-url URL] [--tokens-repo-url URL] [--tokens-path PATH]
sp handoff new  --project SLUG --to code|chat|cowork --title TEXT --body TEXT [--from SURFACE]
sp handoff start ID8 | done ID8 | drop ID8
sp handoff list [--surface S]                      # reads index/handoffs-{surface}-1.md, prints it
sp handoff show ID8                                # prints handoffs/{id8}.md body
sp proof [--tag SLUG]... [--page N]                # reads index/proof-{n}.md or tag files (AND, max 3 tags), max 50 rows
sp project SLUG [--archive]                        # prints index/project/{slug}.md; --archive sets status archived (asks nothing)
sp rules add --rule TEXT [--surface S] | pause ID8
sp brief SLUG                                      # design brief for pasting into Claude Design (WP-13)
```

Behaviour that must match the read models (docs/architecture/read-models.md):
- Ship event of kind shipped or launched sets project status to shipped when it is idea, active or unknown, and sets `shipped_on` if empty; never changes parked or archived (B6).
- Every write to a project or its children updates `project.updated_at` and `project.last_verified_at`.
- `--supersedes ID`: old decision gets status `superseded`, `superseded_by` = new id, `updated_at`.
- A new approved design_system supersedes the previous approved design_system of the same project.
- `handoff start` sets `picked_up`, `picked_up_at`; `done`/`drop` set `done`/`dropped`, `done_at`. `--to design` is rejected (B7).
- Deleting is never offered. `--archive` is the only retirement.
- New uuid: regenerate if the target path exists (B12). File paths and keys exactly as `schema/fields.json` (B18; body columns in the Markdown body).
- `sp brief SLUG` prints: profile voice, project name and one-liner, accepted decisions (from `index/project/{slug}.md`), and the approved design_system pointer as "Use the design tokens in TOKENS_PATH on the default branch of TOKENS_REPO" (A1 showed the file and branch must be named).

## Chat and Cowork (stream A, GitHub backend through the GitHub connector)

- Boot: one `get_file_contents` of `index/boot/{chat|cowork}.md` from the store repo named in the user's setup (US-04). On failure, one line saying the store could not be read, then answer without it.
- Write: build the exact file text with the same keys as the CLI (entry-schema.md documents every entity with an example). Show it with its path, wait for a yes, then `create_or_update_file`. Project updates need the file's current sha: on sha mismatch re-read, re-apply once, then ask the user (consistency table).
- Read-only connector (A2: writes return 403 until the claude.ai GitHub connector's app is installed on the store owner's account): output the entry as a code block with its exact path and say writes need that install (US-06).
- The store Action (stream C) rebuilds the index after a chat write; chat never edits `index/`.

## Notion (stream D)

- Eight databases under one private page "samepage", properties per data-architecture.md "Physical layout: Notion store", select options exactly the lookup codes, plus the serve-only rollup "Last shipped" on Projects (B5).
- notion-backend.md gives, for every read model, the exact query (filters, sorts, page_size 20, max 50) and for every write the exact properties. Boot is the 4 Chat recall queries.
- `sp export --from-notion-csv DIR --out STORE`: converts a Notion "Markdown & CSV" export of the eight databases into a GitHub store layout that passes `sp check`. No Notion API, no tokens (ADR-0006).

## Store Action (stream C)

`store-template/.github/workflows/index.yml`: on push to the default branch, skipping commits that only touch `index/` and commits by the Action itself; checkout the store; checkout `rx4u/samepage` (path `.samepage-tool`, pinned by commit sha (ADR-0016)); `python -m sp check .` then `python -m sp index .`; commit and push only `index/` with message `index: rebuild {sha8}`; `timeout-minutes: 3`; `permissions: contents: write`; actions pinned by commit sha (actions/checkout 3d3c42e5aac5ba805825da76410c181273ba90b1 = v7.0.1, actions/setup-python 6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 = v7.1.0). `sp init` copies the template into new stores.

## Every stream

- Python standard library only. No em dashes anywhere. `python3 scripts/guardrails.py` and `python3 -m unittest discover -s tests` must pass in your worktree.
- Commit on your branch with messages ending in the attribution lines given in the brief. Do not push, do not merge.
