"""`sp setup <tool>`: connect a coding tool to samepage (WP-21, ADR-0020, Tool setup read model).

For one tool: add the `samepage` entry to its MCP config, copy the skill where it reads skills, and
add the instruction block to the current project (`sp context`). Writes a config only where the path
is verified for this OS (system-design.md, Tool adapters); otherwise prints the snippet and the file it
belongs in. Never prompts, never handles a token, never deletes a file. `--dry-run` writes nothing.
"""
import filecmp
import json
import os
import re
import shutil
import subprocess
import sys

from . import context

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_SOURCE = os.path.join(ROOT, "skills", "samepage")
LAUNCHER = os.path.join(ROOT, "sp_run.py")
NAME = "samepage"
PLUGIN_COMMAND = "/plugin marketplace add rx4u/samepage, then /plugin install samepage@samepage"
AGENT_SKILLS = "~/.agents/skills"


def _vscode_user():
    if sys.platform == "darwin":
        return "~/Library/Application Support/Code/User"
    return "~/.config/Code/User"


def tools():
    """setup name -> how that tool is connected. `verified` False means print the snippet only."""
    darwin = sys.platform == "darwin"
    return {
        "codex": {"code": "codex", "label": "Codex",
                  "configs": [{"format": "toml", "path": "~/.codex/config.toml", "verified": True}],
                  "skills": AGENT_SKILLS},
        "copilot": {"code": "copilot", "label": "GitHub Copilot",
                    "configs": [{"format": "copilot_cli", "path": "~/.copilot/mcp-config.json", "verified": True},
                                {"format": "vscode", "path": _vscode_user() + "/mcp.json", "verified": True,
                                 "only_if_folder": _vscode_user()}],
                    "skills": AGENT_SKILLS},
        "gemini": {"code": "gemini_cli", "label": "Gemini CLI",
                   "configs": [{"format": "mcp_servers", "path": "~/.gemini/settings.json", "verified": True}],
                   "skills": AGENT_SKILLS,
                   "note": "Gemini CLI starts MCP servers only in folders you trust. Accept the trust prompt when "
                           "you open this project in Gemini CLI, then check with: gemini mcp list (B45)."},
        "cursor": {"code": "cursor", "label": "Cursor",
                   "configs": [{"format": "mcp_servers", "path": "~/.cursor/mcp.json", "verified": False}],
                   "skills": AGENT_SKILLS},
        "windsurf": {"code": "windsurf", "label": "Windsurf",
                     "configs": [{"format": "mcp_servers", "path": "~/.codeium/windsurf/mcp_config.json",
                                  "verified": False}],
                     "skills": None},
        "claude-desktop": {"code": "claude_desktop", "label": "Claude Desktop",
                           "configs": [{"format": "mcp_servers",
                                        "path": "~/Library/Application Support/Claude/claude_desktop_config.json",
                                        "verified": darwin}],
                           "skills": None,
                           "note": "Skills in Claude Desktop come from your claude.ai account: upload "
                                   "dist/samepage.skill in Customize, Skills."},
        "claude-code": {"code": "claude_code", "label": "Claude Code", "configs": [], "skills": None,
                        "note": "for the /sp commands, also install the plugin. In Claude Code run: " + PLUGIN_COMMAND},
    }


def server_entry(code):
    # No PYTHONPATH: Gemini CLI refuses it in a server env. sp_run.py finds the package by its own path (B45).
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    if os.environ.get("SAMEPAGE_HOME"):
        env["SAMEPAGE_HOME"] = os.environ["SAMEPAGE_HOME"]
    return {"command": sys.executable, "args": [LAUNCHER, "mcp", "--tool", code], "env": env}


def shaped(fmt, entry):
    if fmt == "copilot_cli":
        return dict({"type": "local"}, **entry, tools=["*"])
    if fmt == "vscode":
        return dict({"type": "stdio"}, **entry)
    return dict(entry)


def top_key(fmt):
    return "servers" if fmt == "vscode" else "mcpServers"


# ----- TOML (Codex), edited as text (B29)

def toml_block(entry):
    env = ", ".join("%s = %s" % (k, json.dumps(v)) for k, v in entry["env"].items())
    return ("[mcp_servers.%s]\ncommand = %s\nargs = [%s]\nenv = { %s }\n"
            % (NAME, json.dumps(entry["command"]), ", ".join(json.dumps(a) for a in entry["args"]), env))


