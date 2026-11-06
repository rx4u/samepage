#!/bin/sh
# samepage installer for coding tools other than Claude Code (ADR-0020).
#
#   git clone https://github.com/rx4u/samepage && sh samepage/install.sh
#
# Puts samepage in $SAMEPAGE_HOME/tool (default ~/.samepage/tool) and a shim at ~/.local/bin/sp.
# Needs git and python3 3.9+. No sudo, no package manager, no shell profile edits, no tokens.
# SAMEPAGE_REF picks a branch, tag or commit (default main).
set -eu

SAMEPAGE_HOME="${SAMEPAGE_HOME:-$HOME/.samepage}"
REPO="${SAMEPAGE_REPO:-https://github.com/rx4u/samepage.git}"
REF="${SAMEPAGE_REF:-main}"
TOOL_DIR="$SAMEPAGE_HOME/tool"
BIN_DIR="$HOME/.local/bin"
SHIM="$BIN_DIR/sp"
MARK="# samepage shim (install.sh)"

fail() {
  echo "samepage: $1" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "git not found. Install git, then run this again."
command -v python3 >/dev/null 2>&1 || fail "python3 not found. Install Python 3.9 or newer, then run this again."
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' \
  || fail "python3 is older than 3.9. Install Python 3.9 or newer, then run this again."

if [ -d "$TOOL_DIR/.git" ]; then
  action="updated"
else
  [ -e "$TOOL_DIR" ] && fail "$TOOL_DIR exists and is not a samepage clone. Move it away, then run this again."
  mkdir -p "$SAMEPAGE_HOME"
  git clone -q "$REPO" "$TOOL_DIR" || fail "could not clone $REPO"
  action="installed"
fi
git -C "$TOOL_DIR" fetch -q origin "$REF" || fail "could not fetch $REF from $REPO"
git -C "$TOOL_DIR" checkout -q --detach FETCH_HEAD || fail "could not check out $REF"

if [ -e "$SHIM" ] && ! grep -q "$MARK" "$SHIM" 2>/dev/null; then
  fail "$SHIM exists and is not the samepage shim. Move it away, then run this again."
fi
mkdir -p "$BIN_DIR"
cat > "$SHIM" <<SHIM
#!/bin/sh
$MARK
SAMEPAGE_HOME="\${SAMEPAGE_HOME:-$SAMEPAGE_HOME}"
export SAMEPAGE_HOME
PYTHONPATH="$TOOL_DIR" exec python3 -m sp "\$@"
SHIM
chmod 755 "$SHIM"

echo "samepage: $action $(git -C "$TOOL_DIR" rev-parse --short HEAD) in $TOOL_DIR, command at $SHIM"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "samepage: $BIN_DIR is not on your PATH. Add this line to your shell profile: export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac
echo "samepage: next, if you have no store yet: sp init"
echo "samepage: then connect a tool from inside a project: sp setup codex (or copilot, gemini, cursor, windsurf, claude-desktop)"
