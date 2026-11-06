"""~/.samepage/config: which store this machine uses (ADR-0002).

A plain `key=value` file. Keys: backend (github or notion), store_path (GitHub
store clone), notion_page_id (Notion store). Set SAMEPAGE_HOME to use another
folder (tests). No credentials are ever written here (ADR-0006).
"""
import os

KEYS = ("backend", "store_path", "notion_page_id", "repo")


def home():
    return os.environ.get("SAMEPAGE_HOME") or os.path.join(os.path.expanduser("~"), ".samepage")


def path():
    return os.path.join(home(), "config")


def read():
    values = {}
    if not os.path.isfile(path()):
        return values
    with open(path(), encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() in KEYS:
                values[key.strip()] = value.strip()
    return values


def write(values):
    os.makedirs(home(), exist_ok=True)
    lines = ["# samepage config. No credentials go here."]
    lines += ["%s=%s" % (k, values[k]) for k in KEYS if values.get(k)]
    with open(path(), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def normalize_repo_url(url):
    """B14: git@host:owner/repo.git and https forms become https://host/owner/repo, lowercased."""
    url = (url or "").strip()
    if not url:
        return ""
    if url.startswith("git@") and ":" in url:
        host, rest = url[4:].split(":", 1)
        url = "https://%s/%s" % (host, rest)
    elif url.startswith("ssh://"):
        rest = url[len("ssh://"):]
        if "@" in rest.split("/", 1)[0]:
            rest = rest.split("@", 1)[1]
        url = "https://" + rest
    elif url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    if "@" in url.split("//", 1)[1].split("/", 1)[0]:
        scheme, rest = url.split("//", 1)
        url = scheme + "//" + rest.split("@", 1)[1]
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    return url.lower()
