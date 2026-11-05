# ADR-0014: Package one skill with modes

Status: accepted
Date: 2026-11-06
Deciders: Raja (owner)

## Context
Reading and writing the store could be separate skills. The goal is adoption; every extra install step loses users.

## Options

### Option A: One skill, `samepage`, with modes: setup, boot, log, proof, handoff, decision, design, project, rules
- Pros: one upload in claude.ai, one plugin skill in Code; one description to trigger.
- Cons: a longer description; mode routing must be crisp.
- Price: 0 USD.

### Option B: Two skills, capture and recall
- Pros: tighter triggers per skill.
- Cons: two uploads; users install one and wonder why the other half is missing.
- Price: 0 USD.

## Decision
Option A, chosen by the owner on 2026-11-06. SKILL.md stays under 500 lines; backend and mode details live in references/ (progressive disclosure).

## Non-goals
The skill's exact wording (WP-07).

## Consequences
- Gets easier: install and demo.
- Gets harder: trigger testing covers more phrases.
- Follow-up tasks: WP-07 trigger tests for each mode.

## Implementation plan
- Affected paths: skills/samepage/
- Pattern to follow: a mode table at the top of SKILL.md mapping phrases to modes.
- Pattern to avoid: mode logic duplicated across references.
- Config and env changes: none.

## Verification
- [ ] SKILL.md under 500 lines, description under 1,024 characters
- [ ] 3 must-trigger and 3 must-not-trigger phrases per mode pass

## Revisit when
The description cannot cover all modes under 1,024 characters.

## More information
