# Data dictionary

Lookup tables share one shape: `id` (logical only) and `code` (what files and Notion store). Writers are the skill (modes named in brackets) and the `sp` CLI.

| Column | Type | Meaning | Writer | Written when | Source | Read by |
|---|---|---|---|---|---|---|
| `backend.id` | smallint | Logical id | Spec | Spec release | schema/lookups.json | Store check |
| `backend.code` | text | github or notion | Spec | Spec release | schema/lookups.json | Setup, Store check |
| `surface.id` | smallint | Logical id | Spec | Spec release | schema/lookups.json | Store check |
| `surface.code` | text | code, chat, cowork, design | Spec | Spec release | schema/lookups.json | Session boot, Chat recall, Handoff inbox, Rules |
| `project_status.id` | smallint | Logical id | Spec | Spec release | schema/lookups.json | Store check |
| `project_status.code` | text | idea, active, shipped, parked, archived, unknown | Spec | Spec release | schema/lookups.json | Session boot, Project detail |
| `project_type.id` | smallint | Logical id | Spec | Spec release | schema/lookups.json | Store check |
| `project_type.code` | text | product, client_site, concept, skill, tool, content, other | Spec | Spec release | schema/lookups.json | Project detail, Proof lookup |
| `event_kind.id` | smallint | Logical id | Spec | Spec release | schema/lookups.json | Store check |
| `event_kind.code` | text | shipped, deployed, launched, milestone, metric, published | Spec | Spec release | schema/lookups.json | Log entry, Proof lookup |
| `asset_kind.id` | smallint | Logical id | Spec | Spec release | schema/lookups.json | Store check |
| `asset_kind.code` | text | design_system, screen_set, handoff_bundle, prototype | Spec | Spec release | schema/lookups.json | Design pointer, Design handoff capture |
| `asset_status.id` | smallint | Logical id | Spec | Spec release | schema/lookups.json | Store check |
| `asset_status.code` | text | draft, approved, superseded | Spec | Spec release | schema/lookups.json | Design pointer |
| `decision_status.id` | smallint | Logical id | Spec | Spec release | schema/lookups.json | Store check |
| `decision_status.code` | text | accepted, superseded, reversed | Spec | Spec release | schema/lookups.json | Decision record |
| `handoff_status.id` | smallint | Logical id | Spec | Spec release | schema/lookups.json | Store check |
| `handoff_status.code` | text | open, picked_up, done, dropped | Spec | Spec release | schema/lookups.json | Handoff inbox |
| `build_status.id` | smallint | Logical id | Spec | Spec release | schema/lookups.json | Store check |
| `build_status.code` | text | running, succeeded, failed | Spec | Spec release | schema/lookups.json | Store check |
| `store_meta.id` | smallint | Always 1 | `sp init`, skill (setup) | Setup | constant | Store check |
| `store_meta.schema_version` | text | Spec major.minor the store follows | `sp init`, `sp migrate` | Setup, migration | spec version | Store check, Session boot |
| `store_meta.backend_id` | smallint | Backend in use | `sp init`, skill (setup) | Setup | user choice | Setup, Store check |
| `store_meta.owner_handle` | text | GitHub login or Notion user name | `sp init`, skill (setup) | Setup | gh or Notion connector | Store check |
| `store_meta.created_at` | timestamptz | Store creation time, UTC | `sp init`, skill (setup) | Setup | clock | Store check |
| `store_meta.updated_at` | timestamptz | Last change to store settings | `sp init`, `sp migrate` | Setup, migration | clock | Store check |
| `profile.id` | smallint | Always 1 | `sp init`, skill (setup) | Setup | constant | Store check |
| `profile.display_name` | text | Name used in proposals and bios | skill (setup, profile) | Setup, profile edit | user | Session boot, Chat recall |
| `profile.headline` | text | One-line professional identity | skill (setup, profile) | Setup, profile edit | user | Session boot, Chat recall |
| `profile.location` | text | City and country, display only | skill (setup, profile) | Setup, profile edit | user | Chat recall |
| `profile.bio` | text | Short bio, display only | skill (profile) | Profile edit | user | Chat recall |
| `profile.voice` | text | How the owner writes, display only | skill (profile) | Profile edit | user | Session boot, Chat recall |
| `profile.created_at` | timestamptz | Creation time | `sp init`, skill (setup) | Setup | clock | Store check |
| `profile.updated_at` | timestamptz | Last profile edit | skill (profile) | Profile edit | clock | Store check |
| `profile_link.id` | uuid | Link id | skill (setup, profile) | Setup, profile edit | generated | Chat recall |
| `profile_link.profile_id` | smallint | Always 1 | skill (setup, profile) | Setup, profile edit | constant | Store check |
| `profile_link.label` | text | Portfolio, GitHub, Dribbble, site | skill (setup, profile) | Setup, profile edit | user | Chat recall |
| `profile_link.url` | text | Full URL with https | skill (setup, profile) | Setup, profile edit | user | Chat recall |
| `profile_link.sort_order` | smallint | Display order, 1 first | skill (setup, profile) | Setup, profile edit | user | Chat recall |
| `profile_link.created_at` | timestamptz | Creation time | skill (setup, profile) | Setup, profile edit | clock | Store check |
| `preference.id` | uuid | Rule id | skill (rules) | Rule added | generated | Rules |
| `preference.rule` | text | The rule, 200 chars max, imperative | skill (rules) | Rule added or edited | user | Session boot, Chat recall, Rules |
| `preference.surface_id` | smallint | Surface the rule is limited to; empty = all | skill (rules) | Rule added or edited | user | Session boot, Chat recall, Rules |
| `preference.is_active` | boolean | Rule in force | skill (rules) | Rule added, paused | user | Session boot, Chat recall, Rules |
| `preference.created_at` | timestamptz | Creation time | skill (rules) | Rule added | clock | Rules |
| `preference.updated_at` | timestamptz | Last edit | skill (rules) | Rule edited | clock | Store check |
| `tag.id` | uuid | Tag id | skill (log), `sp log` | First use of a slug | generated | Store check |
| `tag.slug` | text | Lowercase kebab tag, e.g. nextjs | skill (log), `sp log` | First use | user or drafted from stack | Proof lookup, Project detail |
| `tag.label` | text | Display label, e.g. Next.js | skill (log), `sp log` | First use | user | Proof lookup |
| `tag.created_at` | timestamptz | Creation time | skill (log), `sp log` | First use | clock | Store check |
| `project.id` | uuid | Project id | skill (log), `sp log` | Project created | generated | every project screen |
| `project.slug` | text | Stable kebab id, never changed | skill (log), `sp log` | Project created | user, drafted from name | Session boot, Chat recall, Log entry, Proof lookup, Project detail, Handoff inbox |
| `project.name` | text | Display name | skill (log), `sp log` | Created, renamed | user | Session boot, Chat recall, Proof lookup, Project detail |
| `project.status_id` | smallint | Lifecycle status | skill (log, archive), `sp log` | Created, status change | user | Session boot, Chat recall, Proof lookup, Project detail |
| `project.type_id` | smallint | Kind of project | skill (log), `sp log` | Created | user | Proof lookup, Project detail |
| `project.one_liner` | text | What it is, 140 chars | skill (log), `sp log` | Created, edited | user | Session boot, Chat recall, Proof lookup, Project detail |
| `project.problem` | text | Problem it solves, display only | skill (log) | Created, edited | user | Project detail, Proof lookup |
| `project.role` | text | Owner's role on it, display only | skill (log) | Created, edited | user | Proof lookup, Project detail |
| `project.outcome` | text | Result in one sentence, display only | skill (log) | Shipped, edited | user | Proof lookup, Project detail |
| `project.live_url` | text | Live product or site | skill (log), `sp log` | Shipped, edited | user | Proof lookup, Project detail |
| `project.repo_url` | text | Source repo. Agent call (B14): `git@host:owner/repo.git` becomes `https://host/owner/repo`; host, owner and repo lowercased; trailing `.git` and `/` removed | skill (log), `sp log` | Created, edited | git remote or user | Session boot, Project detail |
| `project.started_on` | date | Start date | skill (log), `sp log` | Created | user or first commit date | Project detail |
| `project.shipped_on` | date | First ship date | skill (log), `sp log` | Status to shipped | first shipped event | Proof lookup, Project detail |
| `project.last_verified_at` | timestamptz | Last time the owner confirmed this row | skill (log), `sp log` | Any confirmed write to the project | clock | Project detail |
| `project.archived_at` | timestamptz | When archived | skill (archive) | Status to archived | clock | Project detail |
| `project.created_at` | timestamptz | Creation time | skill (log), `sp log` | Created | clock | Store check |
| `project.updated_at` | timestamptz | Last change, sort key for active lists | skill (log), `sp log` | Any write to the project or its children | clock | Session boot, Chat recall |
| `project_tag.project_id` | uuid | Tagged project | skill (log), `sp log` | Tags set | user | Proof lookup |
| `project_tag.tag_id` | uuid | Tag | skill (log), `sp log` | Tags set | user | Proof lookup |
| `project_tag.created_at` | timestamptz | When tagged | skill (log), `sp log` | Tags set | clock | Store check |
| `ship_event.id` | uuid | Event id | skill (log), `sp log` | Logged | generated | Proof lookup |
| `ship_event.project_id` | uuid | Project it belongs to | skill (log), `sp log` | Logged | user | Proof lookup, Project detail |
| `ship_event.kind_id` | smallint | What happened | skill (log), `sp log` | Logged | user, drafted | Proof lookup, Project detail |
| `ship_event.surface_id` | smallint | Surface it was logged from | skill (log), `sp log` | Logged | runtime | Project detail |
| `ship_event.summary` | text | What happened, 280 chars | skill (log), `sp log` | Logged | drafted from session, confirmed | Proof lookup, Project detail, Session boot |
| `ship_event.proof_url` | text | Public link that proves it | skill (log), `sp log` | Logged | user | Proof lookup |
| `ship_event.metric_label` | text | Metric name, e.g. signups | skill (log), `sp log` | Logged | user | Proof lookup |
| `ship_event.metric_value` | numeric | Metric value | skill (log), `sp log` | Logged | user | Proof lookup |
| `ship_event.metric_unit` | text | Unit, e.g. users, ms, INR | skill (log), `sp log` | Logged | user | Proof lookup |
| `ship_event.occurred_at` | timestamptz | When it happened, sort key | skill (log), `sp log` | Logged | user, default now | Proof lookup, Project detail, Session boot |
| `ship_event.created_at` | timestamptz | When it was logged | skill (log), `sp log` | Logged | clock | Store check |
| `decision.id` | uuid | Decision id | skill (decision) | Logged | generated | Decision record |
| `decision.project_id` | uuid | Project | skill (decision) | Logged | user | Decision record, Project detail |
| `decision.status_id` | smallint | accepted, superseded, reversed | skill (decision) | Logged, superseded | user | Decision record, Session boot |
| `decision.surface_id` | smallint | Surface where decided | skill (decision) | Logged | runtime | Decision record |
| `decision.superseded_by_id` | uuid | Replacing decision | skill (decision) | New decision logged with supersedes | user | Decision record |
| `decision.title` | text | The decision, 120 chars | skill (decision) | Logged | user | Decision record, Session boot, Project detail |
| `decision.reason` | text | Why, display only | skill (decision) | Logged | user | Decision record, Project detail |
| `decision.body` | text | Detail, display only | skill (decision) | Logged | user | Decision record |
| `decision.decided_at` | timestamptz | When decided, sort key | skill (decision) | Logged | user, default now | Decision record, Project detail |
| `decision.created_at` | timestamptz | When logged | skill (decision) | Logged | clock | Store check |
| `decision.updated_at` | timestamptz | Last status change | skill (decision) | Superseded or reversed | clock | Store check |
| `design_asset.id` | uuid | Asset id | skill (design), `sp log design` | Logged | generated | Design pointer |
| `design_asset.project_id` | uuid | Project | skill (design), `sp log design` | Logged | user | Design pointer, Design handoff capture |
| `design_asset.kind_id` | smallint | design_system, screen_set, handoff_bundle, prototype | skill (design), `sp log design` | Logged | user | Design pointer, Design handoff capture, Session boot |
| `design_asset.status_id` | smallint | draft, approved, superseded | skill (design), `sp log design` | Logged, approved | user | Design pointer, Session boot |
| `design_asset.surface_id` | smallint | Surface it was logged from | skill (design), `sp log design` | Logged | runtime | Design pointer |
| `design_asset.title` | text | Name of the system, screen set or handoff | skill (design), `sp log design` | Logged | user or bundle title | Design pointer, Design handoff capture, Session boot |
| `design_asset.source_url` | text | Claude Design share link or file link | skill (design), `sp log design` | Logged | user | Design pointer, Design handoff capture |
| `design_asset.tokens_repo_url` | text | Repo that holds the tokens file | skill (design), `sp log design` | Logged | user or project.repo_url | Design pointer, Session boot |
| `design_asset.tokens_path` | text | Path to W3C tokens file in that repo | skill (design), `sp log design` | Logged | user, default design/tokens.json | Design pointer, Session boot |
| `design_asset.created_at` | timestamptz | When logged | skill (design), `sp log design` | Logged | clock | Store check |
| `design_asset.updated_at` | timestamptz | Last status change, sort key | skill (design), `sp log design` | Logged, approved | clock | Design pointer |
| `handoff.id` | uuid | Handoff id | skill (handoff), `/sp handoff` | Created | generated | Handoff inbox |
| `handoff.project_id` | uuid | Project | skill (handoff), `/sp handoff` | Created | user or current repo | Handoff inbox |
| `handoff.from_surface_id` | smallint | Where it was written | skill (handoff), `/sp handoff` | Created | runtime | Handoff inbox |
| `handoff.to_surface_id` | smallint | Where it should be picked up | skill (handoff), `/sp handoff` | Created | user | Handoff inbox, Session boot, Chat recall |
| `handoff.status_id` | smallint | open, picked_up, done, dropped | skill (handoff), `/sp handoff` | Created, picked up, done | user | Handoff inbox, Session boot, Chat recall |
| `handoff.title` | text | Short title, 120 chars | skill (handoff), `/sp handoff` | Created | user, drafted | Handoff inbox, Session boot, Chat recall |
| `handoff.body` | text | The brief, 4,000 chars | skill (handoff), `/sp handoff` | Created | drafted from chat, confirmed | Handoff inbox |
| `handoff.created_at` | timestamptz | Created, sort key | skill (handoff), `/sp handoff` | Created | clock | Handoff inbox |
| `handoff.picked_up_at` | timestamptz | When picked up | skill (handoff), `/sp handoff` | Picked up | clock | Handoff inbox |
| `handoff.done_at` | timestamptz | When closed | skill (handoff), `/sp handoff` | Done or dropped | clock | Handoff inbox |
| `index_build.id` | uuid | Build id | `sp index` | Each rebuild | generated | Store check |
| `index_build.status_id` | smallint | running, succeeded, failed | `sp index` | Start and end of rebuild | runtime | Store check, Session boot |
| `index_build.commit_sha` | text | Store commit the index was built from | `sp index` | Start of rebuild | git | Session boot, Store check |
| `index_build.entry_count` | integer | Rows read | `sp index` | End of rebuild | count | Store check |
| `index_build.boot_chars` | integer | Largest boot file size in characters | `sp index` | End of rebuild | count | Store check |
| `index_build.error` | text | Failure message | `sp index` | Failed rebuild | runtime | Store check |
| `index_build.started_at` | timestamptz | Start, sort key | `sp index` | Start of rebuild | clock | Store check, Session boot |
| `index_build.finished_at` | timestamptz | End | `sp index` | End of rebuild | clock | Store check |
| `index_build.created_at` | timestamptz | Row creation | `sp index` | Start of rebuild | clock | Store check |
