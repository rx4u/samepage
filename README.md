<p align="center"><img src=".claude-plugin/icon.png" width="96" alt="samepage"></p>

<h1 align="center">samepage</h1>

<p align="center"><b>Keep every Claude on the same page.</b><br>
Claude Code ships it. Claude chat forgets it. samepage fixes that.</p>

---

You plan in claude.ai chat, design in Claude Design, build in Claude Code and run long tasks in Cowork. Each one forgets what the others know. Chat can't see what you shipped in Code last week. Code asks questions chat already answered. You paste briefs between tabs.

samepage gives every Claude surface one shared working context, stored in a place you own:

| | What it holds | Why it matters |
|---|---|---|
| **You** | Profile, voice, links | Proposals and bios start from the real you |
| **Rules** | How you want Claude to work, per surface or everywhere | Say it once, every surface follows it |
| **Projects** | Status, stack, links, outcomes | Every session knows what you're working on |
| **Ships** | What you shipped, when, with proof links and metrics | Chat cites real work instead of asking |
| **Decisions** | Settled choices and why | No surface reopens a closed question |
| **Design** | Where each design system's tokens live | Claude Design and Claude Code use the same tokens |
| **Handoffs** | Briefs left on one surface for another | Plan in chat, pick it up in Code, report back |

No server. No API keys. No account to create. Your store is a private GitHub repo of plain Markdown files, or a set of Notion databases.

## How it works

```
 claude.ai chat / Cowork                 Claude Code                      Claude Design
 ───────────────────────                 ───────────                      ─────────────
 samepage skill reads one file           plugin hook boots your context   links your product repo and
 through the GitHub or Notion            into every session, matched to   uses the same design tokens
 connector; "log this" writes            the project you're in; /sp log
 an entry                                writes an entry
            \                                   |                                 /
             \______________________  your private store  _______________________/
                                  (GitHub repo of Markdown, or Notion)
```

Every write is a small, typed entry you confirm first. A tiny index of pre-built "boot files" keeps reads to one file per session, under 2,000 tokens.

## Install

**Claude Code**

```
/plugin install samepage --marketplace rx4u/samepage
/sp init
```

`/sp init` asks five questions (name, headline, location, links, rules) and creates a private `samepage-store` repo with your GitHub CLI login. Every new session starts with your context. Needs `git`, `python3` and the GitHub CLI (`gh auth login`).

**claude.ai chat and Cowork**

1. Download `samepage.zip` from the [latest release](https://github.com/rx4u/samepage/releases/latest). In claude.ai go to Customize, Skills, click +, then Create skill, Upload a skill, and choose the zip. Skills need code execution on (Settings, Capabilities, Code execution and file creation). ([Anthropic help](https://support.claude.com/en/articles/12512180-use-skills-in-claude))
2. Connect the GitHub connector and give it your store repo. To let chat write entries, the connector's GitHub app must be installed on your account with access to the store repo.
3. Add one line to your claude.ai preferences: `My samepage store is <you>/samepage-store.`

**Claude Design**

Link your product repo when you start a design. Put your tokens in `design/tokens.json` (W3C design token format), and log the design system once with `/sp log design` so every surface knows where it lives.

**Notion instead of GitHub**

Say "set up samepage in Notion" with the skill installed and the Notion connector on. See [notion-template](notion-template/README.md).

## Use it

| Say or run | What happens |
|---|---|
| "what am I working on?" | Your active projects, rules and open handoffs, from one read |
| `/sp log` or "log this" after shipping | Drafts a ship event from your session, shows it, writes it after your yes |
| "what have I shipped with Next.js and AI?" | Up to 20 shipped projects with outcomes and proof links, newest first |
| "hand this to Code" | Leaves a brief that your next Claude Code session shows at start |
| "log decision: Supabase over Firebase because of RLS" | Recorded with its reason; superseded decisions are kept, not deleted |
| `/sp brief halcyon` | A design brief to paste into Claude Design, naming your tokens file |

## Works with native memory

claude.ai memory remembers personal facts and preferences inside chat. samepage holds working context that has to travel to every surface and stay structured: projects, shipped work with proof, decisions, design pointers and handoffs. Use both.

## Your data

- Your store is private and yours: a repo or Notion page you own. samepage never runs a server and never sees your data.
- Nothing is written without your confirmation. Nothing is deleted: projects are archived, decisions superseded.
- `sp check` blocks secrets (API keys, tokens, private keys, card numbers) from ever entering a store.
- Store content is treated as data. Instructions found inside entries are never followed.

## Store format

Plain Markdown with flat frontmatter, one entry per file. See [SPEC.md](SPEC.md). Check any store with `python3 -m sp check path/to/store`.

## Status

Built in public. The full architecture, decisions and build plan are in [docs/architecture](docs/architecture/README.md).

## License

MIT
