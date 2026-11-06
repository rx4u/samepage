#!/bin/sh
# samepage installer (ADR-0020, ADR-0024). The landing page serves this exact file at /install, so the
# one line in README.md (curl the file, pipe it to sh) sets up everything.
#
# Puts samepage in $SAMEPAGE_HOME/tool (default ~/.samepage/tool) and a shim at ~/.local/bin/sp, then
# runs `sp start`: makes or connects your store and connects every AI tool it finds. No questions.
# Needs git and python3 3.9+. No sudo, no package manager, no shell profile edits, no tokens.
# SAMEPAGE_REF picks a branch, tag or commit (default: the newest v* release tag, else main; B36).
# SAMEPAGE_NO_START=1 installs the command only. The whole script runs from main() on the last
# line, so a cut-off download runs nothing.
set -eu

SAMEPAGE_HOME="${SAMEPAGE_HOME:-$HOME/.samepage}"
REPO="${SAMEPAGE_REPO:-https://github.com/rx4u/samepage.git}"
REF="${SAMEPAGE_REF:-}"
TOOL_DIR="$SAMEPAGE_HOME/tool"
BIN_DIR="$HOME/.local/bin"
SHIM="$BIN_DIR/sp"
MARK="# samepage shim (install.sh)"

fail() {
  echo "samepage: $1" >&2
  exit 1
}

main() {
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
if [ -z "$REF" ]; then
  git -C "$TOOL_DIR" fetch -q --tags origin || fail "could not fetch tags from $REPO"
  REF=$(git -C "$TOOL_DIR" tag -l 'v*' --sort=-v:refname | head -n 1)
  [ -n "$REF" ] || REF=main
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
exec python3 "$TOOL_DIR/sp_run.py" "\$@"
SHIM
chmod 755 "$SHIM"

echo "samepage: $action $REF ($(git -C "$TOOL_DIR" rev-parse --short HEAD)) in $TOOL_DIR, command at $SHIM"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "samepage: optional: to type sp yourself, add $BIN_DIR to your PATH (export PATH=\"$BIN_DIR:\$PATH\"). Your tools do not need it." ;;
esac
if [ "${SAMEPAGE_NO_START:-}" = "1" ]; then
  echo "samepage: next: sp start (sets up your store and connects your tools)"
  return 0
fi
"$SHIM" start </dev/null
}

main "$@"
