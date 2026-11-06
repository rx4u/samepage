# ADR-0026: No hooks in the plugin; session start lives in the user's settings

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
The plugin directory held the plugin for its SessionStart and Stop hooks (shell scripts that run python3) and warned that command hooks and .sh files will later be accepted only from Verified organizations. The owner chose (2026-11-06): remove them from the plugin.

## Decision
- plugin/ ships no hooks/ folder and no .sh file. The Stop nudge is dropped.
- `sp setup claude-code`, and so `sp start` and the one-line install, add one SessionStart entry to `~/.claude/settings.json` running the installed `hooks/session-start.sh`. Every other setting stays, the old file is kept as `.samepage-backup`, and running it again changes nothing.
- Without that entry, Claude Code loads context when asked ("what am I working on?") or with `/sp boot`; the skill runs boot once before the first task when no context block is present.
- Supersedes the hook part of ADR-0025.

## Consequences
- Directory listing: no hooks, no shell scripts. The one remaining hold is the user's own `gh` login in `sp init`.
- A plugin-only install no longer loads context by itself until `sp setup claude-code` or the one-line install runs.

## Verification
- [x] plugin/ has no .sh file; `claude plugin validate --strict plugin` passes
- [x] `sp start` adds the entry once, keeps other hooks and settings, and writes a backup
- [x] `python3 -m unittest discover -s tests` and `python3 scripts/guardrails.py` pass
