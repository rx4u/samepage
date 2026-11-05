# Targets

There are no web routes, so browser vitals do not apply. Context budget replaces page weight: what a surface loads at boot is the "first paint".

| Area | Target | Number | Check |
|---|---|---|---|
| Context | Boot file size per surface | 2,000 tokens (8,000 characters) | `sp check` exits 1 when any file in `index/boot/` exceeds 8,000 characters; runs in the store Action and in CI on the demo store |
| Context | Project section size | 1,500 tokens (6,000 characters) | `sp check` exits 1 when any file in `index/project/` exceeds 6,000 characters |
| Context | Reads per boot, GitHub store | 1 file | Skill test fixture asserts one get_file_contents call in boot mode (WP-07) |
| Context | Reads per boot, Notion store | 4 queries | Skill reference lists exactly 4 queries for boot; review checklist in PR template |
| Speed | SessionStart hook duration | 3 s p95 | hooks.json timeout set to 3 s; hook falls back to the cached boot file; `sp boot --time` logged in CI on demo store |
| Speed | Index rebuild after a push | 90 s | Store Action job `timeout-minutes: 3`; failure emails the owner via GitHub |
| Speed | `sp index` on a 1,000 project, 5,000 event store | 5 s | Perf job in CI on generated fixtures fails above 5 s |
| Data | Rows per read | 50 max | `sp` rejects `--limit` above 50; Notion reference sets page_size 20 and never above 50 |
| Data | Default list size | 20 | Index files and Notion queries hold 20 rows per page |
| Setup | Time to first working boot | 10 min | Timed runs with 5 testers before launch, results in docs/launch/setup-tests.md |
| Scale | Projects per store at month 12 | 300 | Demo store perf fixture uses 1,000 projects |
| Scale | Ship events per store at month 12 | 5,000 | Demo store perf fixture uses 5,000 events |
| Cost | Infra cost per user per month | 0 USD | CI fails if any hosted-service config or paid API client is added to the manifest |
| Cost | Store Action minutes per month | 200 min | Rebuild under 30 s per push; private repos get 2,000 free minutes; `sp stats` reports runs |
| Reliability | Silent index failures | 0 | Action fails loudly; every serve file header carries the build commit and time; boot warns when header is older than the latest entry |
| Reliability | Schema compatibility | 0 breaking changes within a major version | CI runs `sp check` against stores at every released schema version |
| Security | Secrets committed to a store | 0 | `sp check` secret patterns plus GitHub push protection enabled by `sp init` |
| Privacy | Public stores created by samepage | 0 | `sp init` creates private only; `sp check` warns when the repo is public |
| Quality | SKILL.md length | 500 lines | CI line count on skills/samepage/SKILL.md |

Default page size is 20 rows for lists. The 50-row ceiling is the hard maximum for any single read.
Change either only with an ADR.
