# samepage store spec

Version 1.1. The binding source is [docs/architecture/data-architecture.md](docs/architecture/data-architecture.md); this page is the readable summary. `schema/fields.json` and `schema/lookups.json` are generated from it with `python3 -m sp schema` and are what `sp check` and the skill use.

## What a store is

A store is your shared working context. It lives in one backend:

- **GitHub:** a private repo of Markdown files, one row per file.
- **Notion:** eight databases under one private page called "samepage".

The rest of this page describes the GitHub layout. The Notion layout maps the same fields to database properties.

## File format

```
---
id: 0e49799a-3292-5f06-9717-98e29764f69c
project: halcyon
status: open
tags: [nextjs, ai]
---

Markdown body. Display only, never parsed.
```

- Frontmatter is flat: one `key: value` per line. Values are text, numbers, `true`/`false`, ISO dates (`2026-11-06`), ISO date-times with a time zone (`2026-11-06T09:30:00Z`), or one inline list (`tags`).
- No nesting and no multi-line values. Quote a value that contains `: ` or starts with a symbol, using double quotes.
- An optional key can be absent or empty. Both mean "no value".
- The body is for humans. The exceptions are `decision.body` and `handoff.body`, which are stored as the body.

## Folders

| What | Path |
|---|---|
| Store settings | `store.md` |
| Profile | `profile.md` |
| Profile links | `profile/links/{id8}.md` |
| Rules | `rules/{id8}.md` |
| Tags | `tags/{slug}.md` |
| Projects | `projects/{slug}.md` |
| Ship events | `events/{yyyy}/{yyyy-mm-dd}-{project}-{id8}.md` |
| Decisions | `decisions/{project}/{yyyy-mm-dd}-{id8}.md` |
| Design assets | `design/{project}/{id8}.md` |
| Handoffs | `handoffs/{id8}.md` |
| Generated serve files | `index/` (never edit by hand) |

`{id8}` is the first 8 characters of the row's uuid. `{slug}` is lowercase kebab case and never changes.

## Key naming

- A lookup is written by its code: `status: shipped`, `to_surface: code`.
- A project reference is written as the project slug: `project: halcyon`.
- `superseded_by` holds the uuid of the replacing decision.
- A project's tags are the inline list `tags: [nextjs, ai]`. Each tag needs a file in `tags/`.

## Allowed values

| Field | Values |
|---|---|
| surface | code, chat, cowork, design. A surface is a role: `code` is any coding agent, `chat` any chat assistant |
| tool (1.1) | claude_code, claude_ai, claude_desktop, cowork, claude_design, codex, cursor, copilot, gemini_cli, windsurf, other |
| project status | idea, active, shipped, parked, archived, unknown |
| project type | product, client_site, concept, skill, tool, content, other |
| event kind | shipped, deployed, launched, milestone, metric, published |
| design asset kind | design_system, screen_set, handoff_bundle, prototype |
| design asset status | draft, approved, superseded |
| decision status | accepted, superseded, reversed |
| handoff status | open, picked_up, done, dropped |

## Version 1.1: the tool keys

Version 1.1 adds one optional key that records which tool wrote an entry: `tool` on ship events, decisions and design assets, and `from_tool` on handoffs. Handoffs still go to a surface, so a handoff to `code` is picked up by whichever coding tool opens next.

```
---
id: 7fe7baaf-2b1c-4f0e-9a51-3c1f1d1e2a10
project: halcyon
kind: shipped
surface: code
tool: cursor
summary: Shipped the pricing page
occurred_at: 2026-11-06T09:30:00Z
created_at: 2026-11-06T09:31:00Z
---
```

- A 1.0 store stays valid. It must not carry `tool` or `from_tool`; `sp check` fails it if it does, and every writer leaves them out.
- New stores start at 1.1.

### Upgrade a store from 1.0 to 1.1

In one commit on the store's default branch:

1. In `store.md`, set `schema_version: 1.1`.
2. In `.github/workflows/index.yml`, set the samepage tool `ref:` to a commit of rx4u/samepage that has schema 1.1 or later (the template repo's workflow shows the current one).

## Rules every store follows

- The reserved project `general` exists. It holds handoffs and decisions that belong to no single project.
- Nothing is deleted. Projects are archived; decisions are superseded or reversed.
- No secrets. `sp check` fails on API keys, tokens, private keys and card-like numbers anywhere in the store.
- Handoffs cannot go to `design` in v1.
- At most 50 active rules in total. More than 20 for one surface is a warning.
- Each boot file in `index/boot/` stays under 8,000 characters; each `index/project/` file under 6,000.

## Check a store

```
python3 -m sp check path/to/store
python3 -m sp check path/to/store --only projects
```

Exit code 0 means valid. Each error names the file, the field and the problem.
