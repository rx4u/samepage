# Design modes

Claude Design is a surface that cannot read or write the store in v1 (ADR-0011). It reads design tokens from a linked product repo. The store keeps pointers to where design lives, records Design handoffs that arrive in Claude Code, and produces a brief the user pastes into Claude Design.

Design assets are pointers. Never copy token values, colours or type scales into the store, and never fetch the tokens file at recall. Claude Code reads it from the product repo when building.

## Kinds

| Kind | Use for | Keys to fill |
|---|---|---|
| design_system | The project's tokens file | `tokens_repo_url`, `tokens_path` (W3C design tokens, usually `design/tokens.json`), optional `source_url` |
| screen_set | A set of designed screens | `source_url` when there is a share link |
| prototype | A clickable prototype | `source_url` |
| handoff_bundle | A Claude Design "Send to Claude Code" bundle received in Code | `source_url` when the bundle has one |

Status is `draft` or `approved`. `superseded` is set only by the rule below.

## Pointer

1. Ask which project, which kind, and the title.
2. For a design system, ask for the product repo URL and the tokens file path. Default path: `design/tokens.json`.
3. Ask whether it is approved. A new approved design_system makes the previous approved design_system of the same project `superseded` (show that change too).
4. Show, confirm, write. Code: `sp log design --project SLUG --kind design_system --title "..." --status approved --tokens-repo-url URL --tokens-path PATH --dry-run`.

Lookup ("where is X's design system?"): read the Design section of the project detail file and answer with the repo, path and status. Approved items come first; superseded ones are hidden.

## Handoff capture (Claude Code)

When a Code session receives a Claude Design handoff bundle:

1. Take the bundle's title and share link if it shows one.
2. Draft a design asset: kind `handoff_bundle`, status `approved`, surface `code`, `source_url` = the link.
3. If the bundle has no link, leave `source_url` empty and set the title to `Design handoff, no link` (append the bundle title after a colon when there is one).
4. Show, confirm, write: `sp log design --project SLUG --kind handoff_bundle --title "..." --status approved [--source-url URL] --dry-run`.

## Design brief

A brief the user pastes into Claude Design so it designs with the owner's voice, the project's decisions and the right tokens. In Code run `sp brief SLUG`. In chat or Cowork compose it from the boot file (profile voice) and the project detail file. It is a read; nothing is written.

Claude Design needs the tokens file and the branch named in the prompt: with a linked repo and no design system selected, it used the named file on the named branch, and its codebase picker shows no branch choice (A1, verified 2026-11-06). Always name both.

Format:

```
Design brief: {project name}

What it is: {one_liner}
Voice: {profile voice}

Decisions in force:
- {decision title}: {reason}
- ...

Design system: Use the design tokens in {tokens_path} on the default branch of {tokens_repo_url}. Do not invent colours, type or spacing outside those tokens.

Task: {what the user wants designed}
```

- This matches what `sp brief` prints. When the user works on another branch, or you know the default branch's name, replace "the default branch" with `the {branch} branch` so Claude Design reads the right one.
- When the project has no approved design_system, write `Design system: none recorded` and suggest logging one.
- Take decisions only from "Decisions in force" (accepted ones), at most 10.

## Claude Design moves into Claude

Standalone Claude Design moves into claude.ai on 2026-12-14. Until that move lands and is retested, keep this flow: pointers in the store, tokens in the product repo, a pasted brief. If Design inside Claude can run skills or connectors, it may read and write the store directly; that change needs an ADR before this skill relies on it.
