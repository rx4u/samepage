# samepage Notion template

A Notion store is one private page titled `samepage` with eight databases under it. The skill builds it for you when you say "set up samepage in Notion" with the Notion connector on (claude.ai or Claude Code). The exact steps the skill follows, every query and every write are in `skills/samepage/references/notion-backend.md`. This page is the same layout for people who want to build or check it by hand.

## Set it up by hand

1. In Notion, create a private page (not in a teamspace) titled `samepage`.
2. Inside it, create eight full-page databases named exactly as in the tables below, with exactly these property names and types. Select options must be the codes shown, lowercase, nothing else.
3. Make each `Project` relation two-way with Projects (Notion adds `Ship Events`, `Decisions`, `Design Assets` and `Handoffs` on Projects). Make Links `Profile` two-way (Notion adds `Links` on Profile). `Superseded by` on Decisions is a one-way relation to Decisions.
4. On Projects add the rollup `Last shipped`: relation `Ship Events`, property `Occurred`, calculate `Latest date`.
5. Add the saved views listed under "Views". The skill reads boot, inbox, rules and proof through them, which works on every Notion plan.
6. Add one Profile row, your links, your rules, and the reserved project `General` (slug `general`, status `active`, type `other`).
7. Save the page id (the 32 hex characters at the end of the page link) in `~/.samepage/config` as `notion_page_id`, or in your claude.ai preferences, with the view links the skill prints at the end of its setup.

The skill can also reuse a page you built: it checks each database, adds only missing properties and views, and never deletes or renames anything.

## Databases and properties

Every row has `UUID` (text): its permanent id, written once. Dates hold UTC date-times except `Started` and `Shipped on`, which are plain dates.

### Profile (exactly one row)
| Property | Type | Contract column |
|---|---|---|
| Name | title | profile.display_name |
| Headline | text | profile.headline |
| Location | text | profile.location |
| Bio | text | profile.bio |
| Voice | text | profile.voice |
| Owner handle | text | store_meta.owner_handle |
| Schema version | text | store_meta.schema_version (`1.0`) |
| Backend | select: github, notion | store_meta.backend_id (`notion`) |
| Created | date | profile.created_at, store_meta.created_at |
| Updated | date | profile.updated_at, store_meta.updated_at |
| Link list | text | serve-only copy of Links, `Label: url` joined by ` \| ` |
| Links | relation (from Links) | profile_link.profile_id |

### Links
| Property | Type | Contract column |
|---|---|---|
| Label | title | profile_link.label |
| Link | url | profile_link.url |
| Order | number | profile_link.sort_order |
| Profile | relation to Profile | profile_link.profile_id |
| UUID | text | profile_link.id |
| Created | date | profile_link.created_at |

### Rules
| Property | Type | Contract column |
|---|---|---|
| Rule | title | preference.rule (max 200 characters) |
| Surface | select: code, chat, cowork, design | preference.surface_id (empty = every surface) |
| Active | checkbox | preference.is_active |
| UUID | text | preference.id |
| Created | date | preference.created_at |
| Updated | date | preference.updated_at |

### Projects
| Property | Type | Contract column |
|---|---|---|
| Name | title | project.name |
| Slug | text | project.slug (lowercase words joined by `-`, unique) |
| Status | select: idea, active, shipped, parked, archived, unknown | project.status_id |
| Type | select: product, client_site, concept, skill, tool, content, other | project.type_id |
| One-liner | text | project.one_liner (max 140) |
| Problem | text | project.problem |
| Role | text | project.role |
| Outcome | text | project.outcome |
| Live URL | url | project.live_url |
| Repo URL | url | project.repo_url |
| Started | date | project.started_on |
| Shipped on | date | project.shipped_on |
| Last verified | date | project.last_verified_at |
| Archived | date | project.archived_at |
| Tags | multi-select | tag.label (option name), tag.slug (option name lowercased, other characters as `-`), project_tag |
| UUID | text | project.id |
| Created | date | project.created_at |
| Updated | date | project.updated_at |
| Last shipped | rollup: Ship Events, Occurred, latest date | serve-only (B5) |
| Ship Events, Decisions, Design Assets, Handoffs | relations (from the child databases) | reverse side of project_id |

