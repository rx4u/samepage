# ADR-0015: Allow non-store folder readers

Status: accepted
Date: 2026-11-06
Deciders: Claude (architect), agent call

## Context
The guardrail "only sp check and sp index walk raw store folders" protects the boot and recall budgets. Three modules read folders that are not a store: `sp/schema.py` reads the architecture docs, `sp/fixtures.py` writes generated stores, and `sp/export.py` reads a Notion CSV export. The first guardrail script exempted two of them silently and did not catch `os.scandir`, so the rule was weaker than written.

## Options

### Option A: Name the non-store readers in the allow list and catch every directory API
- Pros: the rule is explicit and complete; a new folder reader fails CI until someone decides.
- Cons: three more allow-list entries.
- Price: 0 USD.

### Option B: Keep silent exemptions
- Pros: no change.
- Cons: the written rule and the enforced rule differ; scandir slips through.
- Price: 0 USD.

## Decision
Option A. The guardrail script catches os.walk, os.listdir, os.scandir, glob, iterdir and rglob in `sp/`, and allows only sp/check.py and sp/index.py (store readers) plus sp/schema.py, sp/fixtures.py and sp/export.py (non-store readers).

## Non-goals
Read limits inside the allowed modules.

## Consequences
- Gets easier: reviewing a new module; the rule says exactly who may read folders.
- Gets harder: nothing material.
- Follow-up tasks: none.

## Implementation plan
- Affected paths: scripts/guardrails.py, docs/architecture/guardrails.md
- Pattern to follow: a module that must read a non-store folder is added here by a new ADR.
- Pattern to avoid: exemptions inside the script that the docs do not list.
- Config and env changes: none.

## Verification
- [x] A file in sp/ using os.scandir outside the allow list fails `python3 scripts/guardrails.py`
- [x] The allow list in guardrails.md matches the script

## Revisit when
A new module needs to read folders.

## More information
- 2026-11-06: found by the Notion stream (WP-10) while writing sp/export.py.
