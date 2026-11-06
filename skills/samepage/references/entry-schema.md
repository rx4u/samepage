# Entry schema

Every store file the skill may write, with its exact path, keys, allowed values and one complete example. The binding source is `schema/fields.json` in the samepage repo; this page matches it. Every example below passes `sp check` when written into the demo store.

## File format

```
---
key: value
---

Markdown body
```

- Frontmatter is flat: one `key: value` per line. No nesting, no multi-line values.
- Values: text, numbers, `true` or `false`, ISO dates (`2026-11-06`), ISO date-times with a zone (`2026-11-06T10:15:00Z`), or one inline list (`tags: [nextjs, ai]`).
- Wrap a value in double quotes when it contains `: ` or starts with a symbol: `reason: "Speed: it ships today"`.
- An optional key may be absent or empty (`picked_up_at:`). Both mean no value.
- The body is for humans and never parsed, except `decision.body` and `handoff.body`, which are stored as the body.

## Key naming (B18)

- `id` is a full lowercase uuid (`8-4-4-4-12` hex). `{id8}` in a path is its first 8 characters.
- A lookup is written by its code without `_id`: `status: shipped`, `to_surface: code`, `kind: launched`.
- A project reference is the project slug: `project: halcyon`.
- `superseded_by` holds the full uuid of the replacing decision.
- A project's tags are `tags: [slug, slug]`; each slug needs a file `tags/{slug}.md`.
- Slugs are lowercase kebab case (`^[a-z0-9]+(-[a-z0-9]+)*$`) and never change.
- If a new file's path already exists, generate a new uuid (B12).

## Allowed values

| Key | Values |
|---|---|
| surface, from_surface, to_surface | code, chat, cowork, design (`to_surface` never `design`) |
| project status | idea, active, shipped, parked, archived, unknown |
| project type | product, client_site, concept, skill, tool, content, other |
| ship event kind | shipped, deployed, launched, milestone, metric, published |
| design asset kind | design_system, screen_set, handoff_bundle, prototype |
| design asset status | draft, approved, superseded |
| decision status | accepted, superseded, reversed |
| handoff status | open, picked_up, done, dropped |

## Entities

R means required. Lengths are maximum characters.

### Store settings

Path `store.md`. Written by setup only. Keys: `schema_version` R, `backend` R (github, notion), `owner_handle` R, `created_at` R, `updated_at` R.

Example, `store.md`:

```md
---
schema_version: 1.0
backend: github
owner_handle: asha-rao
created_at: 2026-11-01T09:00:00Z
updated_at: 2026-11-01T09:00:00Z
---
```

### Profile

Path `profile.md`. Written by setup. Keys: `display_name` R, `headline` R, `location`, `bio`, `voice`, `created_at` R, `updated_at` R.

Example, `profile.md`:

```md
---
display_name: Asha Rao
headline: Product engineer who designs and ships
location: Pune, India
bio: Builds small products end to end.
voice: Direct, lowercase, no fluff
created_at: 2026-11-01T09:00:00Z
updated_at: 2026-11-06T10:15:00Z
---

Longer bio for humans. Never parsed.
```

### Profile link

Path `profile/links/{id8}.md`. Keys: `id` R, `label` R, `url` R, `sort_order` R (whole number, lowest first), `created_at` R.

Example, `profile/links/1b256bcb.md`:

```md
---
id: 1b256bcb-fb23-4ceb-ba7f-87aa971ae5db
label: Dribbble
url: https://shots.example.com/asha-rao
sort_order: 3
created_at: 2026-11-06T10:15:00Z
---
```

### Rule

Path `rules/{id8}.md`. Keys: `id` R, `rule` R (200), `surface` (empty means every surface), `is_active` (`true` or `false`, absent means true), `created_at` R, `updated_at` R. Pausing sets `is_active: false` and `updated_at`. At most 50 active rules.

Example, `rules/cf3f879e.md`:

```md
---
id: cf3f879e-2677-4b0e-a92f-ecd1b9bd3d7b
rule: Cite a proof link for every project named in a proposal.
surface: chat
is_active: true
created_at: 2026-11-06T10:15:00Z
updated_at: 2026-11-06T10:15:00Z
---
```

### Tag

Path `tags/{slug}.md`. Created by the writer the first time a project uses the tag. Keys: `id` R, `slug` R, `label` R (display form, such as `Next.js`), `created_at` R.

Example, `tags/stripe.md`:

```md
---
id: 88fb5b55-8c38-44f1-860e-7300495c7ec6
slug: stripe
label: Stripe
created_at: 2026-11-06T10:15:00Z
---
```

### Project

Path `projects/{slug}.md`. Keys: `id` R, `slug` R, `name` R, `status` R, `type` R, `one_liner` R (140), `problem`, `role`, `outcome`, `live_url`, `repo_url`, `started_on` (date), `shipped_on` (date), `last_verified_at` R, `archived_at`, `created_at` R, `updated_at` R, `tags`.

