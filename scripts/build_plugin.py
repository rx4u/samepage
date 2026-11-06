"""Build plugin/, the folder the marketplace installs and the plugin directory reviews (ADR-0025).

The repo root holds tests, docs, the landing page and brand images. None of that belongs in a plugin, and
the directory's scan holds or blocks it (a test's fake secret, large vendored scripts, binaries). plugin/
gets only what the plugin runs. Every file is a copy of a source file in the repo, so edit the source and
run `python3 scripts/build_plugin.py`; `--check` exits 1 when plugin/ is stale.
"""
import argparse
import filecmp
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "plugin")
DIRS = ("sp", "skills", "schema", "store-template")  # no hooks/ (ADR-0026)
FILES = ("sp_run.py", "LICENSE", ".claude-plugin/plugin.json", ".claude-plugin/icon.png")
SKIP = ("__pycache__", ".DS_Store")
README = """# samepage plugin for Claude Code

Your AI tools forget. samepage doesn't. This plugin reads your shared working context (profile, rules,
projects, ships, decisions and handoffs) from a store you own, and adds the `/sp` commands to write to it.

## Install
```
/plugin marketplace add rx4u/samepage
/plugin install samepage@samepage
```
On Claude Code 2.1.275 or later, one step also works: `/plugin install samepage --marketplace rx4u/samepage`.
Then run `/sp init` once to create your private store.

## What it runs
- The `/sp` command (the `sp` skill) and the samepage skill. They run the bundled `sp` package with `python3` (Python
  standard library only, no installs). The plugin ships no hooks: ask "what am I working on?" or run
  `/sp boot` to load your context. The one-line installer on the website can also add a session-start
  entry to your own Claude Code settings, so context loads by itself.

## What it reads and writes
- Your store: a private GitHub repo you own, cloned on your machine (default `~/.samepage/store`), and the
  config at `~/.samepage/config`.
- Writes happen only after you confirm an entry. Each is a normal git commit pushed to your own repo with
  your own git credentials. `sp init` uses your signed-in GitHub CLI (`gh`) to create that repo.
- No server, no tokens stored, no data sent anywhere except your own git remote.

Source, tests and docs: https://github.com/rx4u/samepage. License: MIT.
"""


def wanted():
    """{relative path: source path or None for README} for every file plugin/ should hold."""
    files = {"README.md": None}
    for top in DIRS:
        for dirpath, dirnames, names in os.walk(os.path.join(ROOT, top)):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP)
            for name in sorted(names):
                if name in SKIP or name.endswith(".pyc"):
                    continue
                src = os.path.join(dirpath, name)
                files[os.path.relpath(src, ROOT)] = src
    for rel in FILES:
        files[rel] = os.path.join(ROOT, rel)
    return files


def same(rel, src):
    dst = os.path.join(OUT, rel)
    if not os.path.isfile(dst):
        return False
    if src is None:
        with open(dst, encoding="utf-8") as handle:
            return handle.read() == README
    return filecmp.cmp(src, dst, shallow=False)


def present():
    found = set()
    for dirpath, dirnames, names in os.walk(OUT):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for name in names:
            if name not in SKIP and not name.endswith(".pyc"):
                found.add(os.path.relpath(os.path.join(dirpath, name), OUT))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if plugin/ is stale")
    args = parser.parse_args(argv)
    files = wanted()
    stale = sorted(rel for rel, src in files.items() if not same(rel, src))
    extra = sorted(present() - set(files)) if os.path.isdir(OUT) else []
    if args.check:
        if stale or extra:
            print("build_plugin: plugin/ is stale (%s); run python3 scripts/build_plugin.py"
                  % ", ".join((stale + extra)[:5]), file=sys.stderr)
            return 1
        print("build_plugin: plugin/ is current (%d files)" % len(files))
        return 0
    for rel in extra:
        os.remove(os.path.join(OUT, rel))
    for rel in stale:
        dst = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if files[rel] is None:
            with open(dst, "w", encoding="utf-8") as handle:
                handle.write(README)
        else:
            shutil.copy2(files[rel], dst)
    for dirpath, dirnames, names in os.walk(OUT, topdown=False):
        if not os.listdir(dirpath):
            os.rmdir(dirpath)
    print("build_plugin: plugin/ has %d files (%d written, %d removed)" % (len(files), len(stale), len(extra)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
