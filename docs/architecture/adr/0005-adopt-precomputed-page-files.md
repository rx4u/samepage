# ADR-0005: Adopt precomputed page files and cursor paging

Status: accepted
Date: 2026-11-06
Deciders: Claude (architect), agent call

## Context
Lists (projects, proof, handoffs) grow without bound. Readers in chat cannot run queries, so paging has to be built into the files.

## Options

### Option A: Pages of 20 rows, sorted by key DESC then id DESC, `next:` footer as the cursor; Notion uses `start_cursor`
- Pros: keyset semantics; one read per page; stable order; no row-count skipping.
- Cons: more files in `index/`.
- Price: 0 USD.

### Option B: One file per list with every row
- Pros: one file.
- Cons: unbounded size; a 5,000-event store produces a file far over the token budget.
- Price: tokens on every read.

## Decision
Option A. Default 20 rows, hard maximum 50 per read. Tag indexes hold up to 50 rows on one page so tag intersection needs one read per tag.

## Non-goals
Search. Out of v1 scope.

## Consequences
- Gets easier: predictable token cost per read.
- Gets harder: the reader must follow `next:` for older rows.
- Follow-up tasks: WP-03.

## Implementation plan
- Affected paths: sp/index.py, skill references
- Pattern to follow: `write_pages(name, rows, key, size=20)`.
- Pattern to avoid: limit and skip by count.
- Config and env changes: none.

## Verification
- [ ] Perf fixture produces 15 proof pages of at most 20 rows with valid `next:` chains
- [ ] `sp proof --limit 51` exits with an error

## Revisit when
Stores routinely exceed 2,000 projects.

## More information
