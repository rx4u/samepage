# GitHub store from chat and Cowork

How chat and Cowork (local and cloud, claude.ai and Claude Desktop) read and write a GitHub store through the GitHub connector. Coding agents use the samepage MCP tools or the `sp` CLI instead (see SKILL.md).

## Find the store

Read the store line from the user's preferences or project instructions:

```
samepage store: github OWNER/REPO
```

Use the repo's default branch. If there is no line, follow setup.md. Never guess a repo name, and never search the user's repos for one.

## Connector operations

The GitHub connector exposes two operations this skill uses. Names vary slightly by connector version; use the one that matches.

- Read: `get_file_contents(owner, repo, path)`. Returns the file text and its `sha`.
- Write: `create_or_update_file(owner, repo, path, content, message, branch, sha)`. Omit `sha` to create a file; pass the current `sha` to update one.

Commit messages: `samepage: <what>`, for example `samepage: log ship halcyon` or `samepage: archive cv-heap`.

## Reads

Every read below is one call. The index files are pre-sorted and capped; do not list folders or read raw entries to answer these.

| Mode | File | Notes |
|---|---|---|
| boot | `index/boot/{surface}.md` | `chat` or `cowork`. Profile, rules for this surface, up to 10 active projects, open handoffs to this surface |
| proof, no tags | `index/proof-1.md` | 20 projects per page, newest ship first; `next: FILE` footer is the next page |
| proof, with tags | `index/tags/{slug}.md` per tag, max 3 | Up to 50 projects each. Keep the projects present in every tag file, in the first file's order, and stop at 20 |
| project detail, design lookup | `index/project/{slug}.md` | Fields, last 10 ship events, decisions in force, design assets, open handoffs |
| handoff inbox | `index/handoffs-{surface}-1.md` | Open and picked-up, newest first |
| handoff start | `handoffs/{id8}.md` | The full brief; read only when the user picks one |
| rules | `index/rules.md` | Active rules grouped by surface |
| log, archive, any project change | `projects/{slug}.md` | The raw project file, for its text and `sha` |

Rules for reads:
- Follow a `next:` footer only when the user asks for more.
- Every serve file starts with `built: TIME from SHA schema X.Y`, where X.Y is the store's schema version. Write `tool` and `from_tool` only when it is 1.1 or later. A write made from chat appears in index files after the store Action rebuilds them, usually within 90 seconds. If the user asks about something they just logged, say it may take a minute to show.
- A 404 on `projects/{slug}.md` means the project does not exist: offer to create it. A 404 on `index/tags/{slug}.md` means no project has that tag.
- Boot failure (any error): say in one line that the store could not be read, then answer without it. Do not retry in a loop.

### Finding an id the index does not show

The project detail and rules index list decisions, design assets and rules without ids. When a write needs one (superseding a decision, superseding a design system, pausing a rule), read the one folder that holds it and pick by date and title:

- decision: list `decisions/{slug}/`. File names are `{yyyy-mm-dd}-{id8}.md`; match the date from the detail file, then read that file.
- design system: list `design/{slug}/` and read files until you find `kind: design_system` with `status: approved` (at most 20 reads).
- rule: ask the user for the id8 if they have it; otherwise list `rules/` and read files until the rule text matches (at most 50 reads, the active rule cap).

## Writes

Build each file from entry-schema.md. Show the path and full text, wait for a yes, then write. Create new files without `sha`; update existing files with the `sha` from your read in this turn.

| Write | Files |
|---|---|
| Log ship | create `events/{yyyy}/{yyyy-mm-dd}-{project}-{id8}.md`; create `tags/{slug}.md` for each new tag; update `projects/{slug}.md` (`updated_at`, `last_verified_at`, B6 status and `shipped_on`, new tags) |
| New project | create `projects/{slug}.md` before its first event |
| Decision | create `decisions/{project}/{yyyy-mm-dd}-{id8}.md`; when superseding, update the old decision file; update `projects/{slug}.md` |
| Design pointer or handoff capture | create `design/{project}/{id8}.md`; for a new approved design system, update the previous approved one to `status: superseded`; update `projects/{slug}.md` |
| Handoff new | create `handoffs/{id8}.md`; update `projects/{slug}.md` |
| Handoff start, done, drop | update `handoffs/{id8}.md`; update `projects/{slug}.md` |
| Archive project | update `projects/{slug}.md` |
| Rule add | create `rules/{id8}.md` |
| Rule pause | update `rules/{id8}.md` |

Order: create the new entry first, then update the files it affects. If a create returns 422 because the path exists, generate a new uuid and create again (B12).

Never write under `index/`. The store Action rebuilds it on every push.

### Example: log a ship from chat

User: "log that I shipped the halcyon pricing page". Read `projects/halcyon.md` (keep its `sha`). Show:

```
events/2026/2026-11-06-halcyon-7fe7baaf.md (new)
---
id: 7fe7baaf-f981-4684-a558-9b8b1bd9dd15
project: halcyon
kind: shipped
surface: chat
tool: claude_ai
summary: Shipped the Halcyon pricing page with monthly and yearly plans
occurred_at: 2026-11-06T10:00:00Z
created_at: 2026-11-06T10:15:00Z
---

projects/halcyon.md (update)
updated_at: 2026-11-06T10:15:00Z
last_verified_at: 2026-11-06T10:15:00Z
```

Ask "Write these two files?" On yes: `create_or_update_file` for the event without `sha`, then for the project with the full updated file text and its `sha`. Report `samepage: wrote events/2026/2026-11-06-halcyon-7fe7baaf.md, updated projects/halcyon.md`.

## Sha conflicts

Two surfaces can edit the same project, decision, handoff or rule file. An update whose `sha` is stale fails with a conflict (409 or 422 mentioning sha).

1. Re-read the file to get its current text and `sha`.
2. Re-apply only your change (the keys you showed the user) to the new text, keeping every other key as it now is. Write once more.
3. If that also fails, or the re-read shows a change to the same keys you are setting, stop. Show the user both versions of the changed keys and ask which to keep.

New entry files never conflict: each entry is its own file.

## Read-only connector

Writes can fail with `403 Resource not accessible by integration` while reads work. This was observed on 2026-11-06: the GitHub app behind the claude.ai connector was not installed on the store owner's account, so the connector could read but not write.

When a write returns 403, or the user says the connector is read-only:
1. Do not retry.
2. Output each file as a code block with its exact path above it, so the user can add it by hand or from Claude Code.
3. Say, in one or two sentences: writes from chat need the claude.ai GitHub connector's app installed on the account that owns the store repo, with access to that repo (GitHub settings, Applications, Installed GitHub Apps). After installing, start a new conversation.

Nothing is lost: the next write from Claude Code or from chat after the install works the same way.
