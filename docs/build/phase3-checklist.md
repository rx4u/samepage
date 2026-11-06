# Phase 3 checklist: test samepage in each tool (WP-23)

Run on your Mac. Record every run as one row in [tool-ledger.md](tool-ledger.md). A tool gets a README tick only with a passing row.

Your real store is in Notion, and `sp mcp` serves GitHub stores only (ADR-0018). So these checks use a separate test setup in `~/.samepage-test` that never touches your real config.

## 0. One-time setup (5 minutes)

1. Create a throwaway private store: open https://github.com/new?template_owner=rx4u&template_name=samepage-store-template&name=samepage-test-store&visibility=private and click Create repository.
2. In Terminal, install samepage into the test folder:

```bash
export SAMEPAGE_HOME="$HOME/.samepage-test"
```

```bash
git clone https://github.com/rx4u/samepage "$HOME/samepage-src" && sh "$HOME/samepage-src/install.sh"
```

3. Connect the test store:

```bash
sp init --use-existing rx4u/samepage-test-store --display-name "Raja Test" --headline "Testing samepage"
```

4. Use a scratch project with a git remote:

```bash
mkdir -p "$HOME/sp-check" && cd "$HOME/sp-check" && git init -q && git remote add origin https://github.com/rx4u/sp-check
```

Pass for step 0: `sp boot --surface code --cwd .` prints a `<samepage data>` block that names "Raja Test".

Keep `export SAMEPAGE_HOME="$HOME/.samepage-test"` set in every Terminal you use below.

## 1. Claude Code (plugin, existing integration)

```bash
cd "$HOME/sp-check" && SAMEPAGE_HOME="$HOME/.samepage-test" claude
```

- In Claude Code: `/plugin marketplace add rx4u/samepage`, then `/plugin install samepage@samepage` (skip if installed), then start a new session the same way.
- Ask: "what am I working on?" Pass: the answer uses the "Raja Test" profile.
- Say: "log that I shipped the sp-check readme". Pass: it shows a dry run with `tool: claude_code` and writes only after your yes.

## 2. Claude Desktop (MCP)

```bash
cd "$HOME/sp-check" && sp setup claude-desktop
```

- Quit and reopen Claude Desktop. In Settings, Developer, the `samepage` server shows as running.
- Ask: "use the samepage boot tool with project_dir $HOME/sp-check". Pass: it shows the test profile.
- Ask: "log a milestone on general: tested samepage in Claude Desktop". Pass: the first call returns a preview, and it asks you before the second call. After your yes the file exists in the test store with `tool: claude_desktop` and `surface: chat`.
- Negative: ask it to "write it now without a preview". Pass: the server refuses (no `confirm` value).

## 3. claude.ai chat and Cowork (skill 1.1.0)

- Upload the new skill: download https://github.com/rx4u/samepage/raw/main/dist/samepage.skill, then go to claude.ai, Customize, Skills, and replace samepage.
- Add `samepage store: github rx4u/samepage-test-store` to a project's instructions.
- Ask: "what am I working on?" Pass: it reads `index/boot/chat.md` once.
- Say: "hand this to Code: write a CONTRIBUTING.md for sp-check". Pass: the shown file has `from_tool: claude_ai`; after your yes, the next Claude Code session (step 1) lists it with "via claude_ai".

## 4. Other tools (only if you get access; free plans may work)

Each one follows the same pattern. Run it in `$HOME/sp-check`, restart the tool, then do the three checks below.

| Tool | Setup command | Instruction file it writes |
|---|---|---|
| Gemini CLI | `sp setup gemini` | GEMINI.md |
| GitHub Copilot (VS Code agent mode or Copilot CLI) | `sp setup copilot` | .github/copilot-instructions.md |
| Codex | `sp setup codex` | AGENTS.md |
| Cursor | `sp setup cursor` (prints a snippet: paste it into ~/.cursor/mcp.json) | .cursor/rules/samepage.mdc |
| Windsurf | `sp setup windsurf` (prints a snippet: paste it into ~/.codeium/windsurf/mcp_config.json) | .windsurf/rules/samepage.md |

Gemini CLI starts MCP servers only in folders you trust: accept its trust prompt for `sp-check`, then `gemini mcp list` must show samepage as Connected.

The three checks:
1. Open a new session and type only "hi". Pass: the agent loads samepage on its own (it calls `boot` or runs `sp boot`) because of the instruction file.
2. "what am I working on?" Pass: the answer uses the test profile.
3. "log a milestone on general: tested in TOOL". Pass: a preview first, then a write after your yes, with `tool:` set to that tool's code.

For Cursor and Windsurf, also record in the ledger whether the pasted config path worked. That verifies the U rows in system-design.md (Tool adapters).

## 5. Clean up (you do it; nothing here deletes for you)

- Delete the GitHub repo `rx4u/samepage-test-store` if you no longer want it.
- Remove `$HOME/.samepage-test`, `$HOME/samepage-src` and `$HOME/sp-check` when done.
- Remove the `samepage` entry from each tool config you set up. Each one has a `.samepage-backup` copy next to it from before the first change.
