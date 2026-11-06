"""Build site/data.json, the release data the landing page reads (ADR-0022).

Every value comes from a file already in the repo, so the page cannot drift from the release:
- version: .claude-plugin/plugin.json (bumped at every release, B46)
- headline: the `<!-- headline: ... -->` line in docs/release/v<version>.md
- adapters: the "Works with" table in README.md (its status follows the tool ledger)
- tools: sp/mcp.py tool_specs()

Run `python3 scripts/site_data.py` after a release bump; `--check` exits 1 when site/data.json is stale.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OUT = os.path.join(ROOT, "site", "data.json")
REPO = "https://github.com/rx4u/samepage"
KIND_DEFAULT = {"plugin": "/plugin install samepage@samepage", "skill": "GitHub connector", "tokens": "design/tokens.json"}


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return handle.read()


def version():
    return json.loads(read(".claude-plugin", "plugin.json"))["version"]


def headline(ver):
    try:
        notes = read("docs", "release", "v%s.md" % ver)
    except OSError:
        return ""
    found = re.search(r"<!--\s*headline:\s*(.+?)\s*-->", notes)
    return found.group(1) if found else ""


def kind_of(how):
    low = how.lower()
    if low.startswith("plugin"):
        return "plugin"
    if low.startswith("skill"):
        return "skill"
    if "mcp" in low:
        return "mcp"
    return "tokens"


def adapters():
    text = read("README.md")
    start = text.index("## Works with")
    rows = []
    for line in text[start:].splitlines()[1:]:
        if line.startswith("## "):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in ("Tool", "") or set(cells[0]) <= set("-"):
            continue
        name, how, status = cells
        kind = kind_of(how)
        code = re.search(r"`([^`]+)`", how)
        cmd = code.group(1) if code and kind == "mcp" else KIND_DEFAULT.get(kind, how)
        rows.append({"name": name, "kind": kind, "how": cmd, "tested": status.lower() == "tested"})
    if not rows:
        raise SystemExit("site_data: no rows in the README Works with table")
    return rows


def tools():
    from sp.mcp import tool_specs
    specs = tool_specs()
    write = [name for name, spec in specs.items() if spec[3]]
    read_ = [name for name, spec in specs.items() if not spec[3]]
    return {"read": read_, "write": write, "total": len(specs)}


def build():
    ver = version()
    return {
        "version": ver,
        "release_url": "%s/releases/tag/v%s" % (REPO, ver),
        "headline": headline(ver),
        "boot_cap_chars": 8000,
        "tools": tools(),
        "adapters": adapters(),
    }


def render(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if site/data.json is stale")
    args = parser.parse_args(argv)
    want = render(build())
    try:
        have = read("site", "data.json")
    except OSError:
        have = ""
    if args.check:
        if have != want:
            print("site_data: site/data.json is stale; run python3 scripts/site_data.py", file=sys.stderr)
            return 1
        print("site_data: site/data.json is current")
        return 0
    if have != want:
        with open(OUT, "w", encoding="utf-8") as handle:
            handle.write(want)
        print("site_data: wrote site/data.json (v%s)" % json.loads(want)["version"])
    else:
        print("site_data: site/data.json already current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
