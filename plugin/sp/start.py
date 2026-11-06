"""`sp start`: the one-line install's second half (ADR-0024). Asks nothing, prints every step.

1. Store: reuse this machine's config; else connect or create LOGIN/samepage-store with a signed-in
   GitHub CLI; else make a local store. A local store is published later once the GitHub CLI is signed in.
2. Profile without questions: name from GitHub, git or the login; a plain default headline.
3. Tools: every tool found on this machine is connected (Claude Code through its own plugin CLI plus a
   session-start entry in ~/.claude/settings.json, ADR-0026; the others through sp setup's config and
   skill steps).
No tokens are read or stored; GitHub access is the user's own gh login (ADR-0006).
"""
import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys

from . import config, init, setup

DEFAULT_HEADLINE = "Building with AI tools"
MARKETPLACE = "rx4u/samepage"
PLUGIN = "samepage@samepage"
SKILL_LINK = "https://github.com/rx4u/samepage/raw/main/dist/samepage.skill"
ORDER = ("claude-code", "codex", "gemini", "copilot", "cursor", "windsurf", "claude-desktop")


def _run(cmd, cwd=None, timeout=180):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(cmd, 1, "", str(exc))


def _home(*parts):
    return os.path.join(os.path.expanduser("~"), *parts)


def detect():
    """Tools on this machine, by command on PATH or config folder, in ORDER."""
    which = shutil.which
    found = {
        "claude-code": bool(which("claude")),
        "codex": bool(which("codex")) or os.path.isdir(_home(".codex")),
        "gemini": bool(which("gemini")) or os.path.isdir(_home(".gemini")),
        "copilot": bool(which("copilot")) or os.path.isdir(_home(".copilot"))
        or os.path.isdir(os.path.expanduser(setup._vscode_user())),
        "cursor": bool(which("cursor")) or os.path.isdir(_home(".cursor")),
        "windsurf": bool(which("windsurf")) or os.path.isdir(_home(".codeium", "windsurf")),
        "claude-desktop": sys.platform == "darwin" and os.path.isdir(_home("Library", "Application Support",
                                                                          "Claude")),
    }
    return [name for name in ORDER if found[name]]


def guess_name(gh):
    if gh:
        done = _run(["gh", "api", "user", "--jq", ".name"])
        if done.returncode == 0 and done.stdout.strip() and done.stdout.strip() != "null":
            return done.stdout.strip()
    done = _run(["git", "config", "--global", "user.name"])
    if done.returncode == 0 and done.stdout.strip():
        return done.stdout.strip()
    try:
        return getpass.getuser()
    except Exception:
        return "Me"


def _init_args(**over):
    values = dict(force_config=False, path=None, use_existing=None, display_name=None, headline=DEFAULT_HEADLINE,
                  location=None, link=[], rule=[], local=False, owner=None, name=None, backend="github")
    values.update(over)
    return argparse.Namespace(**values)


def _has_remote(store):
    done = _run(["git", "remote"], cwd=store)
    return done.returncode == 0 and bool(done.stdout.strip())


def _publish(store, out):
    """Turn a local store into a private LOGIN/samepage-store repo."""
    owner = _run(["gh", "api", "user", "--jq", ".login"]).stdout.strip()
    repo = "%s/%s" % (owner, init.DEFAULT_REPO)
    if _run(["gh", "repo", "view", repo, "--json", "name"]).returncode == 0:
        out("samepage: %s already exists, so your local store stays local. Connect one of them by hand: "
            "sp init --use-existing %s --force-config" % (repo, repo))
        return
    meta = init._read_fields(store, "store.md")
    if meta.get("owner_handle") != owner:
        meta.update({"owner_handle": owner, "updated_at": init._now()})
        init._write(store, "store.md", meta)
        _run(["git", "add", "-A"], cwd=store)
        _run(["git", "-c", "user.name=samepage", "-c", "user.email=samepage@localhost", "commit", "-q", "-m",
              "samepage: owner %s" % owner], cwd=store)
    done = _run(["gh", "repo", "create", repo, "--private", "--source", store, "--push"], cwd=store)
    if done.returncode != 0:
        out("samepage: could not publish your store: %s" % (done.stderr or done.stdout).strip()[:300])
        return
    values = config.read()
    values["repo"] = repo
    config.write(values)
    out("samepage: published your local store as private repo %s" % repo)