### Ship Events
| Property | Type | Contract column |
|---|---|---|
| Summary | title | ship_event.summary (max 280) |
| Project | relation to Projects (two-way) | ship_event.project_id |
| Project slug | text | serve-only copy of the project's Slug |
| Kind | select: shipped, deployed, launched, milestone, metric, published | ship_event.kind_id |
| Surface | select: code, chat, cowork, design | ship_event.surface_id |
| Proof URL | url | ship_event.proof_url |
| Metric label | text | ship_event.metric_label |
| Metric value | number | ship_event.metric_value |
| Metric unit | text | ship_event.metric_unit |
| Occurred | date | ship_event.occurred_at |
| Created | date | ship_event.created_at |
| UUID | text | ship_event.id |

### Decisions
| Property | Type | Contract column |
|---|---|---|
| Title | title | decision.title (max 120) |
| Project | relation to Projects (two-way) | decision.project_id |
| Project slug | text | serve-only copy |
| Status | select: accepted, superseded, reversed | decision.status_id |
| Surface | select: code, chat, cowork, design | decision.surface_id |
| Superseded by | relation to Decisions (one-way) | decision.superseded_by_id |
| Reason | text | decision.reason |
| Decided | date | decision.decided_at |
| Created | date | decision.created_at |
| Updated | date | decision.updated_at |
| UUID | text | decision.id |
| page content | | decision.body |

### Design Assets
| Property | Type | Contract column |
|---|---|---|
| Title | title | design_asset.title |
| Project | relation to Projects (two-way) | design_asset.project_id |
| Project slug | text | serve-only copy |
| Kind | select: design_system, screen_set, handoff_bundle, prototype | design_asset.kind_id |
| Status | select: draft, approved, superseded | design_asset.status_id |
| Surface | select: code, chat, cowork, design | design_asset.surface_id |
| Source URL | url | design_asset.source_url |
| Tokens repo URL | url | design_asset.tokens_repo_url |
| Tokens path | text | design_asset.tokens_path |
| Created | date | design_asset.created_at |
| Updated | date | design_asset.updated_at |
| UUID | text | design_asset.id |

### Handoffs
| Property | Type | Contract column |
|---|---|---|
| Title | title | handoff.title (max 120) |
| Project | relation to Projects (two-way) | handoff.project_id |
| Project slug | text | serve-only copy |
| From | select: code, chat, cowork, design | handoff.from_surface_id |
| To | select: code, chat, cowork | handoff.to_surface_id (never design, B7) |
| Status | select: open, picked_up, done, dropped | handoff.status_id |
| Created | date | handoff.created_at |
| Picked up | date | handoff.picked_up_at |
| Done | date | handoff.done_at |
| UUID | text | handoff.id |
| page content | | handoff.body (required, max 4000) |

## Views

| Database | View name | Filter | Sort |
|---|---|---|---|
| Profile | sp boot | none | Created ascending |
| Rules | sp boot code / chat / cowork | Active is checked and (Surface is empty or Surface is that surface) | Created ascending, UUID ascending |
| Rules | sp rules | Active is checked | Created ascending, UUID ascending |
| Projects | sp active | Status is active and Slug is not general | Updated descending, UUID descending |
| Projects | sp proof | Last shipped is not empty and Slug is not general | Last shipped descending, UUID descending |
| Ship Events | sp recent | none | Occurred descending, UUID descending |
| Handoffs | sp boot code / chat / cowork | To is that surface and Status is open | Created descending, UUID descending |
| Handoffs | sp inbox code / chat / cowork | To is that surface and Status is open or picked_up | Created descending, UUID descending |

## Moving to a GitHub store

Export the `samepage` page from Notion (Export, "Markdown & CSV", "Include subpages" on), unzip it, then run:

