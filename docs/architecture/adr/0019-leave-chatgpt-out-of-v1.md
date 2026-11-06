# ADR-0019: Leave ChatGPT out of v1

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner)

## Context
The plan proposed ChatGPT as a read-only reader of `index/boot/chat.md` through its GitHub connector. ChatGPT accepts only remote HTTPS MCP servers, so ChatGPT writes would need a hosted server, which ADR-0001 rules out. Raja has no ChatGPT login to test with (ADR-0017 context).

## Options

### Option A: Read-only through ChatGPT's GitHub connector
- Pros: ChatGPT users get boot and proof reads with no server.
- Cons: untestable before launch; a half-working tool in the pitch; connector availability depends on the ChatGPT plan.
- Price: 0 USD, about 1 day of docs and setup work.

### Option B: Hosted HTTPS MCP server for ChatGPT
- Pros: full read and write.
- Cons: breaks the no-server and no-credentials promises (ADR-0001, ADR-0006).
- Price: 5 to 25 USD per month plus auth work. Rejected.

### Option C: Leave ChatGPT out of v1
- Pros: the launch claims only what works; no ChatGPT-specific code or docs to keep.
- Cons: ChatGPT users are not served at launch.
- Price: 0 USD.

## Decision
Option C, chosen by Raja on 2026-11-06. No `chatgpt` tool code, no `sp setup chatgpt`, no ChatGPT row in the README tool table. A user can still paste a boot file into any chat tool by hand; samepage does not document or support that path.

## Non-goals
Any hosted component.

## Consequences
- Gets easier: scope and launch copy.
- Gets harder: nothing material.
- Follow-up tasks: none.

## Implementation plan
- Affected paths: docs/build/everyone-plan.md (note), scope.md (cut list), ADR-0017 lookup list.
- Pattern to follow: a tool enters the README only with a working adapter.
- Pattern to avoid: claiming ChatGPT support.
- Config and env changes: none.

## Verification
- [ ] `grep -ri chatgpt sp/ skills/ commands/ hooks/` finds nothing
- [ ] `sp setup chatgpt` exits 2 with the list of supported tools

## Revisit when
ChatGPT supports local stdio MCP servers or reads a GitHub repo through its connector on the free plan, and 10 issues ask for it.

## More information
