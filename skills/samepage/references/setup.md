# Setup

A store is created once, then connected on every surface. Walk the user through one step at a time and stop at the first step that fails. Notion stores follow notion-backend.md instead.

The one-click template: `https://github.com/new?template_owner=rx4u&template_name=samepage-store-template&name=samepage-store&visibility=private`

## Claude Code

- GitHub CLI signed in (`gh auth status` succeeds): run `/sp init` with the user's display name, headline, optional location, links and up to three rules. It creates the private repo `samepage-store`, clones it to `~/.samepage/store` and writes `~/.samepage/config`.
- No GitHub CLI: `/sp init` prints the template link. Ask the user to open it and click Create repository (keep it Private), then run `/sp init --use-existing LOGIN/samepage-store --display-name "..." --headline "..."`. It clones with plain git and fills in the template's placeholder profile.
- Store already exists: `/sp init --use-existing OWNER/REPO`.

The next session boots with the context loaded.

## Chat and Cowork with a GitHub store

1. **Find the store.**
   - A line such as `samepage store: github OWNER/REPO` in the user's preferences or project instructions names it.
   - With no line, ask the GitHub connector for the signed-in user's login if it offers that, and try `LOGIN/samepage-store` by reading its `store.md`.
   - Otherwise ask the user for `OWNER/REPO`.
2. **No store yet.** Give the template link above. Tell them: click Create repository, keep the name `samepage-store` and keep it Private. If the GitHub connector only sees selected repositories, they add the new repo to it. Then continue at step 3.
3. **Read.** Read `index/boot/chat.md` (or `index/boot/cowork.md`).
   - Read fails: the connector cannot see the repo. Ask them to give it access to that repo.
   - File missing but the repo exists: the index is not built yet. Ask them to edit any file on GitHub and commit, so the store Action builds it, or run `/sp index` in Claude Code.
4. **Fill in the profile.** If the profile says `Your name`, the store is fresh from the template. Ask for display name, headline, optional location, up to three links and up to three working rules. Build `profile.md` and one file per link and rule per entry-schema.md, show them with their paths, and write after a yes (store `owner_handle` becomes the repo owner).
5. **Write access.** The first confirmed write in step 4 is the write test. If it returns 403 (A2), see below. Never write a test entry the user did not ask for.
6. **Store line.** Only when the repo is not `LOGIN/samepage-store`: ask them to add `samepage store: github OWNER/REPO` to their claude.ai preferences or project instructions. Do not save it to memory yourself.
7. **Check.** Answer "what am I working on?" from the boot file in one read.

### When the connector cannot write

Known state (A2, observed 2026-11-06): reads work, writes return `403 Resource not accessible by integration` until the claude.ai GitHub connector's app is installed on the account that owns the store. Tell the user:

- Everything except writing works now: boot, proof, project detail, handoff inbox, rules.
- To turn on writes: GitHub settings, Applications, Installed GitHub Apps, then give the Claude app access to the store repo, then start a new conversation.
- Until then, show each entry as a code block with its exact path and the edit link `https://github.com/OWNER/REPO/edit/main/PATH` (or `/new/main/FOLDER` for a new file), so they can paste it on GitHub. The store Action rebuilds the index after their commit.

## Rules for every setup

- The store is private. Never create or suggest a public repo or a shared page.
- Collect no secrets. Profile answers, links and rules are the only inputs.
- Profile questions come only after the backend is chosen.
