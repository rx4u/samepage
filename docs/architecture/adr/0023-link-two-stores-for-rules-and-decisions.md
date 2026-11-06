# ADR-0023: Link two stores and share rules and decisions both ways

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
One person often has two stores: one for an office account and one for a personal account (two GitHub logins, two Claude accounts). Today the stores never meet, so a rule added at work ("never use em dashes") has to be typed again at home, and a decision made in one is invisible in the other.

The owner chose (2026-11-06): rules and decisions cross, nothing else; both directions.

What may cross is the user's call, not samepage's. samepage does not ask about employers or policies. It makes the boundary explicit (what crosses, shown before it is written) and moves only the two record types the user opted into.

This is not the cut "two-way sync between a GitHub store and a Notion store" (scope.md): both stores here are GitHub stores with the same file layout, and only two tables are copied, by id.

## Options

### Option A: `sp link` plus `sp sync`, file copy by id between two local clones
- Pros: no server, no tokens (ADR-0001, ADR-0006); both stores are already cloned on the machine; ids are uuids, so files never collide; idempotent.
- Cons: runs only on a machine that has both clones.
- Price: 0 USD.

### Option B: A third shared store both accounts read
- Pros: one source.
- Cons: both accounts need access to one repo, which is the very thing the user may not want; boot reads two stores; more setup.
- Price: 0 USD.

### Option C: Export and import files by hand
- Pros: nothing to build.
- Cons: nobody does it twice.
- Price: 0 USD.

## Decision
Option A.

- `sp link add PATH --name NAME` records a second local store clone in `~/.samepage/config` (new key `links`, `name=path` pairs, max 3). `sp link list`, `sp link remove NAME`.
- `sp sync [NAME] [--dry-run]` compares both stores and copies in both directions:
  - rules: `rules/{id8}.md`, all of them, active or paused;
  - decisions: `decisions/{slug}/...` only for project slugs present in both stores, plus `general`. Decisions of a project the other store does not have stay where they are, and the dry run lists them as skipped.
- Same id in both stores: the file with the later `updated_at` wins; equal means no change. A rule paused on one side is paused on the other.
- Files are copied byte for byte. No new key is added, so the schema stays 1.1 and the sha-pinned store Action on either side passes unchanged. A record carrying a key newer than the other store's `schema_version` (B23) is skipped with the reason, never rewritten.
- Every sync prints the plan first (copy, update, skip, per direction) and writes only after a yes (`--yes` skips the prompt; with no terminal and no `--yes` nothing is written). Each store then goes through the shared write path: pull, check, index, one commit, push when a remote exists.
- Nothing else crosses: projects, ships, proof, handoffs, design assets, store.md and config stay in their store.
- MCP and the skill get no sync tool in this ADR. Sync is a CLI step the user runs.

## Non-goals
Notion stores, more than one linked pair per run, sharing projects or handoffs, scheduled or background sync, team stores.

## Consequences
- Gets easier: one rule set and one decision log across both accounts.
- Gets harder: `rules/` and `decisions/` can change from outside a session.
- Follow-up tasks: none. Showing where a record came from would need a new key and schema 1.2; revisit if users ask.

## Implementation plan
- Affected paths: sp/config.py (`link.NAME` keys, kept when `sp init` rewrites the config), new sp/sync.py, sp/__main__.py, docs/architecture/scope.md, README.md, tests/test_sync.py.
- Pattern to follow: `sp.index.load` for the store rows (no new folder walk, guardrails.md), `sp.write.apply` for each store's write.
- Pattern to avoid: any network call beyond the user's own git remote, reading a store through GitHub instead of the local clone, copying by path instead of by id.

## Verification
- [x] Sync twice in a row: the second run plans nothing
- [x] A rule added in A and a rule paused in B both land on the other side after one run
- [x] A decision in a project only A has is reported as skipped, not copied
- [x] `--dry-run` writes nothing
- [x] `python3 -m unittest discover -s tests` and `python3 scripts/guardrails.py` pass

## More information
- 2026-11-06: accepted by the owner ("build them and push"). The `origin` key in the first draft was dropped: it needed schema 1.2, and every linked store's pinned Action would reject it until upgraded.

## Revisit when
A user asks for handoffs to cross, or for a Notion store to be linked.
