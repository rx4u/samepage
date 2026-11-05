# ADR-0008: Restrict AI drafting to log modes

Status: accepted
Date: 2026-11-06
Deciders: Claude (architect), agent call

## Context
Claude could summarise the store at boot ("here is what matters today"). That costs tokens every session and produces different answers on different surfaces, which defeats one shared context.

## Options

### Option A: AI drafts only when writing (log, decision, handoff); boot and recall print serve files as built
- Pros: identical boot content on every surface; summaries are confirmed by the user once; no per-session cost.
- Cons: boot content is as good as what was logged.
- Price: 0 USD extra.

### Option B: AI summary at boot
- Pros: fresher framing.
- Cons: tokens per session; drift between surfaces; unconfirmed content.
- Price: about 2,000 to 5,000 tokens per session.

## Decision
Option A.

## Non-goals
Limits on what the user asks Claude to do with the context after boot.

## Consequences
- Gets easier: consistency and cost.
- Gets harder: nothing material.
- Follow-up tasks: WP-07 skill modes.

## Implementation plan
- Affected paths: skills/samepage/SKILL.md
- Pattern to follow: draft, show, confirm, write.
- Pattern to avoid: "summarise the store" steps in boot.
- Config and env changes: none.

## Verification
- [ ] Skill boot mode has no instruction to summarise
- [ ] Boot output for the demo store is byte-identical across two runs

## Revisit when
Stores outgrow the boot budget even with caps.

## More information
