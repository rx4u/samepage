# Decisions

| ADR | Title | Status | Date |
|---|---|---|---|
| [0001](0001-choose-distribution-and-hosting.md) | Choose distribution and hosting | accepted | 2026-11-06 |
| [0002](0002-choose-store-backends.md) | Choose store backends | accepted | 2026-11-06 |
| [0003](0003-adopt-logical-schema-with-file-adapters.md) | Adopt a logical schema with file and Notion adapters | accepted | 2026-11-06 |
| [0004](0004-adopt-write-time-serve-layer.md) | Adopt a write-time serve layer | accepted | 2026-11-06 |
| [0005](0005-adopt-precomputed-page-files.md) | Adopt precomputed page files and cursor paging | accepted | 2026-11-06 |
| [0006](0006-choose-auth-method.md) | Choose auth method | accepted | 2026-11-06 |
| [0007](0007-adopt-never-do-rules.md) | Adopt the never-do rules | accepted | 2026-11-06 |
| [0008](0008-restrict-ai-drafting-to-log-modes.md) | Restrict AI drafting to log modes | accepted | 2026-11-06 |
| [0009](0009-use-demo-store-as-staging.md) | Use a demo store as staging | accepted | 2026-11-06 |
| [0010](0010-choose-public-name.md) | Choose the public name | accepted | 2026-11-06 |
| [0011](0011-define-claude-design-integration.md) | Define the Claude Design integration | accepted | 2026-11-06 |
| [0012](0012-choose-python-stdlib-cli.md) | Choose a Python standard library CLI | accepted | 2026-11-06 |
| [0013](0013-choose-repo-owner-account.md) | Choose where the public repo lives | accepted | 2026-11-06 |
| [0014](0014-package-one-skill-with-modes.md) | Package one skill with modes | accepted | 2026-11-06 |

Statuses: proposed, accepted, rejected, deprecated, superseded.
A superseded ADR links to its replacement and the replacement links back. History is never rewritten;
learnings are appended under More information with a date.

Required first set coverage: hosting (0001), database plan (0002, 0003), auth (0006), data layers (0004), paging (0005), where AI calls are allowed (0008), staging (0009), never-do rules (0007).
