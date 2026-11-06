"""`sp init`: create or connect a store (US-01, Setup read model).

GitHub: creates a private repo (default name samepage-store) with the GitHub
CLI, scaffolds and indexes the store, pushes, and writes ~/.samepage/config.
--use-existing clones an existing store instead, with plain git when the
GitHub CLI is missing, and fills a placeholder profile from the template repo
(ADR-0016). Without the GitHub CLI a new store starts from the template link.
--local makes a store with no GitHub repo (offline use and tests). Never
overwrites anything, never handles tokens: auth is the user's own `gh` login
or git credentials (ADR-0006).
"""
import datetime
import json
import os
import shutil
import subprocess
import sys
import uuid

from . import SCHEMA_VERSION, config
from .frontmatter import emit
from .index import build_index

DEFAULT_REPO = "samepage-store"
TEMPLATE_REPO = "rx4u/samepage-store-template"
TEMPLATE_LINK = ("https://github.com/new?template_owner=rx4u&template_name=samepage-store-template"
                 "&name=samepage-store&visibility=private")
PLACEHOLDER_NAME = "Your name"
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "store-template")


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


def copy_template(path):
    """Copy store-template/ (README, .gitignore, the index Action) into a new store (WP-11)."""
    if not os.path.isdir(TEMPLATE_DIR):
        raise InitError("store template missing at %s; reinstall samepage" % TEMPLATE_DIR)
    shutil.copytree(TEMPLATE_DIR, path, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))


