# samepage plugin for Claude Code

Your AI tools forget. samepage doesn't. This plugin reads your shared working context (profile, rules, projects, ships, decisions and handoffs) from a store you own, and adds the `/sp` commands to write to it.

## Install
```
/plugin marketplace add rx4u/samepage
/plugin install samepage@samepage
```
On Claude Code 2.1.275 or later, one step also works: `/plugin install samepage --marketplace rx4u/samepage`.
Then run samepage's one-line install once (see the repo's Set up section). It installs the `sp` command these skills call, creates your private store and connects your other AI tools.

## What it runs
- Nothing of its own. The plugin is two skills in Markdown: `samepage` (Claude uses it when you ask about your work) and `sp` (the `/sp` command). Both call the `sp` command that samepage's one-line install puts in `~/.local/bin` (Python standard library only). Without it, the skills say how to install it and stop. The plugin never downloads or runs the installer.
- No hooks and no MCP servers. Ask "what am I working on?" or run `/sp boot` to load your context. The one-line install can also add a session-start entry to your own Claude Code settings.

## What it reads and writes
- Your store: a private GitHub repo you own, cloned on your machine (default `~/.samepage/store`), and the config at `~/.samepage/config`.
- Writes happen only after you confirm an entry. Each is a normal git commit pushed to your own repo with your own git credentials.
- No server, no tokens stored, no data sent anywhere except your own git remote.

Source, tests and docs: https://github.com/rx4u/samepage. License: MIT.
