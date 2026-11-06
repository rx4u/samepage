# ADR-0020: Adopt an installer and `sp setup`

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
Outside Claude Code, `sp` has no home: the plugin bundles it and calls it from `${CLAUDE_PLUGIN_ROOT}` (B10). Codex, Cursor and the rest need `sp` on the machine, an MCP entry in their own config and the skill where they read skills. Each tool keeps that config in a different file and format. B10 said "no PATH install"; this ADR replaces that agent call for non-Claude tools.

## Options

### Option A: POSIX `install.sh` plus `sp setup <tool>`
- `install.sh` clones or updates rx4u/samepage into `~/.samepage/tool` with git, writes a shim `~/.local/bin/sp` that runs `python3 -m sp` from there, and prints the next step. No sudo, no package manager, no network call except git to github.com.
- `sp setup <tool>` for codex, cursor, copilot, gemini, windsurf and claude-desktop: adds the `samepage` MCP server to that tool's user config, copies the skill into the tool's skills folder where one is documented, and runs `sp context --tool` for the current project when it is a git repo.
- Pros: two commands per tool; idempotent; no dependency added.
- Cons: config paths change between tool versions; paths must be checked at each release.
- Price: 0 USD.

### Option B: Package managers (Homebrew, pipx, npm)
- Pros: familiar upgrades.
- Cons: a new dependency per channel (ADR-0012), a package to publish and sign, and still no tool config.
- Price: 0 USD, ongoing release work.

### Option C: Print snippets only
- Pros: never touches a user's config.
- Cons: hand-editing JSON and TOML is where setups fail.
- Price: 0 USD.

## Decision
Option A, with these rules.
- `install.sh` honours `SAMEPAGE_HOME` (default `~/.samepage`) and `SAMEPAGE_REF` (default `main`, the same channel the store template pins by sha and the README skill link uses, ADR-0016; a tag such as `v1.0.0` or a sha pins a version). Agent call (B36), to confirm with Raja after the first release: switch the default to the latest release tag then. It needs git and python3 and stops with one line naming whichever is missing. It never edits shell profiles; when `~/.local/bin` is not on PATH it prints the line to add.
- `sp setup <tool>` writes only when the config path is listed in system-design.md (Tool adapters) for the current OS. Otherwise it prints the exact snippet and the file it belongs in, and changes nothing.
- A config is changed only by adding or replacing the `samepage` entry. Before the first change to an existing file, a copy is kept at `FILE.samepage-backup` (never overwritten once it exists). JSON is parsed and written back with the file's own indent (2 when it cannot be told) and its key order; other entries keep their content and order. A JSON file that does not parse (comments, trailing commas) is not touched: the snippet is printed instead (exit 1). TOML (Codex) is edited as text: the samepage block is every line from `[mcp_servers.samepage]` through any `[mcp_servers.samepage.*]` subtable up to the next other table header; it is replaced, or appended when absent, and `env` is written as an inline table (B29).
- The verified/unverified rule (system-design.md, Tool adapters) applies to MCP configs only. Skill folders and instruction files are new files samepage owns, so they are written for every tool that has a path in the table, verified or not, and every path is printed (B33).
- The MCP entry runs `sys.executable` (the absolute python3 running setup) with `/path/to/samepage/sp_run.py mcp --tool CODE` (a launcher that imports the `sp` package next to it, so no `PYTHONPATH` is needed: Gemini CLI refuses that override, B45), and its `env` sets `PATH` to the PATH setup ran with (so git is found from GUI apps) and `SAMEPAGE_HOME` when it is set. `SAMEPAGE_HOME` moves the tool folder, the config and the default store together (B35).
- Copilot (B34): the Copilot CLI config is always written; the VS Code user `mcp.json` is written too when its User folder exists.
- Exit codes: 0 done or nothing to do (a snippet printed for an unverified path counts as done), 1 a config that does not parse or a write that failed, 2 an unknown tool name.
- `--dry-run` prints every planned change and writes nothing. Setup never prompts, never asks for or stores a token, and never deletes a file.
- `sp/setup.py` walks `skills/samepage/` in the samepage folder to copy the skill. It is a non-store folder reader and joins the ADR-0015 allow list; it never reads a store.
- There is no `sp setup chatgpt` (ADR-0019). Claude Code keeps the plugin install; `sp setup claude-code` prints the plugin command.

## Non-goals
Windows paths (scope.md), uninstall (the user deletes `~/.samepage/tool` and the `samepage` entries by hand; `sp setup TOOL --dry-run` shows where they are), auto-update.

## Consequences
- Gets easier: any coding tool reaches a working boot with `install.sh` and one `sp setup`.
- Gets harder: a path table to keep current per tool release; B10 now holds for Claude Code only.
- Follow-up tasks: WP-21.

## Implementation plan
- Affected paths: install.sh, sp_run.py, sp/setup.py, sp/__main__.py, tests/test_setup.py, scripts/guardrails.py (install.sh joins the endpoint, credential and em dash scans), docs/architecture/system-design.md.
- Pattern to follow: every path a command writes is printed before it is written.
- Pattern to avoid: editing a config the tool did not document, or one that failed to parse.
- Config and env changes: `SAMEPAGE_REF` for install.sh.

## Verification
- [ ] `sp setup cursor --dry-run` with `HOME` in a temp folder prints the planned JSON and writes nothing
- [ ] `sp setup cursor` twice gives one `samepage` entry and keeps every other server
- [ ] A config with comments is left byte for byte and the snippet is printed
- [ ] `sh install.sh` with a temp `SAMEPAGE_HOME` and `HOME` creates the shim and `sp --help` runs through it

## Revisit when
A tool's config path moves (fix the table), or 10 issues ask for a package manager.

## More information
