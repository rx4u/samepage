# ADR-0013: Choose where the public repo lives

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner)

## Context
Stars accrue to a repo, and attribution accrues to its owner. The owner's GitHub account is `rx4u`. The owner also runs a solo-founder brand. Moving a repo later keeps stars but breaks install commands that include the owner name.


## Options

### Option A: Personal account `rx4u`
- Pros: stars and followers build the owner's own profile, which links to the portfolio; no new account.
- Cons: the handle does not carry the brand name.
- Price: 0 USD.

### Option B: A new organisation for the solo-founder brand
- Pros: brand in every install command; room for future open-source repos under one roof.
- Cons: a new org starts with no followers; the owner's profile shows the repo only as a contribution.
- Price: 0 USD.

## Decision
Option A: `github.com/rx4u/samepage`, so attention lands on the owner's profile and portfolio link. Chosen by the owner on 2026-11-06.

## Non-goals
The name (ADR-0010).

## Consequences
- Gets easier: one place to build reputation.
- Gets harder: nothing material.
- Follow-up tasks: plugin marketplace id and README install lines use the chosen owner.

## Implementation plan
- Affected paths: README.md, plugin/.claude-plugin/marketplace.json
- Pattern to follow: owner name in one place in the release script.
- Pattern to avoid: hard-coded owner in docs.
- Config and env changes: none.

## Verification
- [ ] `/plugin marketplace add {owner}/{repo}` works from a clean Claude Code install

## Revisit when
Before launch only.

## More information
