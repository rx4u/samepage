# ADR-0003: Adopt a logical schema with file and Notion adapters

Status: accepted
Date: 2026-11-06
Deciders: Claude (architect), agent call

## Context
There is no database server, but two backends and four surfaces must agree on every field. Without one contract, each surface would invent its own shape and the store would drift.

## Options

### Option A: Logical SQL DDL as the contract, mapped to files and Notion properties, validated by `sp check`
- Pros: one precise source of truth; types, lengths and relationships are explicit; the data dictionary and read models can reference real columns.
- Cons: contributors must understand that the SQL is never run.
- Price: 0 USD.

### Option B: Prose spec only
- Pros: easy to read.
- Cons: ambiguous; two builders will disagree on types and required fields.
- Price: 0 USD.

## Decision
Option A. `data-architecture.md` holds the DDL. `schema/fields.json` and `schema/lookups.json` are generated from it in WP-02 and are what `sp check` and the skill use. GitHub frontmatter is a flat YAML subset: `key: value` scalars, ISO dates, and inline lists `[a, b]`; no nesting, no multi-line values. The Markdown body is display-only.

Agent call: flat frontmatter so `sp` can parse it with the standard library and so chat can write it by hand without errors.

## Non-goals
Not a migration framework for SQL databases.

## Consequences
- Gets easier: validation, adapters, docs.
- Gets harder: any new field needs a spec change.
- Follow-up tasks: WP-02.

## Implementation plan
- Affected paths: schema/, sp/model.py, SPEC.md
- Pattern to follow: one writer function per table that emits the exact frontmatter keys in dictionary order.
- Pattern to avoid: reading fields from the Markdown body.
- Config and env changes: none.

## Verification
- [ ] `sp check` rejects a file with a nested frontmatter value
- [ ] Every dictionary column appears in schema/fields.json (CI diff)

## Revisit when
A field needs nested structure that cannot be expressed as another table.

## More information
