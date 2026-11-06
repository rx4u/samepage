# ADR-0016: Adopt a one-click store and guided setup

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner), Claude (architect)

## Context
A stranger who finds the repo hits four frictions before samepage works:
1. A store can only be created from Claude Code with the GitHub CLI signed in, so a user of claude.ai chat or Cowork alone cannot start.
2. The store Action checks out the tool at tag `v1.0.0`. Until a release exists, every new store fails its index run.
3. The claude.ai skill file is only downloadable from a release.
4. Chat needs a "samepage store" line in the user's preferences before it can read anything.

## Options

### Option A: Public template repo, sha pin, skill file in the repo, guided first run
- A public GitHub template repo `rx4u/samepage-store-template` holds a valid placeholder store with a built index and the index Action. "Use this template" creates a private store with no CLI, no Python and no Claude Code.
- The Action pins the tool by commit sha, so no tag is needed.
- `dist/samepage.skill` is committed, built reproducibly, and a test keeps it equal to the skill source.
- The skill's setup mode guesses `LOGIN/samepage-store` from the connector's own user when no store line exists, fills a placeholder profile, and tests one write.
- Pros: every surface can start setup alone; nothing waits on a release; one less step in chat.
- Cons: one more public repo to keep in sync with `store-template/`; the skill file is a binary in git (about 25 KB).
- Price: 0 USD.

### Option B: Keep Claude Code as the only way to create a store
- Pros: no change.
- Cons: chat-only users cannot start, which is most claude.ai users.
- Price: 0 USD.

## Decision
Option A. Writes from chat still need the claude.ai GitHub connector's app on the user's account (A2); that stays one guided step because it is a GitHub permission samepage cannot grant.

## Non-goals
A hosted setup page, OAuth, or any token handling (ADR-0006 stands). Windows support for the Claude Code hooks.

## Consequences
- Gets easier: setup from chat alone; stores work before and after releases; claude.ai install is one download.
- Gets harder: `store-template/` changes must be copied to the template repo (`scripts/make_template_repo.py` builds it).
- Follow-up tasks: none (template flag set 2026-11-06).

## Implementation plan
- Affected paths: scripts/make_template_repo.py, scripts/package_skill.py, dist/samepage.skill, store-template/.github/workflows/index.yml, sp/init.py, skills/samepage/SKILL.md, skills/samepage/references/setup.md, README.md, .github/workflows/release.yml, tests.
- Pattern to follow: the placeholder profile is recognised by `display_name: Your name`; setup replaces it.
- Pattern to avoid: a store that fails `sp check`, including the template.
- Config and env changes: none.

## Verification
- [x] A repo created from the template passes `sp check` and its Action rebuilds the index on the first edit
- [x] `sp init` without the GitHub CLI prints the template link instead of failing
- [x] `sp init --use-existing OWNER/REPO` works with plain git and fills a placeholder profile
- [x] `dist/samepage.skill` matches `skills/samepage/` (test)

## Revisit when
Claude Code or claude.ai can create a repo for the user without a CLI, or the connector can write without an app install.

## More information
- 2026-11-06: asked for by Raja after a walkthrough of what a stranger does after finding the repo.
- 2026-11-06: verified on real GitHub. A private repo made from the template link ran its index Action on the first commit; `sp init --use-existing` with no GitHub CLI cloned it with plain git, filled the profile, pushed, and the Action rebuilt the index in under a minute.
