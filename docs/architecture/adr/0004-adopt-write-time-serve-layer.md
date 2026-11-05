# ADR-0004: Adopt a write-time serve layer

Status: accepted
Date: 2026-11-06
Deciders: Claude (architect), agent call

## Context
A boot from chat can only read files through the GitHub connector, one call at a time. Reading and filtering every project file at boot would take dozens of calls and thousands of tokens.

## Options

### Option A: Generate serve files under `index/` at write time (`sp index` locally and in a store Action)
- Pros: boot is one file; sorting, filtering and caps happen once per write; the reader does no parsing.
- Cons: chat writes are eventually consistent (90 s target); an Action must exist in the user's repo.
- Price: about 20 to 30 s of Action time per push, inside GitHub's free 2,000 minutes for private repos.

### Option B: Read the raw folders at boot and filter in the reader
- Pros: no job; always current.
- Cons: breaks the boot budget (1 read, 2,000 tokens); filtering in prose is unreliable.
- Price: tokens on every session.

## Decision
Option A. Serve files are listed in data-architecture.md and owned by `sp index`. They are generated, committed by the Action with the message `index: rebuild {sha8}`, and never hand-edited.

## Non-goals
Notion stores, which use live queries instead.

## Consequences
- Gets easier: fast, cheap boot on every surface.
- Gets harder: debugging a stale index (mitigated by headers and `index/builds.md`).
- Follow-up tasks: WP-03, WP-11.

## Implementation plan
- Affected paths: sp/index.py, store-template/.github/workflows/index.yml
- Pattern to follow: one generator function per serve file, each fed by one sorted pass.
- Pattern to avoid: a reader that globs raw folders.
- Config and env changes: the workflow needs `contents: write` permission.

## Verification
- [ ] `sp index` on the perf fixture finishes under 5 s
- [ ] A chat write to the demo store appears in `index/boot/chat.md` within 90 s

## Revisit when
GitHub Action limits change or chat gains a way to run code against the store.

## More information
