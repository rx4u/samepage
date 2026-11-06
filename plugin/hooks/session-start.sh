#!/bin/sh
# samepage SessionStart hook: print this session's context (US-03).
# Never fails a session: any problem prints one line and exits 0.
ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
if ! command -v python3 >/dev/null 2>&1; then
  echo "samepage: python3 not found, context not loaded"
  exit 0
fi
PYTHONPATH="$ROOT" python3 -m sp boot --surface code --cwd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null \
  || echo "samepage: boot failed, continuing without context"
exit 0
