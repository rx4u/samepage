# samepage

**Keep every Claude on the same page.**

Claude Code ships it. Claude chat forgets it. samepage fixes that.

You plan in claude.ai chat, design in Claude Design, build in Claude Code and run long tasks in Cowork. Each one forgets what the others know. Chat can't see what you shipped in Code last week. Code asks questions chat already answered.

samepage gives every Claude surface one shared working context:

- **Who you are** and how you want Claude to work, applied on every surface
- **Every project you have**, with status, stack, links and outcomes
- **What you shipped**, with proof links, so proposals and bios cite real work
- **What you decided**, so no surface reopens a settled question
- **Handoffs** between surfaces: plan in chat, pick it up in Code
- **Where each design system lives**, so Claude Design and Claude Code use the same tokens

Your context lives in a store you own: a private GitHub repo of Markdown files, or Notion. No server. No API keys. No account to create.

## Status

In design. The full architecture is in [docs/architecture](docs/architecture/README.md): PRD, data model, read contracts per surface, decisions and the build plan. v1 is planned for December 2026.

Star or watch the repo to follow the build.

## How it will work

| Surface | Reads | Writes |
|---|---|---|
| Claude Code | Boots your context into every session through a plugin hook | `/sp log`, `/sp handoff` |
| claude.ai chat and Cowork | One skill reads your store through the GitHub or Notion connector | "log this", "hand this to Code" |
| Claude Design | Imports tokens from your product repo; handoffs are recorded from Code | through Code and chat |

## License

MIT
