# ADR-0012: Choose a Python standard library CLI

Status: accepted
Date: 2026-11-06
Deciders: Claude (architect), agent call

## Context
The hook, index job and validator need a small program. It must run on the user's machine without an install step and in GitHub Actions.

## Options

### Option A: Python 3.9+ standard library only
- Pros: python3 is present wherever git came from Xcode Command Line Tools (macOS) and on Linux and GitHub runners; no dependencies.
- Cons: no YAML library, hence the flat frontmatter rule (ADR-0003); Windows needs Python installed.
- Price: 0 USD.

### Option B: Node.js script
- Pros: familiar to web developers.
- Cons: Claude Code's native installer does not require Node, so Node is not guaranteed; a YAML package would add a dependency.
- Price: 0 USD.

### Option C: Compiled Go binary
- Pros: no runtime needed.
- Cons: per-OS builds and signing; contributors need Go.
- Price: 0 USD, more release work.

## Decision
Option A. ASSUMPTION: python3 is available on target machines (A6). The skill can still log and recall without `sp` by writing files directly; `sp` only makes it faster and adds the index rebuild.

## Non-goals
Windows-native support in v1 (scope.md).

## Consequences
- Gets easier: zero install, easy contributions.
- Gets harder: Windows users need Python and a POSIX shell for hooks.
- Follow-up tasks: WP-02.

## Implementation plan
- Affected paths: sp/
- Pattern to follow: one module per command; `python3 -m sp {command}`.
- Pattern to avoid: any import outside the standard library.
- Config and env changes: none.

## Verification
- [ ] CI runs on Python 3.9 and 3.13
- [ ] CI fails on any non-stdlib import

## Revisit when
10 Windows issues, or python3 found missing on a supported setup.

## More information