def toml_render(old, entry):
    block = toml_block(entry)
    lines = (old or "").splitlines(True)
    head = "[mcp_servers.%s]" % NAME
    start = None
    for i, line in enumerate(lines):
        if line.strip() == head:
            start = i
            break
    if start is None:
        text = old or ""
        if text and not text.endswith("\n"):
            text += "\n"
        return text + ("\n" if text else "") + block
    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j].strip()
        if stripped.startswith("[") and not stripped.startswith("[mcp_servers.%s." % NAME):
            end = j
            break
    rest = "".join(lines[end:])
    return "".join(lines[:start]) + block + ("\n" + rest if rest else "")


# ----- JSON configs

def json_indent(text):
    match = re.search(r"\n([ \t]+)\"", text or "")
    if not match:
        return 2
    return "\t" if match.group(1).startswith("\t") else len(match.group(1))


def json_render(old, fmt, entry):
    """Return (new_text or None when unchanged). Raise ValueError when the file does not parse."""
    data = json.loads(old) if old and old.strip() else {}
    if not isinstance(data, dict):
        raise ValueError("the top level is not an object")
    servers = data.get(top_key(fmt))
    if servers is None:
        servers = {}
    if not isinstance(servers, dict):
        raise ValueError("%s is not an object" % top_key(fmt))
    wanted = shaped(fmt, entry)
    if servers.get(NAME) == wanted:
        return None
    servers[NAME] = wanted
    data[top_key(fmt)] = servers
    return json.dumps(data, indent=json_indent(old)) + "\n"


def snippet(fmt, entry):
    if fmt == "toml":
        return toml_block(entry).rstrip("\n")
    return json.dumps({top_key(fmt): {NAME: shaped(fmt, entry)}}, indent=2)


# ----- steps

def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def config_step(cfg, code, dry_run, out):
    """Returns an exit code contribution: 0 or 1."""
    path = os.path.expanduser(cfg["path"])
    entry = server_entry(code)
    if cfg.get("only_if_folder") and not os.path.isdir(os.path.expanduser(cfg["only_if_folder"])):
        out("samepage: skipped %s (%s not found)" % (cfg["path"], cfg["only_if_folder"]))
        return 0
    if not cfg["verified"]:
        out("samepage: the config path for this tool is not verified, so nothing was changed. Add this to %s:"
            % cfg["path"])
        out(snippet(cfg["format"], entry))
        return 0
    old = _read(path) if os.path.isfile(path) else None
    try:
        new = toml_render(old, entry) if cfg["format"] == "toml" else json_render(old, cfg["format"], entry)
    except ValueError as exc:
        out("samepage: not changed: %s does not parse as plain JSON (%s). Add this to it by hand:" % (cfg["path"], exc))
        out(snippet(cfg["format"], entry))
        return 1
    if new is None or new == old:
        out("samepage: %s already has the samepage entry" % cfg["path"])
        return 0
    if dry_run:
        out("samepage: dry run, would %s the samepage entry in %s:" % ("add" if old is None or NAME not in old else "replace", cfg["path"]))
        out(snippet(cfg["format"], entry))
        return 0
    backup = path + ".samepage-backup"
    if old is not None and not os.path.exists(backup):
        shutil.copy2(path, backup)
    try:
        _write(path, new)
    except OSError as exc:
        out("samepage: could not write %s (%s)" % (cfg["path"], exc))
        return 1
    out("samepage: wrote the samepage entry in %s%s" % (cfg["path"], " (backup: %s)" % (cfg["path"] + ".samepage-backup")
                                                        if old is not None else ""))
    return 0


def _skill_files():
    for folder, dirs, names in os.walk(SKILL_SOURCE):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(names):
            if name.endswith(".pyc") or name == ".DS_Store":
                continue
            full = os.path.join(folder, name)
            yield os.path.relpath(full, SKILL_SOURCE), full


def skill_step(target, dry_run, out):
    dest = os.path.join(os.path.expanduser(target), NAME)
    changed = [rel for rel, full in _skill_files()
               if not (os.path.isfile(os.path.join(dest, rel)) and filecmp.cmp(full, os.path.join(dest, rel), False))]
    if not changed:
        out("samepage: skill already current in %s/%s" % (target, NAME))
        return 0
    if dry_run:
        out("samepage: dry run, would copy the samepage skill to %s/%s (%d files)" % (target, NAME, len(changed)))
        return 0
    for rel in changed:
        os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
        shutil.copyfile(os.path.join(SKILL_SOURCE, rel), os.path.join(dest, rel))
    out("samepage: copied the samepage skill to %s/%s (%d files)" % (target, NAME, len(changed)))
    return 0


CLAUDE_SETTINGS = "~/.claude/settings.json"
HOOK_SCRIPT = os.path.join(ROOT, "hooks", "session-start.sh")


