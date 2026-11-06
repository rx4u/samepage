# Users and roles

### Persona: Solo Builder
- Who: Freelancer, indie hacker or solo founder who builds with Claude Code and writes proposals, bios, posts and plans in claude.ai chat. Uses 2 to 4 Claude surfaces a day.
- Goal: every Claude surface already knows their work, rules and shipped projects.
- Frequency: boots daily (every Code session, most chats); logs 3 to 15 entries a week.
- Device: desktop for Code; desktop and mobile for chat.

### Persona: Design Builder
- Who: Product designer or design engineer who designs in Claude Design and builds or hands off in Claude Code.
- Goal: one design system and one set of design decisions shared by Design, Code and chat.
- Frequency: logs design assets 1 to 5 times a week; boots daily.
- Device: desktop.

### Persona: Maintainer
- Who: Owner of the public repo and reviewers of contributions.
- Goal: keep the spec stable, adapters working and issues answerable with `sp check` output.
- Frequency: weekly triage.
- Device: desktop.

## Account model
Single-user. One store belongs to one person. Tenancy key: none inside the store; the store itself is the tenancy boundary (one private repo or one Notion page tree per person).

## Permissions
| Role | Can read | Can write | Can delete | Can administer |
|---|---|---|---|---|
| Store owner (Solo Builder or Design Builder) | Whole store from every surface | Every entity, after per-entry confirmation | Nothing through samepage; by hand in GitHub or Notion only | Store repo settings, Notion page sharing |
| Surface (Claude on a surface) | Whole store | Only through the skill or `sp`, after confirmation | Nothing | Nothing |
| Other coding tool (Codex, Cursor, Copilot, Gemini CLI, Windsurf) through `sp mcp` or `sp` | Whole store, through serve files | Only through `sp`, after a preview the MCP server checks (ADR-0018) | Nothing | Nothing |
| Maintainer | Public repo and demo store | Public repo via reviewed PRs | Public repo files via PRs | Public repo |

## Auth
No credentials are created or stored by samepage.
- GitHub store from Code: the user's existing git credentials or `gh auth` session.
- GitHub store from chat and Cowork: the claude.ai GitHub connector, authorised by the user in claude.ai settings.
- Notion store: the Notion connector, authorised in claude.ai; Claude Code uses the same connectors when signed in with the claude.ai account (A9).
- Other coding tools: `sp mcp` and `sp` run as the user on their own machine and use the same git credentials as Claude Code. No tool is given a token by samepage (ADR-0006).
- Session length, MFA and SSO are inherited from GitHub, Notion and claude.ai.

## Lifecycle
- Onboarding: `install.sh` then `sp setup <tool>` for a non-Claude coding tool (ADR-0020); `sp init` (GitHub) or "set up samepage in Notion" (skill). Asks 6 profile questions: display name, headline, location, two links, three working rules.
- Invitation: none in v1.
- Deletion: the user deletes the store repo or Notion page by hand. samepage never deletes. Retention is the user's choice.
- Export: the GitHub store is already plain Markdown. A Notion store exports with `sp export --from notion` to the GitHub layout (WP-10).
