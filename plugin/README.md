# samepage plugin for Claude Code

Your AI tools forget. samepage doesn't. This plugin reads your shared working context (profile, rules,
projects, ships, decisions and handoffs) from a store you own, and adds the `/sp` commands to write to it.

## Install
```
/plugin marketplace add rx4u/samepage
/plugin install samepage@samepage
```
On Claude Code 2.1.275 or later, one step also works: `/plugin install samepage --marketplace rx4u/samepage`.
Then run `/sp init` once to create your private store.

## What it runs
- The `/sp` commands and the samepage skill. They run the bundled `sp` package with `python3` (Python
  standard library only, no installs). The plugin ships no hooks: ask "what am I working on?" or run
  `/sp boot` to load your context. The one-line installer on the website can also add a session-start
  entry to your own Claude Code settings, so context loads by itself.

## What it reads and writes
- Your store: a private GitHub repo you own, cloned on your machine (default `~/.samepage/store`), and the
  config at `~/.samepage/config`.
- Writes happen only after you confirm an entry. Each is a normal git commit pushed to your own repo with
  your own git credentials. `sp init` uses your signed-in GitHub CLI (`gh`) to create that repo.
- No server, no tokens stored, no data sent anywhere except your own git remote.

Source, tests and docs: https://github.com/rx4u/samepage. License: MIT.
