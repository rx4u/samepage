# samepage store

Your shared working context for Claude and your other AI tools. Private. Edit through samepage (`/sp log`, "log this") or by hand, then run `sp check`.

## Set it up

If this store came from the template, `profile.md` still says `Your name`. Fill it in one of three ways:

- In claude.ai chat or Cowork with the samepage skill: say "set up samepage".
- In Claude Code with the plugin: `/sp init --use-existing YOUR-LOGIN/samepage-store --display-name "..." --headline "..."`.
- By hand: edit `profile.md` on GitHub and commit. The index Action rebuilds within a minute.

Keep the repo private. Full guide: https://github.com/rx4u/samepage

## Folders

- `store.md`, `profile.md`, `profile/links/`: who you are and the store's schema version.
- `projects/`, `events/`, `decisions/`, `design/`, `handoffs/`, `rules/`, `tags/`: your entries, one Markdown file each.
- `index/`: the serve layer that Claude reads at boot. Built by `sp index`. Never edit it by hand.

## The index Action

`.github/workflows/index.yml` runs on every push to the default branch that changes anything outside `index/`. It runs `sp check`, then `sp index`, then commits only `index/` as `index: rebuild {sha8}`. A chat or Cowork write shows up in `index/boot/chat.md` about a minute later.

- When `sp check` fails, the job fails, GitHub emails you, and nothing is committed: the previous index stays. Fix the file named in the job log and push again.
- The Action skips its own commits, so it never loops.
- The store ships without branch protection. If you add protection to the default branch, it must allow GitHub Actions to push, or the index will not rebuild.
- Keep this repo private. Secrets never go in a store; `sp check` blocks them.
