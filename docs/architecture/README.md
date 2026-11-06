# Architecture: samepage

Mode: new
Status: approved (PRD and scope accepted by Raja, 2026-11-06; gate passed)
Last validated: 2026-11-06

Name: samepage, CLI `sp`, published under github.com/rx4u (ADR-0010, ADR-0013). Earlier drafts used the working name context-os.

## What this is
An open-source kit that gives every Claude surface (Claude Code, claude.ai chat, Cowork, Claude Design) one shared working context: who you are, how you want Claude to behave, every project you have, what you shipped, what you decided, and what is waiting to be picked up on another surface. The context lives in a store the user owns: a private GitHub repo of Markdown files, or a set of Notion databases. One skill reads and writes it from every surface. A Claude Code plugin boots it into every session.

There is no hosted service, no database server and no API key. The SQL in data-architecture.md is the logical contract every adapter must honour (ADR-0003), not a deployed database.

## Documents
| Document | What it decides |
|---|---|
| [prd.md](prd.md) | Problem, users, stories, success metrics |
| [scope.md](scope.md) | v1 in, v1 out, later phases |
| [users-and-roles.md](users-and-roles.md) | Personas, account model, permissions |
| [targets.md](targets.md) | Context size, speed, scale, cost, reliability, privacy numbers |
| [data-architecture.md](data-architecture.md) | Layers, entities, DDL, lookups, physical layouts per backend |
| [data-dictionary.md](data-dictionary.md) | Every column, its writer and readers |
| [read-models.md](read-models.md) | One read contract per screen (each surface moment) |
| [system-design.md](system-design.md) | Repo layout, distribution, jobs, external services, AI use |
| [adr/](adr/README.md) | Decisions and their status |
| [test-data.md](test-data.md) | Demo store data and perf checks |
| [monitoring.md](monitoring.md) | What is measured and who is alerted |
| [guardrails.md](guardrails.md) | CI rules that enforce the standards |
| [build-plan.md](build-plan.md) | Work packages, waves, definition of done |
| [assumptions.md](assumptions.md) | Ranked assumptions and constraints |
| [builder-check.md](builder-check.md) | Cold-read questions and their resolutions |

## Vocabulary
- **Store**: the user's own context, in one backend (GitHub or Notion).
- **Surface**: where Claude runs. Lookup `surface`: code, chat, cowork, design.
- **Screen**: a moment on a surface where the store is read or written (session boot, logging a ship, a proof lookup). There is no web UI; screens are skill modes, hook runs and commands.
- **Serve layer**: pre-built index files (GitHub) or database queries (Notion) that answer one screen in one read.

## Binding standards
1. Structured-data rule: filter, sort and count fields are typed frontmatter keys or Notion properties with fixed options, written at log time. No parsing prose or AI summarising at read time.
2. One read model per screen. The serve layer narrows. Cursor paging, never offset. 50 rows per read maximum.
3. Every change meets the targets it touches, with before and after numbers.

## Roles
- Architect: owns these documents, writes work package briefs.
- Builder: implements one brief. Never decides a field, file path, read or dependency.
- Reviewer: checks against targets, read models and the dictionary.

## Changing the architecture
Only by a new ADR. Edit the affected documents in the same change and re-run the validator.
