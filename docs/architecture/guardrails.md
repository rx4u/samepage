# Guardrails

| Rule | Enforced by | Fails | Allow list |
|---|---|---|---|
| No unbounded reads: every list read passes a limit of 50 or less | `sp` argument check and unit test with the fake reader | Merge | None |
| No reader globs raw store folders except `sp check` and `sp index` | CI grep for directory walks (os.walk, os.listdir, os.scandir, glob, iterdir) outside the allow list | Merge | sp/check.py, sp/index.py; non-store readers per ADR-0015: sp/schema.py, sp/fixtures.py, sp/export.py; per ADR-0020: sp/setup.py (copies skills/samepage/) |
| No offset or row-skip paging | CI grep for `skip`, `offset` in sp/ and skill references | Merge | None |
| Boot file under 8,000 characters | `sp check` on fixtures/perf | Merge | None |
| Only Python standard library imports | CI import scan | Merge | None |
| No new dependency without ADR | CI diff check on workflows and plugin manifests | Merge | adr/ references |
| No maintainer-hosted endpoints | CI grep for http URLs outside docs, example hosts and github.com (the store backend, ADR-0016), in sp/, hooks/, commands/, skills/ and install.sh | Merge | docs/, README.md |
| No token or credential handling | CI grep for token, secret, password variables in sp/, hooks/, commands/, skills/ and install.sh | Merge | None |
| No store content outside the store | Test: the `sp context` block contains no line of any fixture boot file | Merge | None |
| MCP stdout carries protocol only | Protocol test: every stdout line of `sp mcp` parses as one JSON-RPC message | Merge | None |
| No ChatGPT adapter (ADR-0019) | CI grep for chatgpt in sp/, skills/, commands/, hooks/ | Merge | None |
| SKILL.md under 500 lines, description under 1,024 characters, no XML brackets in frontmatter | CI script | Merge | None |
| No em dashes in skill, docs, README, install.sh and every runtime file (house style) | CI grep for U+2014 | Merge | None |
| Store Action never commits when `sp check` fails | workflow step order | Store push (user's repo) | None |
| Every frontmatter key is in schema/fields.json | `sp check` | Store push and Merge | None |

Allow lists only shrink. Adding an entry needs an ADR.
