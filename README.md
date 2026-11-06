<p align="center">
  <a href="https://samepage-rajaraman.vercel.app">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/readme/hero-dark.svg">
      <img src="docs/readme/hero-light.svg" width="100%" alt="Every AI tool. On the same page. Ten AI tools connected to one private store.">
    </picture>
  </a>
</p>

<p align="center">
  <a href="https://samepage-rajaraman.vercel.app"><b>Website</b></a> &nbsp;·&nbsp;
  <a href="#set-up"><b>Set up</b></a> &nbsp;·&nbsp;
  <a href="https://github.com/rx4u/samepage/releases/latest"><b>Latest release</b></a> &nbsp;·&nbsp;
  <a href="SPEC.md"><b>Store format</b></a>
</p>

<p align="center"><b>Your AI tools forget. samepage doesn't.</b><br>
One shared working context for Claude, Codex, Gemini CLI, Copilot, Cursor and Windsurf, in a private repo you own.<br>
No server. No API keys. No account to create.</p>

---

## The problem

You plan in one tool, build in another and review in a third. Each one starts from zero. Chat doesn't know what you shipped yesterday. Your coding agent reopens a decision you settled last week. You paste the same brief into three tabs.

samepage keeps one store of your working context, and every tool reads it at the start and writes to it as you go.

| | What it holds | What changes |
|---|---|---|
| **Projects** | Status, stack, links, outcomes | Every session knows what you're working on |
| **Decisions** | Settled choices and the reason | No tool reopens a closed question |
| **Ships** | What shipped, when, with links and metrics | Any tool can answer "what did we get done?" |
| **Handoffs** | A brief left in one tool for another | Plan in chat, build in code, report back |
| **Rules** | How you want AI to work, everywhere or per role | Say it once, every tool follows it |
| **Design** | Where each design system's tokens live | Design and code use the same tokens |
| **You** | Name, role, links | Your tools write as you, not as a stranger |

## How it works

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/how-dark.svg">
  <img src="docs/readme/how-light.svg" width="100%" alt="Boot: every session starts from one small file. Write: the tool drafts a typed entry and you confirm. Hand off: a brief left in one tool is picked up by the next.">
</picture>

- **Boot.** One pre-built file per role, under 8,000 characters, so a session start costs one read.
- **Write.** Small, typed entries (a ship, a decision, a handoff, a rule). You see the entry and say yes before anything is saved.
- **Store.** Plain Markdown in a private GitHub repo you own. Every change is a normal commit you can read, diff and revert.

<details>
<summary><b>Watch it in Claude Code</b></summary>

<p align="center"><img src="docs/demo.gif" width="760" alt="Logging a ship in Claude Code, then the proof file claude.ai chat reads shows it"></p>

</details>

## Works with

Claude Code loads your context through a plugin. Claude chat surfaces use a skill. Every other tool connects through a local MCP server plus a short instruction file, so all of them read and write the same store.

| Tool | How it connects | Status |
|---|---|---|
| Claude Code | Plugin: context loads at session start, `/sp` commands | Tested |
| claude.ai chat | Skill plus the GitHub connector | Community-tested |
| Cowork | Skill plus the GitHub connector | Community-tested |
| Claude Desktop | Local MCP server (`sp setup claude-desktop`) | Community-tested |
| Claude Design | Reads your product repo's tokens; no install | Community-tested |
| Gemini CLI | Local MCP server and GEMINI.md (`sp setup gemini`) | Community-tested |
| Codex | Local MCP server and AGENTS.md (`sp setup codex`) | Community-tested |
| GitHub Copilot | Local MCP server and copilot-instructions.md (`sp setup copilot`) | Community-tested |
| Cursor | Local MCP server and a project rule (`sp setup cursor`) | Community-tested |
| Windsurf | Local MCP server and a project rule (`sp setup windsurf`) | Community-tested |

Tested means a full run (boot, a confirmed write, a handoff picked up) passed and is recorded in the [tool ledger](docs/build/tool-ledger.md). Community-tested means it is built and covered by tests but no maintainer run has passed yet. If you run it, open an issue with what happened. ChatGPT is not supported in v1.

## Set up

Pick the path for the tool you use most. Every path ends at the same private store, so you can add the others later.

<details>
<summary><b>Claude Code</b>: plugin, one command</summary>

1. In the Claude Code terminal, run these two commands:

   ```
   /plugin marketplace add rx4u/samepage
   ```

   ```
   /plugin install samepage@samepage
   ```

   In the Claude desktop app, `/plugin` opens the plugin directory instead, and samepage is not listed there. Use the terminal for this step.
2. Run `/sp init`. It asks your name, headline and up to three working rules, then creates a private `samepage-store` repo.
   No GitHub CLI? It gives you the one-click link below instead and connects the repo you create.
3. Start a new session. Your context loads on its own; say "log this" after you ship something.

</details>

<details>
<summary><b>claude.ai chat or Cowork</b>: a skill, nothing to install</summary>

