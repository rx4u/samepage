# ADR-0027: A text-only plugin that calls the installed `sp`

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
The plugin directory refused v1.3.3 (aaf3919): "Files outside the allowed types accepted only from Verified organizations". From unverified publishers it accepts only Markdown, text, JSON, YAML and images (plus LICENSE, README, .gitignore and the icon). plugin/ shipped the `sp` Python package.

## Decision
- plugin/ holds only the two skills (`samepage`, `sp`), the manifest, the icon, LICENSE and README. No code, no hooks, no MCP servers.
- The skills call the `sp` command that the one-line install (ADR-0024) puts in `~/.local/bin`. When it is missing, they tell the user to run the one-line install and stop; they never download or run it themselves.
- tests/test_plugin_bundle.py fails on any file type the directory refuses.
- Supersedes the package list in ADR-0025. The `gh` credential hold leaves with the code.

## Consequences
- Claude Code users run the one line once. The plugin alone is not enough.
- Nothing runs from the plugin folder, so updates to `sp` arrive through the installer (run the line again), not through plugin updates.

## Verification
- [x] plugin/ has only allowed file types; `claude plugin validate --strict plugin` passes
- [x] `python3 -m unittest discover -s tests` and `python3 scripts/guardrails.py` pass
