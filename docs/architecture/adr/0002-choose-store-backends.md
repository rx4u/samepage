# ADR-0002: Choose store backends

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
The store must be readable and writable from Claude Code (local tools, git) and from claude.ai chat and Cowork (connectors only). The owner asked for GitHub and Notion.

## Options

### Option A: GitHub repo and Notion, one backend per store, same logical schema
- Pros: both have first-party claude.ai connectors with write tools; GitHub suits developers and works offline from Code; Notion suits people who already run their work in Notion.
- Cons: two adapters to maintain; Notion has no index job, so its boot costs 4 queries instead of 1 file.
- Price: 0 USD (GitHub free private repos, Notion free plan for one person).

### Option B: GitHub only
- Pros: one adapter; one boot read; simplest docs.
- Cons: excludes Notion-first users, including the owner's own workflow.
- Price: 0 USD.

### Option C: Google Drive documents (as claude-shared-memory does)
- Pros: Drive connector is common.
- Cons: Docs are not structured rows; filtering and sorting would need parsing at read time, which breaks the structured-data rule.
- Price: 0 USD.

## Decision
Option A. A store uses exactly one backend, recorded in `store_meta.backend_id`. No sync between backends in v1; `sp export --from notion` converts a Notion store to the GitHub layout for users who switch.

## Non-goals
Two-way sync between backends (scope.md, cut).

## Consequences
- Gets easier: reaching both developer and Notion audiences.
- Gets harder: every read and write mode needs two documented paths.
- Follow-up tasks: WP-10 Notion adapter.

## Implementation plan
- Affected paths: skills/samepage/references/github-backend.md, notion-backend.md; notion-template/
- Pattern to follow: the skill's mode text is backend-neutral; backend specifics live only in the two reference files.
- Pattern to avoid: backend checks scattered through SKILL.md.
- Config and env changes: `~/.samepage/config` holds `backend` and either `store_path` or `notion_page_id`.

## Verification
- [ ] Every read model in read-models.md has a GitHub and a Notion query line
- [ ] The release test plays US-04 and US-06 against both demo stores

## Revisit when
A third backend is requested by 20 or more users with a connector that has write tools.

## More information
