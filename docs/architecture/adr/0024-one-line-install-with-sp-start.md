# ADR-0024: One-line install with `sp start`

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
Getting started took two to five commands per tool, a choice between four paths, and a store-creation step with questions (name, headline, rules). The owner chose (2026-11-06): one line, copied once, that installs samepage, makes the store without asking, and connects every tool on the machine.

Claude Code's own CLI installs a plugin without prompts (`claude plugin marketplace add rx4u/samepage`, `claude plugin install samepage@samepage`; both are safe to run again, checked 2026-11-06), so the installer can do the Claude Code step too.

## Options

### Option A: `curl -fsSL https://samepage-sigma.vercel.app/install | sh`, which runs `sp start`
- Pros: one line; the script is the repo's own install.sh served as a static file (no server, ADR-0001, ADR-0021); `sp start` reuses `sp init` and `sp setup`.
- Cons: some people distrust `curl | sh`. The README links the script so it can be read first, and the old two-step clone path still works.
- Price: 0 USD.

### Option B: A setup wizard on the landing page that prints custom commands
- Cons: still several commands to paste.

### Option C: Keep the four paths
- Cons: the reason for this ADR.

## Decision
Option A.

- `site/install` is a byte-for-byte copy of `install.sh`. `scripts/site_data.py` writes it and `--check` fails when it drifts.
- install.sh wraps its body in a function called on the last line (a cut-off download runs nothing), then runs `sp start` with stdin closed. `SAMEPAGE_NO_START=1` skips it.
- `sp start [--dry-run]` asks nothing and prints every step:
  1. Store. An existing config is reused. Otherwise, with a signed-in GitHub CLI: connect `LOGIN/samepage-store` if it exists, else create it private (the `sp init` path). Without the GitHub CLI: a local store in `~/.samepage/store`. A later `sp start` with the GitHub CLI signed in publishes that local store as a private `samepage-store` repo.
  2. Profile, without questions: the name from the GitHub account, else git `user.name`, else the login name; the headline "Building with AI tools". Both are plain fields the user edits later. No rules are added.
  3. Tools: every tool found on the machine is connected. Claude Code (the `claude` command) gets the plugin through its CLI. Codex, Gemini CLI, Copilot, Cursor, Windsurf and Claude Desktop (found by command or config folder) get the MCP entry and skill through `sp setup`'s config and skill steps, with the same backups and the same snippet-only rule for unverified paths. The per-project instruction file is not written (the shell's folder is rarely a project); start prints `sp setup TOOL` for that.
  4. claude.ai and Cowork cannot be set up from a terminal: start prints the skill link.
- No tokens are read or stored. GitHub access is the user's own `gh` login (ADR-0006).

## Non-goals
Windows, a team rollout, a hosted installer that varies by user, changing any store record type.

## Consequences
- Gets easier: one line from zero to every local tool connected.
- Gets harder: install.sh now edits tool configs on first run, so its output must list every file it changed.
- Follow-up: submit the plugin to the official directory so the Claude desktop app finds it by search.

## Implementation plan
- Affected paths: install.sh, new sp/start.py, sp/__main__.py, scripts/site_data.py, site/install, site/index.html, README.md, docs/architecture/scope.md, tests/test_start.py.
- Pattern to follow: `sp.init.init` for the store, `sp.setup.config_step` and `skill_step` for tools.
- Pattern to avoid: prompts, reading stdin, editing shell profiles, any network call beyond GitHub, the user's git remote and Claude Code's own plugin commands.

## Verification
- [x] With no GitHub CLI and no tools, `sp start` makes a local store and says what it skipped
- [x] A fake `claude` on PATH receives the marketplace add and install calls
- [x] A `~/.codex` folder gets the MCP entry with a backup
- [x] A second `sp start` changes nothing and reports the store it reused
- [x] `site/install` matches install.sh (`site_data.py --check`)
- [x] `python3 -m unittest discover -s tests` and `python3 scripts/guardrails.py` pass

## Revisit when
Windows users ask, or a tool's config path changes.