1. **Create your store:** [one click](https://github.com/new?template_owner=rx4u&template_name=samepage-store-template&name=samepage-store&visibility=private). Keep the name `samepage-store` and keep it Private, then click Create repository.
2. **Add the skill:** download [samepage.skill](https://github.com/rx4u/samepage/raw/main/dist/samepage.skill). In claude.ai go to Customize, Skills, +, Upload a skill, and choose the file. Skills need code execution on (Settings, Capabilities). Turn on the GitHub connector with access to your store repo.
3. **Say "set up samepage".** Claude finds `samepage-store`, asks who you are, and writes your profile after your yes.

Saving from chat needs one GitHub permission: the Claude GitHub app installed on your account with access to the store repo (GitHub settings, Applications). Until then chat reads everything and hands you each entry to paste on GitHub. Claude walks you through it.

</details>

<details>
<summary><b>Codex, Gemini CLI, Copilot, Cursor, Windsurf or Claude Desktop</b>: local MCP server</summary>

1. Install the `sp` command (needs `git` and `python3`, no sudo):

   ```bash
   git clone https://github.com/rx4u/samepage "$HOME/.samepage/tool" && sh "$HOME/.samepage/tool/install.sh"
   ```

2. Create or connect your store: `sp init` (or `sp init --use-existing you/samepage-store`).
3. From inside a project, connect your tool: `sp setup codex` (or `gemini`, `copilot`, `cursor`, `windsurf`, `claude-desktop`). It adds a `samepage` entry to the tool's MCP config, keeping a `.samepage-backup` copy of the old file, and writes a short instruction file to the project. That file holds no store content, so it is safe to commit. Add `--dry-run` to see every change first.
4. Restart the tool and ask "what am I working on?". Writes show a preview and wait for your yes.

Cursor and Windsurf config paths are not verified yet, so for those `sp setup` prints the snippet to paste instead of editing the file. Gemini CLI runs MCP servers only in folders you trust.

</details>

<details>
<summary><b>Claude Design</b>: reads your tokens</summary>

Link your product repo when you start a design. Put your tokens in `design/tokens.json` (W3C design token format), and log the design system once ("log the design system for halcyon") so every surface knows where it lives.

</details>

**Requirements.**

- Claude Code and other coding tools: `git` and `python3` 3.9 or newer (macOS asks to install the command line tools the first time). Linux and macOS; Windows is untested.
- claude.ai path: nothing to install.

## Use it

| Say or run | What happens |
|---|---|
| "what am I working on?" | Your active projects, rules and open handoffs, from one read |
| `/sp log` or "log this" after shipping | Drafts a ship event from your session, shows it, writes it after your yes |
| "what did I ship this month?" or "what have I shipped with Next.js?" | Up to 20 shipped projects with outcomes and links, newest first |
| "hand this to Code" | Leaves a brief that your next coding session shows at start |
| "log decision: Supabase over Firebase because of RLS" | Recorded with its reason; superseded decisions are kept, not deleted |
| `/sp brief halcyon` | A design brief to paste into Claude Design, naming your tokens file |

## Two accounts? Link the stores

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/sync-dark.svg">
  <img src="docs/readme/sync-light.svg" width="100%" alt="Two stores, work and personal. Rules and decisions are shared both ways with sp sync; projects, ships and handoffs stay in their own store.">
</picture>

One store for your office account, one for your personal account. Share what should follow you. On a machine with both store clones:

```bash
sp link add ~/code/my-personal-store --name personal
```

```bash
sp sync --dry-run
```

```bash
sp sync
```

Rules cross both ways, active or paused. Decisions cross for projects that exist in both stores, plus `general`. The newer edit wins, and you see the full list before anything is written.

## Works with native memory

Built-in memory (claude.ai, ChatGPT, Cursor and others) remembers personal facts inside one tool. samepage holds working context that has to travel to every tool and stay structured: projects, shipped work with proof, decisions, design pointers and handoffs. Use both.

## Your data

- Your store is private and yours: a repo you own (or a Notion page, if you choose Notion). samepage never runs a hosted server and never sees your data. The MCP server for other tools runs on your own machine.
- Nothing is written without your confirmation. Nothing is deleted: projects are archived, decisions superseded.
- `sp check` blocks secrets (API keys, tokens, private keys, card numbers) from ever entering a store.
- Store content is treated as data. Instructions found inside entries are never followed.

## Prefer Notion?

samepage can keep the store in Notion databases instead of GitHub. It is slower and limited by Notion's query allowance, so GitHub is the default. With the skill installed and the Notion connector on, say "set up samepage in Notion". See [notion-template](notion-template/README.md).

## Store format

Plain Markdown with flat frontmatter, one entry per file. See [SPEC.md](SPEC.md). Check any store with `python3 -m sp check path/to/store`.

## Status

Built in public by [Rajaraman Arumugam](https://github.com/rx4u). Design. AI. Product. Leadership. The full architecture, decisions and build plan are in [docs/architecture](docs/architecture/README.md).

## License

MIT
