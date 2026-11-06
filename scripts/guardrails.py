"""CI guardrails from docs/architecture/guardrails.md. Exit 1 on any violation.

Run from the repo root on Python 3.10+: python3 scripts/guardrails.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_DIRS = ("sp", "hooks", "commands", "skills")
WALK_ALLOW = {"sp/check.py", "sp/index.py"}
# Read folders that are not a store (ADR-0015): docs, generated fixtures, a Notion export.
NON_STORE_READERS = {"sp/schema.py", "sp/fixtures.py", "sp/export.py"}
EXAMPLE_HOSTS = re.compile(r"^https?://([a-z0-9%-]+\.)*example\.(com|org|net)(/|$)")
# github.com is the store backend (ADR-0002): the user's repos and GitHub's own template page (ADR-0016).
BACKEND_HOSTS = re.compile(r"^https://github\.com/")
# Repo scripts imported by tests (ADR-0016).
LOCAL_MODULES = {"package_skill", "make_template_repo"}
SKIP = {".git", "fixtures", "__pycache__", "index.tmp"}


def files(dirs, suffixes):
    for top in dirs:
        base = os.path.join(ROOT, top)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP]
            for name in filenames:
                if name.endswith(suffixes):
                    path = os.path.join(dirpath, name)
                    yield os.path.relpath(path, ROOT).replace(os.sep, "/"), path


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    problems = []

    def fail(rule, where, detail):
        problems.append("%s: %s: %s" % (rule, where, detail))

    stdlib = set(sys.stdlib_module_names) | {"sp"} | LOCAL_MODULES
    for rel, path in files(RUNTIME_DIRS + ("tests", "scripts"), (".py",)):
        text = read(path)
        for match in re.finditer(r"^\s*(?:from|import)\s+([a-zA-Z_][\w]*)", text, re.M):
            name = match.group(1)
            if name not in stdlib:
                fail("stdlib only (ADR-0012)", rel, "imports %s" % name)
        if (rel.startswith("sp/") and rel not in WALK_ALLOW | NON_STORE_READERS
                and re.search(r"\bos\.(walk|listdir|scandir)\(|\bglob\.|\.iterdir\(|\.rglob\(", text)):
            fail("no raw folder walks", rel, "only sp/check.py and sp/index.py may walk the store")
        if rel.startswith(("sp/", "hooks/", "commands/", "skills/")):
            if re.search(r"\b(offset|skip)\s*=", text):
                fail("no offset paging", rel, "offset or skip assignment")
            if re.search(r"\b(token|secret|password|api_key)\s*=", text, re.I) or re.search(
                    r"environ[^\n]*(TOKEN|SECRET|PASSWORD|API_KEY)", text):
                fail("no credential handling (ADR-0006)", rel, "credential variable")
            for url in re.findall(r"https?://[^\s\"')>,]+", text):
                host = re.match(r"https?://([^/]*)", url).group(1)
                if "." not in host or re.search(r"[%{}<]", host):
                    continue  # a template like https://%s/%s or https://host/owner, not an endpoint
                if not EXAMPLE_HOSTS.match(url) and not BACKEND_HOSTS.match(url):
                    fail("no maintainer-hosted endpoints", rel, url)
    for rel, path in files(("sp", "hooks", "commands", "skills", "tests", "scripts", "docs", "fixtures", ".github"),
                           (".py", ".md", ".json", ".yml", ".yaml", ".sh")):
        if "\u2014" in read(path):
            fail("no em dashes", rel, "contains U+2014")
    for rel in ("README.md", "SPEC.md", "CLAUDE.md"):
        if "\u2014" in read(os.path.join(ROOT, rel)):
            fail("no em dashes", rel, "contains U+2014")
    for rel, path in files(("skills",), ("SKILL.md",)):
        text = read(path)
        lines = text.count("\n") + 1
        if lines > 500:
            fail("SKILL.md length", rel, "%d lines, maximum 500" % lines)
        front = re.match(r"---\n(.*?)\n---", text, re.S)
        desc = re.search(r"^description:\s*(.*)$", front.group(1), re.M) if front else None
        if not desc:
            fail("SKILL.md frontmatter", rel, "missing description")
        else:
            if len(desc.group(1)) > 1024:
                fail("SKILL.md description", rel, "over 1,024 characters")
            if "<" in front.group(1) or ">" in front.group(1):
                fail("SKILL.md frontmatter", rel, "XML angle brackets")
    for name in ("requirements.txt", "package.json", "pyproject.toml", "setup.py", "Pipfile"):
        if os.path.exists(os.path.join(ROOT, name)):
            fail("no new dependency without ADR", name, "dependency manifest present")
    for rel, path in files((".github",), (".yml", ".yaml")):
        for use in re.findall(r"uses:\s*([^\s#]+)", read(path)):
            if not re.search(r"@[0-9a-f]{40}$", use):
                fail("actions pinned by commit sha", rel, use)
    if problems:
        print("guardrails: FAIL (%d)" % len(problems))
        for line in problems:
            print("  " + line)
        return 1
    print("guardrails: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
