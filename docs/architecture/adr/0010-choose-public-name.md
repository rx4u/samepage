# ADR-0010: Choose the public name

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner)

## Context
The goal is stars, so the name must be findable and memorable. A GitHub search on 2026-11-06 for repos named context-os returned 446 results, including conorbronsdon/agent-context-os, which brands itself "Context OS" for a Git-backed context layer (31 stars), and Arkya-AI/claude-context-os, "a complete operating system for Claude that prevents context loss" (295 stars). Neither covers claude.ai chat natively, but searchers will find them first. Anthropic's trademark rules out names starting with "claude", and skill names cannot start with "claude".


## Options

### Option A: Keep context-os
- Pros: the owner's chosen name; says what it is.
- Cons: fifth result for its own name; easy to confuse with "Context OS" by conorbronsdon.
- Price: 0 USD; discoverability cost.

### Option B: samepage
- Pros: no GitHub repo matched "samepage claude" on 2026-11-06; the pitch writes itself ("keep every Claude on the same page"); short, works as the CLI name.
- Cons: generic English phrase; a domain may be taken.
- Price: 0 USD.

### Option C: context-os with a distinct org prefix (for example `onebillionsolo/context-os`)
- Pros: keeps the name; the org adds brand.
- Cons: search still collides on the repo name.
- Price: 0 USD.

## Decision
Option B: samepage. CLI `sp`, skill id `samepage`, plugin id `samepage`, config folder `~/.samepage/`, store repo `samepage-store`, demo repo `samepage-demo`. Chosen by the owner on 2026-11-06.

## Non-goals
Logo and visual identity.

## Consequences
- Gets easier: search, social posts, memorability.
- Gets harder: nothing material.
- Follow-up tasks: rename skill id, plugin id, CLI name and config folder in one change before WP-15.

## Implementation plan
- Affected paths: README.md, plugin.json, skills/{name}/, cos/ package name, `~/.context-os/`
- Pattern to follow: one constant `PRODUCT_NAME` in the CLI.
- Pattern to avoid: the name hard-coded in many files.
- Config and env changes: config folder follows the name.

## Verification
- [ ] GitHub repo search for the final name shows no repo over 50 stars with the same name
- [ ] Name contains no "claude" or "anthropic"

## Revisit when
Before launch only.

## More information