```
python3 -m sp export --from-notion-csv ~/Downloads/samepage-export --out ~/samepage-store
```

No Notion token is needed. The command refuses a folder that already exists and writes nothing unless the result passes `sp check`. Add `--utc-offset +05:30` if your Notion workspace shows dates in a time zone other than UTC.

## Demo store

A synthetic store loaded from `fixtures/small` (fake person Asha Rao, example.com links) for release testing. It is a private draft page in the maintainer's workspace.

- Page: samepage demo store (synthetic), https://app.notion.com/p/410a0a72a54681e1b1d9fee370db0031

| Database | Data source | Database page |
|---|---|---|
| Profile | collection://d57d66dc-32a0-465f-a724-908603d70ef7 | 210cbefea39640b185279efa0c422fa8 |
| Links | collection://0387cc83-84b1-4d53-bcf5-ae257727924a | 2d241a82c8cc4fb4a193901c62e8612e |
| Rules | collection://81a89fa1-4b8a-474b-a43b-fc22c92ff1e8 | d5ad4acc438c484ebfed32fc43627235 |
| Projects | collection://370d648e-026f-4fcd-951f-cf07be95d8d4 | 06b3f0ba6c104d58ae557569eb5134c0 |
| Ship Events | collection://9b2143f4-dd82-4585-8b7c-e17fafaa3494 | 7ebf8bc2228b4305956d026956a39724 |
| Decisions | collection://e3fea836-1c4b-44d2-9dc9-7594b188f656 | a055e537d5af45a19efe2bcc8979b38d |
| Design Assets | collection://d4167a0f-5113-4a4c-9900-43ff64b96fd5 | 9cfc37f34a8e4bb189562b0f10274110 |
| Handoffs | collection://53f2e54d-22b7-4710-9b49-852a6922a824 | 30ba72a4bbf84c33bbf78dc3ee68c38d |

| View | URL |
|---|---|
| Profile: sp boot | view://410a0a72-a546-814e-9bf3-000cd109f660 |
| Rules: sp boot code | view://410a0a72-a546-81f2-92d7-000c7bf39f29 |
| Rules: sp boot chat | view://410a0a72-a546-8176-8b42-000ccdc445d9 |
| Rules: sp boot cowork | view://410a0a72-a546-8188-8754-000cff8a5bec |
| Rules: sp rules | view://410a0a72-a546-815e-b94e-000ca4b2a94e |
| Projects: sp active | view://410a0a72-a546-8166-95a2-000c9f2224bb |
| Projects: sp proof | view://410a0a72-a546-81ef-b691-000c4e1e602b |
| Ship Events: sp recent | view://410a0a72-a546-81f4-99f9-000c98bf2358 |
| Handoffs: sp boot code | view://410a0a72-a546-8194-80e6-000cbbfcd925 |
| Handoffs: sp boot chat | view://410a0a72-a546-8180-952a-000c09d9ba4b |
| Handoffs: sp boot cowork | view://410a0a72-a546-81bd-8161-000c475dfb89 |
| Handoffs: sp inbox code | view://410a0a72-a546-8135-a5ed-000cba1561fd |
| Handoffs: sp inbox chat | view://410a0a72-a546-81af-bbd3-000c121673aa |
| Handoffs: sp inbox cowork | view://410a0a72-a546-816c-ac99-000c4fe014d6 |

Loaded: 1 profile row (with store fields), 2 links, 5 rules, 20 projects with 7 tag options, 40 ship events, 10 decisions (one supersede chain), 3 design assets, 5 handoffs. Checked on 2026-11-06 against `sp index` of `fixtures/small`: the four boot queries for chat equal `index/boot/chat.md` (3 rules, 5 active projects in order, 2 open handoffs), `sp inbox code` equals `index/handoffs-code-1.md`, `sp rules` equals `index/rules.md`, `sp proof` returns the 19 projects of `index/proof-1.md` in the same order, and the AI tag query returns the 5 projects of `index/tags/ai.md` in the same order.