def store_step(dry_run, out):
    values = config.read()
    store = values.get("store_path")
    gh = init._has_gh()
    if values.get("backend") and store and os.path.isfile(os.path.join(store, "store.md")):
        out("samepage: store: using %s" % store)
        if gh and not _has_remote(store):
            if dry_run:
                out("samepage: would publish it as a private GitHub repo")
            else:
                _publish(store, out)
        return 0
    if values.get("backend"):
        out("samepage: the config points at %s, which is not a store. Fix it with sp init --force-config" % store)
        return 1
    name = guess_name(gh)
    if gh:
        owner = _run(["gh", "api", "user", "--jq", ".login"]).stdout.strip()
        exists = _run(["gh", "repo", "view", "%s/%s" % (owner, init.DEFAULT_REPO), "--json", "name"]).returncode == 0
        plan = ("connect your existing %s/%s" if exists else "create private repo %s/%s") % (owner, init.DEFAULT_REPO)
        args = _init_args(use_existing=init.DEFAULT_REPO if exists else None, display_name=name)
    else:
        plan = "create a local store (sign in to GitHub later and run sp start again to put it on GitHub)"
        args = _init_args(local=True, owner=getpass.getuser() or "local", display_name=name)
    if dry_run:
        out("samepage: store: would %s, profile name %r" % (plan, name))
        return 0
    try:
        out(init.init(args))
    except init.InitError as exc:
        out("samepage: store not set up: %s" % exc)
        return 1
    out("samepage: profile: %s, %s. Change either in profile.md in your store" % (name, DEFAULT_HEADLINE))
    return 0


def claude_code_step(dry_run, out):
    if dry_run:
        out("samepage: Claude Code: would run claude plugin marketplace add %s and claude plugin install %s"
            % (MARKETPLACE, PLUGIN))
        return setup.claude_hook_step(dry_run, out)
    added = _run(["claude", "plugin", "marketplace", "add", MARKETPLACE])
    if added.returncode != 0:
        out("samepage: Claude Code: could not add the marketplace: %s"
            % (added.stderr or added.stdout).strip()[-300:])
        return 1
    done = _run(["claude", "plugin", "install", PLUGIN])
    if done.returncode != 0:
        out("samepage: Claude Code: install failed: %s" % (done.stderr or done.stdout).strip()[-300:])
        return 1
    if "already installed" in (done.stdout + done.stderr):
        _run(["claude", "plugin", "marketplace", "update", "samepage"])
        _run(["claude", "plugin", "update", PLUGIN])
        out("samepage: Claude Code: plugin already installed, updated to the latest")
    else:
        out("samepage: Claude Code: plugin installed")
    return setup.claude_hook_step(dry_run, out)


def tool_step(name, dry_run, out):
    spec = setup.tools()[name]
    status = 0
    for cfg in spec["configs"]:
        status = max(status, setup.config_step(cfg, spec["code"], dry_run, out))
    if spec.get("skills"):
        status = max(status, setup.skill_step(spec["skills"], dry_run, out))
    return status


def start(dry_run=False, out=print):
    status = store_step(dry_run, out)
    if status:
        return status
    found = detect()
    if not found:
        out("samepage: tools: none found. Install one, then run sp start again (or sp setup TOOL)")
    for name in found:
        label = setup.tools()[name]["label"]
        out("samepage: connecting %s" % label)
        step = claude_code_step if name == "claude-code" else (lambda d, o, n=name: tool_step(n, d, o))
        status = max(status, step(dry_run, out))
    missing = [setup.tools()[n]["label"] for n in ORDER if n not in found]
    if missing:
        out("samepage: not found here: %s" % ", ".join(missing))
    out("samepage: claude.ai and Cowork: upload %s in Customize, Skills" % SKILL_LINK)
    if any(n != "claude-code" for n in found):
        out("samepage: in a project, sp setup TOOL also adds the short instruction file")
    if not dry_run:
        out("samepage: done. Restart your tools and ask: what am I working on?")
    return status


def run(args):
    return start(dry_run=args.dry_run)


def register(sub):
    parser = sub.add_parser("start", help="set up everything with no questions: store and every tool found (ADR-0024)")
    parser.add_argument("--dry-run", action="store_true", help="print every planned step and write nothing")
    parser.set_defaults(func=run)
