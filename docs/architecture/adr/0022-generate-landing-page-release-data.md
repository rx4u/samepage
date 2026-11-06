# ADR-0022: Generate the landing page's release data from the repo

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
The landing page (ADR-0021) shows the version, the release headline, each tool's status and the MCP tool count. Typed into the HTML by hand, every release leaves them stale until someone remembers to edit the page.

## Options

### Option A: Generate `site/data.json` from repo files; the page bakes the values and refreshes from the file
- Pros: one source per value, all already in the repo; works with JavaScript off; no runtime host; CI catches drift.
- Cons: one more file to regenerate when a release is bumped.
- Price: 0 USD.

### Option B: Fetch the latest release from the GitHub API in the browser
- Pros: no file to regenerate.
- Cons: 60 unauthenticated requests an hour per visitor, a flicker on load, a third-party call at runtime (ADR-0021 forbids it), and it cannot see tool status.
- Price: 0 USD.

### Option C: Keep editing the HTML by hand
- Pros: nothing new.
- Cons: drifts at every release.
- Price: 0 USD.

## Decision
Option A. `scripts/site_data.py` (standard library only) writes `site/data.json` from:
- version: `.claude-plugin/plugin.json` (bumped at every release, B46), release link `releases/tag/v<version>`;
- headline: the `<!-- headline: ... -->` line in `docs/release/v<version>.md` (an HTML comment, so it does not show in the release notes);
- adapters: the README "Works with" table, whose status follows the tool ledger;
- tools: `sp.mcp.tool_specs()`, split into read and write.

`site/index.html` carries the same values in its markup and replaces them from `data.json` on load. `tests/test_site.py` fails when `data.json` is stale or the page's baked values disagree with it, and the release workflow runs `site_data.py --check` before it tags.

## Non-goals
A changelog page, live GitHub data, analytics.

## Consequences
- Gets easier: a release changes the page by regenerating one file.
- Gets harder: a version bump needs `python3 scripts/site_data.py` and the baked values in `site/index.html` updated in the same commit (the test says which).
- Follow-up tasks: none.

## Implementation plan
- Affected paths: scripts/site_data.py, site/data.json, site/index.html, tests/test_site.py, .github/workflows/release.yml, docs/release/v*.md (headline line).
- Pattern to follow: the page reads only `data.json` next to it.
- Pattern to avoid: any runtime call to another host.

## Verification
- [x] `python3 scripts/site_data.py --check` passes on main
- [x] tests/test_site.py passes
- [x] The page shows the same values with and without JavaScript

## Revisit when
The page needs data that is not in the repo.
