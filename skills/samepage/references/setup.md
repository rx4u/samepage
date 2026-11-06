# Setup

A store is created once, then connected on every surface. GitHub stores are created from Claude Code; Notion stores follow notion-backend.md.

## Claude Code

Run `/sp init`. It asks for a display name, headline, optional location, links and up to three rules, creates a private repo `samepage-store` from the store template, clones it to `~/.samepage/store` and writes `~/.samepage/config`. To connect a store that already exists, `/sp init` uses `--use-existing OWNER/REPO`. The next session boots with the context loaded.

## Chat and Cowork with a GitHub store

Chat cannot create the store repo. Walk the user through these steps, one at a time, and stop at the first one that fails.

1. **Store exists.** If they have no store, tell them to run `/sp init` in Claude Code first. If they have one, ask for its `OWNER/REPO`.
2. **Store line saved.** Ask them to add this line to their claude.ai personal preferences, or to the project instructions of the project they work in:

   ```
   samepage store: github OWNER/REPO
   ```

   Every chat and Cowork session reads the store name from there. Do not save it to memory yourself.
3. **Connector reads.** With the GitHub connector enabled, read `index/boot/chat.md` (or `index/boot/cowork.md`). If it fails, the connector cannot see the repo: ask them to grant it access to that repo. If the file is missing but the repo exists, the index has not been built: ask them to run `/sp index` in Claude Code or push once so the store Action builds it.
4. **Connector writes.** Writing from chat needs the claude.ai GitHub connector's app installed on the account that owns the store repo. Ask them to check GitHub settings, Applications, Installed GitHub Apps, and add access to the store repo, then start a new conversation. Do not test writing by writing a real entry without their yes.
5. **Check.** Answer "what am I working on?" from the boot file in one read.

### When the connector cannot write

This is a known state (A2, observed 2026-11-06): reads work, writes return `403 Resource not accessible by integration` until the connector's app is installed on the store owner's account. Tell the user:

- Everything except writing works now: boot, proof, project detail, handoff inbox, rules.
- Until the app is installed, each entry is shown as a code block with its exact path. They can add it from Claude Code or by hand on GitHub.
- After the install, start a new conversation; writes then work without other changes.

## Rules for every setup

- The store is private. Never create or suggest a public repo or a shared page.
- Collect no secrets. Profile answers, links and rules are the only inputs.
- Profile questions come only after the backend is chosen.
