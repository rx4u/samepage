"""`sp init`: create or connect a store (US-01, Setup read model).

GitHub: creates a private repo (default name samepage-store) with the GitHub
CLI, scaffolds and indexes the store, pushes, and writes ~/.samepage/config.
--use-existing clones an existing store instead. --local makes a store with
no GitHub repo (offline use and tests). Never overwrites anything, never
handles tokens: auth is the user's own `gh` login (ADR-0006).
"""
import datetime
import json
import os
import subprocess
import sys
import uuid

from . import SCHEMA_VERSION, config
from .frontmatter import emit
from .index import build_index

DEFAULT_REPO = "samepage-store"


class InitError(Exception):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run(cmd, cwd=None, check=True):
    try:
        done = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        raise InitError("%s is not installed" % cmd[0])
    if check and done.returncode != 0:
        raise InitError("%s failed: %s" % (" ".join(cmd[:3]), (done.stderr or done.stdout).strip()[:300]))
    return done


def scaffold(path, owner, profile, links, rules):
    """Write a new, valid store into an empty folder."""
    if os.path.exists(path):
        raise InitError("%s already exists; nothing was overwritten. Pick another --path" % path)
    now = _now()

    def write(rel, fields, body=""):
        full = os.path.join(path, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(emit(fields, body))

    write("store.md", {"schema_version": SCHEMA_VERSION, "backend": "github", "owner_handle": owner,
                       "created_at": now, "updated_at": now})
    write("profile.md", {"display_name": profile["display_name"], "headline": profile["headline"],
                         "location": profile.get("location"), "created_at": now, "updated_at": now})
    for order, (label, url) in enumerate(links, start=1):
        lid = str(uuid.uuid4())
        write("profile/links/%s.md" % lid[:8], {"id": lid, "label": label, "url": url, "sort_order": order,
                                                 "created_at": now})
    for rule in rules:
        rid = str(uuid.uuid4())
        write("rules/%s.md" % rid[:8], {"id": rid, "rule": rule, "surface": None, "is_active": "true",
                                        "created_at": now, "updated_at": now})
    write("projects/general.md", {"id": str(uuid.uuid4()), "slug": "general", "name": "General", "status": "active",
                                  "type": "other", "one_liner": "Handoffs and decisions that belong to no single project",
                                  "last_verified_at": now, "created_at": now, "updated_at": now, "tags": []})
    with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as handle:
        handle.write("# samepage store\n\nYour shared working context for every Claude surface. Private. "
                     "Edit through samepage (`/sp log`, \"log this\") or by hand, then run `sp check`.\n")
    ok, message, _ = build_index(path)
    if not ok:
        raise InitError(message)


def _parse_links(items):
    links = []
    for item in items or []:
        if "=" not in item:
            raise InitError("--link must look like Label=https://url")
        label, url = item.split("=", 1)
        if not url.startswith(("https://", "http://")):
            raise InitError("link %r must start with https://" % label)
        links.append((label.strip(), url.strip()))
    return links


def init(args):
    if config.read().get("backend") and not args.force_config:
        raise InitError("this machine already has a store in %s; use --force-config to replace the config entry"
                        % config.path())
    store = os.path.abspath(os.path.expanduser(args.path or os.path.join(config.home(), "store")))
    if args.use_existing:
        _run(["gh", "auth", "status"])
        owner = _run(["gh", "api", "user", "--jq", ".login"]).stdout.strip()
        repo = args.use_existing if "/" in args.use_existing else "%s/%s" % (owner, args.use_existing)
        info = json.loads(_run(["gh", "repo", "view", repo, "--json", "visibility"]).stdout)
        if os.path.exists(store):
            raise InitError("%s already exists; nothing was overwritten. Pick another --path" % store)
        _run(["gh", "repo", "clone", repo, store])
        config.write({"backend": "github", "store_path": store, "repo": repo})
        lines = ["samepage: connected %s at %s" % (repo, store)]
        if info.get("visibility", "").upper() == "PUBLIC":
            lines.append("warning: %s is public; a store should be private" % repo)
        return "\n".join(lines)
    if not args.display_name or not args.headline:
        raise InitError("--display-name and --headline are required for a new store")
    profile = {"display_name": args.display_name, "headline": args.headline, "location": args.location}
    links = _parse_links(args.link)
    rules = [r.strip() for r in (args.rule or []) if r.strip()]
    if any(len(r) > 200 for r in rules):
        raise InitError("each rule must be 200 characters or fewer")
    if args.local:
        scaffold(store, args.owner or "local", profile, links, rules)
        _run(["git", "init", "-q", "-b", "main"], cwd=store)
        _run(["git", "add", "-A"], cwd=store)
        _run(["git", "-c", "user.name=samepage", "-c", "user.email=samepage@localhost", "commit", "-q", "-m",
              "samepage: new store"], cwd=store)
        config.write({"backend": "github", "store_path": store})
        return "samepage: local store created at %s (no GitHub repo)" % store
    try:
        _run(["gh", "auth", "status"])
    except InitError:
        raise InitError("GitHub CLI is not signed in. Run: gh auth login")
    owner = _run(["gh", "api", "user", "--jq", ".login"]).stdout.strip()
    name = args.name or DEFAULT_REPO
    if _run(["gh", "repo", "view", "%s/%s" % (owner, name), "--json", "name"], check=False).returncode == 0:
        raise InitError("%s/%s already exists. Use --name to pick another name, or --use-existing %s to connect it"
                        % (owner, name, name))
    scaffold(store, owner, profile, links, rules)
    _run(["git", "init", "-q", "-b", "main"], cwd=store)
    _run(["git", "add", "-A"], cwd=store)
    _run(["git", "commit", "-q", "-m", "samepage: new store"], cwd=store)
    _run(["gh", "repo", "create", "%s/%s" % (owner, name), "--private", "--source", store, "--push"], cwd=store)
    lines = ["samepage: created private repo %s/%s and store at %s" % (owner, name, store)]
    protect = _run(["gh", "api", "-X", "PATCH", "repos/%s/%s" % (owner, name),
                    "-f", "security_and_analysis[secret_scanning][status]=enabled",
                    "-f", "security_and_analysis[secret_scanning_push_protection][status]=enabled"], check=False)
    if protect.returncode != 0:
        lines.append("note: GitHub push protection could not be enabled on this plan; sp check still blocks secrets")
    config.write({"backend": "github", "store_path": store, "repo": "%s/%s" % (owner, name)})
    return "\n".join(lines)


def run(args):
    try:
        print(init(args))
        return 0
    except InitError as exc:
        print("sp init: %s" % exc, file=sys.stderr)
        return 1

