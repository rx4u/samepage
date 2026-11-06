#!/bin/sh
# samepage Stop hook: one nudge line when this project has commits today and the
# store has no ship event dated today (WP-08). Prints nothing otherwise.
# Never fails a session: any problem prints nothing and exits 0. sp nudge keeps
# its git call under 1 second; hooks.json caps the whole hook at 2 seconds.
ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
command -v python3 >/dev/null 2>&1 || exit 0
PYTHONPATH="$ROOT" python3 -m sp nudge --cwd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null
exit 0