def _write(path, rel, fields, body=""):
    full = os.path.join(path, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as handle:
        handle.write(emit(fields, body))


def _write_people(path, now, profile, links, rules):
    _write(path, "profile.md", {"display_name": profile["display_name"], "headline": profile["headline"],
                                "location": profile.get("location"), "created_at": now, "updated_at": now})
    for order, (label, url) in enumerate(links, start=1):
        lid = str(uuid.uuid4())
        _write(path, "profile/links/%s.md" % lid[:8], {"id": lid, "label": label, "url": url, "sort_order": order,
                                                        "created_at": now})
    for rule in rules:
        rid = str(uuid.uuid4())
        _write(path, "rules/%s.md" % rid[:8], {"id": rid, "rule": rule, "surface": None, "is_active": "true",
                                               "created_at": now, "updated_at": now})


def scaffold(path, owner, profile, links, rules):
    """Write a new, valid store into an empty folder."""
    if os.path.exists(path):
        raise InitError("%s already exists; nothing was overwritten. Pick another --path" % path)
    now = _now()
    _write(path, "store.md", {"schema_version": SCHEMA_VERSION, "backend": "github", "owner_handle": owner,
                              "created_at": now, "updated_at": now})
    _write_people(path, now, profile, links, rules)
    _write(path, "projects/general.md", {"id": str(uuid.uuid4()), "slug": "general", "name": "General",
                                         "status": "active", "type": "other",
                                         "one_liner": "Handoffs and decisions that belong to no single project",
                                         "last_verified_at": now, "created_at": now, "updated_at": now, "tags": []})
    copy_template(path)
    ok, message, _ = build_index(path)
    if not ok:
        raise InitError(message)


def _read_fields(path, rel):
    from .frontmatter import parse
    with open(os.path.join(path, rel), encoding="utf-8") as handle:
        fields, _ = parse(handle.read())
    return fields


def is_placeholder(path):
    """True when the store still has the template repo's placeholder profile (ADR-0016)."""
    try:
        return _read_fields(path, "profile.md").get("display_name") == PLACEHOLDER_NAME
    except Exception:
        return False


def fill_profile(path, owner, profile, links, rules):
    """Replace the template's placeholder profile and owner, add links and rules, rebuild the index."""
    now = _now()
    store = _read_fields(path, "store.md")
    store.update({"owner_handle": owner, "updated_at": now})
    _write(path, "store.md", store)
    _write_people(path, now, profile, links, rules)
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


def _has_gh():
    try:
        return _run(["gh", "auth", "status"], check=False).returncode == 0
    except InitError:
        return False


def _profile_args(args):
    if not args.display_name or not args.headline:
        return None
    profile = {"display_name": args.display_name, "headline": args.headline, "location": args.location}
    links = _parse_links(args.link)
    rules = [r.strip() for r in (args.rule or []) if r.strip()]
    if any(len(r) > 200 for r in rules):
        raise InitError("each rule must be 200 characters or fewer")
    return profile, links, rules


def _use_existing(args, store):
    gh = _has_gh()
    if gh:
        owner = _run(["gh", "api", "user", "--jq", ".login"]).stdout.strip()
        repo = args.use_existing if "/" in args.use_existing else "%s/%s" % (owner, args.use_existing)
        visibility = json.loads(_run(["gh", "repo", "view", repo, "--json", "visibility"]).stdout).get("visibility", "")
    else:
        if "/" not in args.use_existing:
            raise InitError("without the GitHub CLI, give the full name: --use-existing OWNER/REPO")
        repo, visibility = args.use_existing, ""
    if os.path.exists(store):
        raise InitError("%s already exists; nothing was overwritten. Pick another --path" % store)
    if gh:
        _run(["gh", "repo", "clone", repo, store])
    else:
        _run(["git", "clone", "-q", "https://github.com/%s.git" % repo, store])
    if not os.path.isfile(os.path.join(store, "store.md")):
        raise InitError("%s is not a samepage store (no store.md). Make one from %s" % (repo, TEMPLATE_LINK))
    lines = ["samepage: connected %s at %s" % (repo, store)]
    if is_placeholder(store):
        filled = _profile_args(args)
        if not filled:
            raise InitError("%s still has the template profile. Run again with --display-name and --headline "
                            "(and optional --location, --link, --rule) to fill it in" % repo)
        fill_profile(store, repo.split("/")[0], *filled)
        _run(["git", "add", "-A"], cwd=store)
        _run(["git", "commit", "-q", "-m", "samepage: fill in profile"], cwd=store)
        push = _run(["git", "push", "-q"], cwd=store, check=False)
        lines.append("samepage: filled in your profile" + ("" if push.returncode == 0 else
                     " (saved locally; push failed, run git push in %s)" % store))
    config.write({"backend": "github", "store_path": store, "repo": repo})
    if visibility.upper() == "PUBLIC":
        lines.append("warning: %s is public; a store should be private" % repo)
    return "\n".join(lines)


def init(args):
    if config.read().get("backend") and not args.force_config:
        raise InitError("this machine already has a store in %s; use --force-config to replace the config entry"
                        % config.path())
    store = os.path.abspath(os.path.expanduser(args.path or os.path.join(config.home(), "store")))
    if args.use_existing:
        return _use_existing(args, store)
    filled = _profile_args(args)
    if not filled:
        raise InitError("--display-name and --headline are required for a new store")
    profile, links, rules = filled
    if args.local:
        scaffold(store, args.owner or "local", profile, links, rules)
        _run(["git", "init", "-q", "-b", "main"], cwd=store)
        _run(["git", "add", "-A"], cwd=store)
        _run(["git", "-c", "user.name=samepage", "-c", "user.email=samepage@localhost", "commit", "-q", "-m",
              "samepage: new store"], cwd=store)
        config.write({"backend": "github", "store_path": store})
        return "samepage: local store created at %s (no GitHub repo)" % store
    if not _has_gh():
        raise InitError("the GitHub CLI is not installed or not signed in. Create your store in one click instead:\n"
                        "  1. Open %s and click Create repository (keep it Private)\n"
                        "  2. Run: /sp init --use-existing YOUR-LOGIN/samepage-store --display-name ... --headline ..."
                        % TEMPLATE_LINK)
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

