# samepage plugin for Claude Code

Your AI tools forget. samepage doesn't. This plugin loads your shared working context (profile, rules,
projects, ships, decisions and handoffs) at the start of every Claude Code session, from a store you own,
and adds the `/sp` commands to write to it.

## Install
```
/plugin marketplace add rx4u/samepage
/plugin install samepage@samepage
```
On Claude Code 2.1.275 or later, one step also works: `/plugin install samepage --marketplace rx4u/samepage`.
Then run `/sp init` once to create your private store.

## What it runs
- A SessionStart hook (`hooks/session-start.sh`) that runs `python3 -m sp boot` from this folder and prints
  your context. It reads your local store clone and runs `git pull` on it with a 2 second limit.
- A Stop hook (`hooks/stop-nudge.sh`) that prints a one-line reminder to log what you shipped.
- The `/sp` commands, which run the same `sp` package (Python standard library only, no installs).

## What it reads and writes
- Your store: a private GitHub repo you own, cloned on your machine (default `~/.samepage/store`), and the
  config at `~/.samepage/config`.
- Writes happen only after you confirm an entry. Each is a normal git commit pushed to your own repo with
  your own git credentials. `sp init` uses your signed-in GitHub CLI (`gh`) to create that repo.
- No server, no tokens stored, no data sent anywhere except your own git remote.

Source, tests and docs: https://github.com/rx4u/samepage. License: MIT.
