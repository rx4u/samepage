# ADR-0025: Ship a slim plugin folder

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
B21 made the repo root the plugin. The plugin directory's validator (claude.ai/directory/manage) scanned the whole root on its first run (main @ e690862): 1 blocking finding (the fake API key in tests/test_write.py that proves `sp check` blocks secrets), 14 policy holds and 13 warnings, most from files a plugin never runs (tests, docs, the landing page, brand images, the vendored three.min.js, the samepage.skill zip, CLAUDE.md).

## Options
- A: a generated `plugin/` folder with only what the plugin runs; the marketplace installs it and the directory reviews it. Pros: nothing test-only ships; existing `samepage@samepage` installs update in place. Cons: a second copy of the source in the repo, kept equal by a check.
- B: rewrite the test secret and move files out of the root. Cons: the root would still ship docs and the site.
- C: a separate plugin repo. Cons: two repos to release.

## Decision
Option A.
- `scripts/build_plugin.py` copies sp/, hooks/, commands/, skills/, schema/, store-template/, sp_run.py, LICENSE and .claude-plugin/plugin.json and icon.png into `plugin/`, and writes a plugin README that says what the plugin runs, reads and writes. `--check` fails when plugin/ differs; tests/test_plugin_bundle.py runs it.
- `.claude-plugin/marketplace.json` lists the plugin with source `./plugin`. The root `.claude-plugin/plugin.json` stays the version source for releases (B46) and site data (ADR-0022).
- Hooks use `command` plus `args` instead of one command string, as the validator asks.
- The directory submission uses Plugin path `plugin`.
- Supersedes B21 for what is installed; the root stays the source.

## Consequences
- Every source change needs `python3 scripts/build_plugin.py` before commit; the test catches a miss.
- Expected holds that stay for a reviewer: hooks run python3, `sp init` uses the user's own gh login, the README documents a download-and-run line.

## Verification
- [x] `claude plugin validate --strict plugin` passes
- [x] A clean home installs `samepage@samepage` from the marketplace and gets only plugin/'s files; the SessionStart hook runs
- [x] `python3 -m unittest discover -s tests` and `python3 scripts/guardrails.py` pass
