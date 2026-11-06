# ADR-0023: Link two stores and share rules and decisions both ways

Status: proposed
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
- Copied files get one new optional key, `origin` (the link name of the store the record was first written in), so boot and the Rules list can show "from personal". `origin` is never changed after the first copy.
- Every sync prints the plan first (copy, update, skip, per store) and writes only after confirmation, then commits to each store with one commit and rebuilds `index/` there. It never pushes; the user's normal push does.
- Nothing else crosses: projects, ships, proof, handoffs, design assets, store.md and config stay in their store.
- MCP and the skill get no sync tool in this ADR. Sync is a CLI step the user runs.

## Non-goals
Notion stores, more than one linked pair per run, sharing projects or handoffs, scheduled or background sync, team stores.

## Consequences
- Gets easier: one rule set and one decision log across both accounts.
- Gets harder: `rules/` and `decisions/` can change from outside a session; the store check must accept `origin`.
- Follow-up tasks: data-dictionary rows for `preference.origin` and `decision.origin`; Store check accepts the key; Rules read model shows the origin; a work package brief.

## Implementation plan
- Affected paths: sp/config.py (links key), new sp/link.py and sp/sync.py, sp/__main__.py, sp/check.py, sp/index.py (rules origin), docs/architecture/data-dictionary.md, docs/architecture/scope.md, tests/test_sync.py.
- Pattern to follow: the write context and confirm-then-write flow in sp/write.py; one commit per store.
- Pattern to avoid: any network call, reading a store through GitHub instead of the local clone, copying by path instead of by id.

## Verification
- [ ] Sync twice in a row: the second run plans nothing
- [ ] A rule added in A and a rule paused in B both land on the other side after one run
- [ ] A decision in a project only A has is reported as skipped, not copied
- [ ] `--dry-run` writes nothing
- [ ] `python3 -m unittest discover -s tests` and `python3 scripts/guardrails.py` pass

## Revisit when
A user asks for handoffs to cross, or for a Notion store to be linked.
