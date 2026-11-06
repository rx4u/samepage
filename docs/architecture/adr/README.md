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
| [0015](0015-allow-non-store-folder-readers.md) | Allow non-store folder readers | accepted | 2026-11-06 |
| [0016](0016-adopt-one-click-store-and-guided-setup.md) | Adopt a one-click store and guided setup | accepted | 2026-11-06 |
| [0017](0017-adopt-surfaces-as-roles-with-tool-field.md) | Adopt surfaces as roles, with a tool field | accepted | 2026-11-06 |
| [0018](0018-adopt-multi-tool-adapters.md) | Adopt multi-tool adapters (instruction files, local MCP, portable skill) | accepted | 2026-11-06 |
| [0019](0019-leave-chatgpt-out-of-v1.md) | Leave ChatGPT out of v1 | accepted | 2026-11-06 |
| [0020](0020-adopt-installer-and-sp-setup.md) | Adopt an installer and `sp setup` | accepted | 2026-11-06 |
| [0021](0021-host-landing-page-as-static-files-on-vercel.md) | Host the landing page as static files on Vercel | accepted | 2026-11-06 |
| [0022](0022-generate-landing-page-release-data.md) | Generate the landing page's release data from the repo | accepted | 2026-11-06 |
| [0023](0023-link-two-stores-for-rules-and-decisions.md) | Link two stores and share rules and decisions both ways | accepted | 2026-11-06 |
| [0024](0024-one-line-install-with-sp-start.md) | One-line install with `sp start` | accepted | 2026-11-06 |

Statuses: proposed, accepted, rejected, deprecated, superseded.
A superseded ADR links to its replacement and the replacement links back. History is never rewritten;
learnings are appended under More information with a date.

Required first set coverage: hosting (0001), database plan (0002, 0003), auth (0006), data layers (0004), paging (0005), where AI calls are allowed (0008), staging (0009), never-do rules (0007).
