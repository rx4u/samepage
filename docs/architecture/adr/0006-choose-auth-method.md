# ADR-0006: Choose auth method

Status: accepted
Date: 2026-11-06
Deciders: Claude (architect), agent call

## Context
The store is private. Every surface needs read and write access without samepage handling credentials.

## Options

### Option A: Reuse existing auth: git credentials and `gh` in Code, claude.ai GitHub and Notion connectors elsewhere
- Pros: no secrets in samepage; revocation is the user's normal GitHub or Notion flow.
- Cons: chat write access depends on how the user installed the GitHub connector and app.
- Price: 0 USD.

### Option B: Personal access token stored in `~/.samepage/config` and pasted into chat
- Pros: works the same everywhere.
- Cons: a token in chat history and in a file; breaks the Never do list.
- Price: 0 USD, high risk.

## Decision
Option A. samepage never asks for, stores or prints a token.

## Non-goals
Team permissions.

## Consequences
- Gets easier: security review, trust.
- Gets harder: support for users whose connector lacks write access (handled by the read-only fallback in US-06).
- Follow-up tasks: README section "Connect your store" in WP-15.

## Implementation plan
- Affected paths: sp/init.py, skill references
- Pattern to follow: call `gh` and git; detect missing auth and print the exact command to fix it.
- Pattern to avoid: reading or writing any token.
- Config and env changes: none.

## Verification
- [ ] Repo-wide grep in CI finds no token-handling code paths
- [ ] `sp init` without `gh auth` prints `gh auth login` and exits 1

## Revisit when
A surface offers no connector for either backend.

## More information
