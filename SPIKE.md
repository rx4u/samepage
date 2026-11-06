# WP-01 spikes (throwaway branch, deleted after results are recorded)

## A1: Claude Design imports tokens from a linked repo (Raja)
1. In Claude Design, start a new design and link the GitHub repo `rx4u/samepage`, branch `spike/wp01`.
2. Ask: "Design a simple pricing card for samepage using this repo's design system."
3. Pass if the card uses magenta `#C026D3` as the brand colour, Space Grotesk headings and square corners (0 radius).
4. Record: pass or fail, plus one screenshot. If the branch cannot be chosen, note that; the fallback test is the same file on main.

## A2: claude.ai chat reads and writes the repo in one run (Raja)
1. In claude.ai chat with the GitHub connector on, say: "Read SPIKE.md on branch spike/wp01 of rx4u/samepage, then create the file spikes/chat-write.md on that same branch containing the line: written from chat."
2. Pass if the file appears on the branch with that line.
3. Record: pass or fail, and the exact error if it fails.

## A7: SessionStart hook output reaches Claude Code context (Claude)
Result: PASS on 2026-11-06. A 5,965 character hook output was recalled at both ends (start and end markers) by Claude Code 2.1.318 in headless mode.