def claude_hook_entry():
    return {"type": "command", "command": 'sh "%s"' % HOOK_SCRIPT, "timeout": 3}


def _is_ours(hook):
    return isinstance(hook, dict) and "session-start.sh" in str(hook.get("command", "")) and \
        "samepage" in str(hook.get("command", ""))


def claude_hook_step(dry_run, out):
    """Load samepage context at every Claude Code session start, from the user's own settings (ADR-0026).

    The plugin ships no hooks, so the installed sp adds one SessionStart entry to ~/.claude/settings.json,
    keeping every other setting and a .samepage-backup copy of the old file.
    """
    if not os.path.isfile(HOOK_SCRIPT):
        out("samepage: session start not added: this sp has no hooks/session-start.sh (the plugin copy ships none). "
            "Use the one-line install in the samepage README")
        return 0
    path = os.path.expanduser(CLAUDE_SETTINGS)
    old = _read(path) if os.path.isfile(path) else None
    try:
        data = json.loads(old) if old and old.strip() else {}
        if not isinstance(data, dict):
            raise ValueError("the top level is not an object")
        hooks = data.setdefault("hooks", {})
        groups = hooks.setdefault("SessionStart", [])
        if not isinstance(hooks, dict) or not isinstance(groups, list):
            raise ValueError("hooks.SessionStart is not a list")
    except ValueError as exc:
        out("samepage: %s not changed (%s). Add a SessionStart hook running: sh \"%s\"" % (CLAUDE_SETTINGS, exc,
                                                                                          HOOK_SCRIPT))
        return 1
    wanted = claude_hook_entry()
    found = False
    for group in groups:
        inner = group.get("hooks", []) if isinstance(group, dict) else []
        for i, hook in enumerate(inner):
            if _is_ours(hook):
                if found:
                    continue
                found = True
                if hook == wanted:
                    out("samepage: %s already loads samepage at session start" % CLAUDE_SETTINGS)
                    return 0
                inner[i] = wanted
    if not found:
        groups.append({"hooks": [wanted]})
    text = json.dumps(data, indent=json_indent(old)) + "\n"
    if dry_run:
        out("samepage: would add a session-start entry to %s" % CLAUDE_SETTINGS)
        return 0
    if old is not None:
        _write(path + ".samepage-backup", old)
    _write(path, text)
    out("samepage: %s now loads samepage at every session start%s"
        % (CLAUDE_SETTINGS, " (backup: settings.json.samepage-backup)" if old is not None else ""))
    return 0


def project_root(cwd):
    try:
        done = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True,
                              timeout=5, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() if done.returncode == 0 and done.stdout.strip() else None


def context_step(code, cwd, dry_run, out):
    if code not in context.TARGETS:
        return 0
    root = project_root(cwd)
    if not root:
        out("samepage: %s is not inside a git repo; in a project, run: sp context --tool %s" % (cwd, code))
        return 0
    try:
        context.apply(root, [context.plan(root, code)], dry_run=dry_run, out=out)
    except context.ContextError as exc:
        out("samepage: instruction file not changed: %s" % exc)
        return 1
    return 0


def setup(name, cwd, dry_run=False, out=print):
    spec = tools()[name]
    code = spec["code"]
    status = 0
    if "/.claude/plugins/" in ROOT.replace(os.sep, "/"):
        out("samepage: note: this sp runs from the Claude Code plugin cache, which moves on plugin updates. "
            "Install sp with install.sh and run sp setup from there.")
    for cfg in spec["configs"]:
        status = max(status, config_step(cfg, code, dry_run, out))
    if spec.get("skills"):
        status = max(status, skill_step(spec["skills"], dry_run, out))
    if name == "claude-code":
        status = max(status, claude_hook_step(dry_run, out))
    status = max(status, context_step(code, cwd, dry_run, out))
    if spec.get("note"):
        out("samepage: " + spec["note"])
    if not dry_run and spec["configs"]:
        out("samepage: restart %s, then ask it: what am I working on?" % spec["label"])
    return status


def run(args):
    return setup(args.tool, os.path.abspath(os.path.expanduser(args.cwd or os.getcwd())), dry_run=args.dry_run)


def register(sub):
    parser = sub.add_parser("setup", help="connect a coding tool: MCP entry, skill and instruction block (ADR-0020)")
    parser.add_argument("tool", choices=sorted(tools()), help="tool to connect")
    parser.add_argument("--cwd", help="project folder for the instruction block (default: current folder)")
    parser.add_argument("--dry-run", action="store_true", help="print every planned change and write nothing")
    parser.set_defaults(func=run)