- A new project starts with `status: active` unless the user says otherwise.
- The reserved project `general` holds decisions and handoffs that belong to no single project. Never archive or rename it.
- Archive sets `status: archived`, `archived_at`, `updated_at` and `last_verified_at`.
- Any write to the project or its children sets `updated_at` and `last_verified_at` to now.

Example, `projects/halcyon-billing.md`:

```md
---
id: 7a4e6426-84bf-42ce-9a62-4bf7dca582ec
slug: halcyon-billing
name: Halcyon Billing
status: shipped
type: product
one_liner: Usage-based billing for Halcyon teams
role: Design and build
outcome: "Live: 12 paying teams in week one"
live_url: https://halcyon.example.com/pricing
repo_url: https://code.example.com/asha-rao/halcyon-billing
started_on: 2026-10-20
shipped_on: 2026-11-06
last_verified_at: 2026-11-06T10:15:00Z
created_at: 2026-10-20T09:00:00Z
updated_at: 2026-11-06T10:15:00Z
tags: [nextjs, stripe]
---
```

### Ship event

Path `events/{yyyy}/{yyyy-mm-dd}-{project}-{id8}.md`, where the date is the `occurred_at` date. Keys: `id` R, `project` R, `kind` R, `surface` R, `summary` R (280), `proof_url`, `metric_label`, `metric_value` (number), `metric_unit`, `occurred_at` R, `created_at` R. Append only.

- Kind shipped or launched: set the project to `shipped` when it is idea, active or unknown, and set `shipped_on` if empty. Never change parked or archived.
- Store `proof_url` as given. Never fetch it.

Example, `events/2026/2026-11-06-halcyon-7fe7baaf.md`:

```md
---
id: 7fe7baaf-f981-4684-a558-9b8b1bd9dd15
project: halcyon
kind: shipped
surface: chat
summary: Shipped the Halcyon pricing page with monthly and yearly plans
proof_url: https://halcyon.example.com/pricing
metric_label: signups
metric_value: 25
metric_unit: users
occurred_at: 2026-11-06T10:00:00Z
created_at: 2026-11-06T10:15:00Z
---
```

### Decision

Path `decisions/{project}/{yyyy-mm-dd}-{id8}.md`, where the date is the `decided_at` date. Keys: `id` R, `project` R, `status` R, `surface` R, `superseded_by`, `title` R (120), `reason` R, body (optional, as the Markdown body), `decided_at` R, `created_at` R, `updated_at` R.

- A new decision has `status: accepted`.
- Superseding: the old file gets `status: superseded`, `superseded_by: NEW_UUID` and a new `updated_at`. Nothing else in it changes.

Example, `decisions/halcyon/2026-11-06-f15be5ba.md`:

```md
---
id: f15be5ba-5578-4a1c-9e3f-36140ccb1b59
project: halcyon
status: accepted
surface: chat
title: Use Supabase over Firebase
reason: "Row level security: tenant isolation without extra code"
decided_at: 2026-11-06T10:15:00Z
created_at: 2026-11-06T10:15:00Z
updated_at: 2026-11-06T10:15:00Z
---

Firebase rules were harder to test. Revisit if we need offline sync.
```

### Design asset

Path `design/{project}/{id8}.md`. Keys: `id` R, `project` R, `kind` R, `status` R, `surface` R, `title` R, `source_url`, `tokens_repo_url`, `tokens_path`, `created_at` R, `updated_at` R. A pointer only; token values live in the product repo. See design.md for each kind.

Example, `design/halcyon/b4b647d0.md`:

```md
---
id: b4b647d0-2371-43d0-8536-36140ccb1b59
project: halcyon
kind: handoff_bundle
status: approved
surface: code
title: Pricing page handoff
source_url: https://design.example.com/p/halcyon-pricing
created_at: 2026-11-06T10:15:00Z
updated_at: 2026-11-06T10:15:00Z
---
```

### Handoff

Path `handoffs/{id8}.md`. Keys: `id` R, `project` R, `from_surface` R, `to_surface` R (not `design`), `status` R, `title` R (120), body R (4,000, as the Markdown body), `created_at` R, `picked_up_at`, `done_at`.

- New: `status: open`, empty `picked_up_at` and `done_at`.
- Start: `status: picked_up`, `picked_up_at` set. Done or drop: `status: done` or `dropped`, `done_at` set.

Example, `handoffs/e16a056a.md`:

```md
---
id: e16a056a-46eb-4826-8ee6-64a531788284
project: halcyon
from_surface: chat
to_surface: code
status: open
title: Build the yearly plan toggle
created_at: 2026-11-06T10:15:00Z
picked_up_at:
done_at:
---

## Goal
Add a monthly or yearly toggle to the pricing page.

## Constraints
- Use the tokens in design/tokens.json
- Yearly price is 10 times monthly

## Done when
The toggle switches all three plan prices and the page passes its tests.
```
