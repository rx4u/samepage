"""`sp link` and `sp sync`: share rules and decisions between two local store clones (ADR-0023).

sp link add PATH --name NAME | list | remove NAME
sp sync [NAME] [--dry-run] [--yes]

Sync copies, in both directions and by id:
- rules: every `rules/{id8}.md`, active or paused;
- decisions: `decisions/{slug}/...` when the other store has project `slug` (every store has `general`).

The same id in both stores: the later `updated_at` wins; equal and identical means nothing to do.
Files are copied byte for byte, so no new key is written and each store's pinned Action passes.
A record carrying a key newer than the other store's schema_version is skipped, never rewritten.
Nothing else crosses. Each store gets one commit through the shared write path (pull, check,
index, commit, push). No network call beyond the user's own git remote, no tokens (ADR-0006).
"""
import os
import re
import sys

from . import config, version_tuple
from .index import load, to_time
from .write import Change, Context, WriteError, apply, has_remote, pull, resolve_store, schema

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TABLES = ("preference", "decision")
LABEL = {"preference": "rule", "decision": "decision"}


# ----- sp link

def _store_dir(path):
    full = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(os.path.join(full, "store.md")):
        raise WriteError("%s is not a samepage store (no store.md)" % full)
    return full


def run_link_add(args):
    try:
        name = (args.name or "").strip().lower()
        if not NAME_RE.match(name):
            raise WriteError("--name %r: use lowercase letters, digits and single hyphens, like personal" % args.name)
        path = _store_dir(args.path)
        values = config.read()
        current = config.links(values)
        main_store = values.get("store_path") and os.path.abspath(os.path.expanduser(values["store_path"]))
        if path == main_store:
            raise WriteError("%s is this machine's own store; link the other one" % path)
        for other, where in current.items():
            if other != name and os.path.abspath(where) == path:
                raise WriteError("%s is already linked as %s" % (path, other))
        if name not in current and len(current) >= config.MAX_LINKS:
            raise WriteError("already %d linked stores, the maximum; remove one first" % config.MAX_LINKS)
        values[config.LINK_PREFIX + name] = path
        config.write(values, keep_links=False)
        print("samepage: linked %s (%s). Run sp sync %s --dry-run to see what would cross" % (name, path, name))
        return 0
    except WriteError as exc:
        print("samepage: %s" % exc, file=sys.stderr)
        return 1


def run_link_list(args):
    current = config.links()
    if not current:
        print("samepage: no linked stores. Add one with sp link add PATH --name personal")
        return 0
    for name, path in current.items():
        ok = os.path.isfile(os.path.join(path, "store.md"))
        print("%s  %s%s" % (name, path, "" if ok else "  (missing: no store.md)"))
    return 0


def run_link_remove(args):
    values = config.read()
    key = config.LINK_PREFIX + (args.name or "").strip().lower()
    if key not in values:
        print("samepage: no linked store %r (see sp link list)" % args.name, file=sys.stderr)
        return 1
    del values[key]
    config.write(values, keep_links=False)
    print("samepage: unlinked %s. Nothing in either store was changed" % args.name)
    return 0


# ----- planning

class Side:
    """One store as sync sees it: its schema version, project slugs and rule and decision records."""

    def __init__(self, label, store):
        self.label = label
        self.store = store
        rows = load(store)
        meta = rows.get("store_meta") or [{}]
        self.version = version_tuple(meta[0].get("schema_version", ""))
        self.projects = {r.get("slug") for r in rows.get("project", [])}
        self.records = {}
        for table in TABLES:
            for row in rows.get(table, []):
                if row.get("id"):
                    self.records[row["id"]] = (table, row)

    def text(self, rel):
        with open(os.path.join(self.store, rel), encoding="utf-8") as handle:
            return handle.read()


def _since_keys():
    tables = schema()[0]["tables"]
    return {t: {k["key"]: version_tuple(k["since"]) for k in tables[t]["keys"] if k.get("since")} for t in TABLES}


def _newer_key(table, row, target_version, since):
    for key, need in since[table].items():
        if row.get(key) not in (None, "") and need > target_version:
            return key, need
    return None


def _stamp(row):
    try:
        return to_time(row.get("updated_at") or row.get("created_at") or "")
    except ValueError:
        return None


def plan_one_way(src, dst, since=None):
    """What moves from src to dst. Returns (changes, skipped) where skipped is [(rel, reason)]."""
    since = since or _since_keys()
    changes, skipped = [], []
    for rid, (table, row) in sorted(src.records.items(), key=lambda item: item[1][1]["_path"]):
        rel = row["_path"]
        if table == "decision" and row.get("project") not in dst.projects:
            skipped.append((rel, "%s has no project %s" % (dst.label, row.get("project"))))
            continue
        newer = _newer_key(table, row, dst.version, since)
        if newer:
            skipped.append((rel, "uses %s (schema %d.%d); upgrade %s first" % (newer[0], newer[1][0], newer[1][1],
                                                                               dst.label)))
            continue
        text = src.text(rel)
        theirs = dst.records.get(rid)
        if theirs is None:
            if os.path.exists(os.path.join(dst.store, rel)):
                skipped.append((rel, "%s has a different record at this path" % dst.label))
                continue
            changes.append(_change(table, rel, row, text, new=True))
            continue
        their_row = theirs[1]
        if their_row["_path"] != rel:
            skipped.append((rel, "same id at %s in %s; fix by hand" % (their_row["_path"], dst.label)))
            continue
        if dst.text(rel) == text:
            continue
        mine, other = _stamp(row), _stamp(their_row)
        if mine is None or other is None:
            skipped.append((rel, "updated_at is not readable"))
        elif mine > other:
            changes.append(_change(table, rel, row, text, new=False))
        elif mine == other:
            skipped.append((rel, "edited in both stores at the same updated_at; edit one and sync again"))
    return changes, skipped


def _change(table, rel, row, text, new):
    change = Change(table, rel, {}, "", new=new)
    change.text = text  # byte for byte; validate() parses this text
    change.fields = {k: v for k, v in row.items() if not k.startswith("_")}
    return change


def plan(here, there):
    since = _since_keys()
    return {"to_there": plan_one_way(here, there, since), "to_here": plan_one_way(there, here, since)}


def _counts(changes):
    rules = sum(1 for c in changes if c.table == "preference")
    decisions = len(changes) - rules
    parts = []
    if rules:
        parts.append("%d rule%s" % (rules, "" if rules == 1 else "s"))
    if decisions:
        parts.append("%d decision%s" % (decisions, "" if decisions == 1 else "s"))
    return ", ".join(parts) or "nothing"


def print_plan(here, there, result, out=print):
    for key, src, dst in (("to_there", here, there), ("to_here", there, here)):
        changes, skipped = result[key]
        out("%s -> %s: %s" % (src.label, dst.label, _counts(changes)))
        for change in changes[:50]:
            what = LABEL[change.table]
            title = change.fields.get("rule") or change.fields.get("title") or ""
            out("  %s %s %s  %s" % ("copy" if change.new else "update", what, change.rel, title[:80]))
        if len(changes) > 50:
            out("  %d more" % (len(changes) - 50))
        for rel, reason in skipped[:50]:
            out("  skip %s: %s" % (rel, reason))
        if len(skipped) > 50:
            out("  %d more skipped" % (len(skipped) - 50))


# ----- sp sync

def _pick_link(name):
    current = config.links()
    if not current:
        raise WriteError("no linked store. Add one with sp link add PATH --name personal")
    if name:
        key = name.strip().lower()
        if key not in current:
            raise WriteError("no linked store %r (linked: %s)" % (name, ", ".join(current)))
        return key, current[key]
    if len(current) > 1:
        raise WriteError("%d linked stores; name one: sp sync %s" % (len(current), " | ".join(current)))
    return next(iter(current.items()))


def _confirm(args):
    if args.yes:
        return True
    if not sys.stdin.isatty():
        print("samepage: not written. Run again with --yes to write without a prompt")
        return False
    try:
        answer = input("Write these changes to both stores? [y/N] ")
    except EOFError:
        return False
    return answer.strip().lower() in ("y", "yes")


def run_sync(args):
    try:
        here_path = resolve_store(args.store)
        name, there_path = _pick_link(args.name)
        there_path = _store_dir(there_path)
        if os.path.abspath(there_path) == os.path.abspath(here_path):
            raise WriteError("the linked store %s is this store" % name)
        if not args.dry_run:
            for path in (here_path, there_path):
                if has_remote(path):
                    pull(path, print)
        here, there = Side("this store", here_path), Side(name, there_path)
        result = plan(here, there)
        print_plan(here, there, result)
        if not result["to_there"][0] and not result["to_here"][0]:
            print("samepage: both stores already share every rule and decision they can")
            return 0
        if args.dry_run:
            print("samepage: dry run, nothing written")
            return 0
        if not _confirm(args):
            return 1
        code = 0
        for key, dst, src_label in (("to_there", there, "this store"), ("to_here", here, name)):
            changes = result[key][0]
            if not changes:
                continue
            ctx = Context(dst.store)
            code |= apply(ctx, changes, "sync from %s: %s" % (src_label, _counts(changes)))
        return code
    except WriteError as exc:
        print("samepage: %s" % exc, file=sys.stderr)
        return 1


def register(sub):
    link = sub.add_parser("link", help="link a second store to share rules and decisions (ADR-0023)")
    link.set_defaults(func=run_link_list)
    actions = link.add_subparsers(dest="action")
    add = actions.add_parser("add", help="link another local store clone")
    add.add_argument("path", metavar="PATH", help="the other store's folder on this machine")
    add.add_argument("--name", required=True, help="a short name, like personal or work")
    add.set_defaults(func=run_link_add)
    listing = actions.add_parser("list", help="linked stores")
    listing.set_defaults(func=run_link_list)
    remove = actions.add_parser("remove", help="unlink a store (changes no files)")
    remove.add_argument("name", metavar="NAME")
    remove.set_defaults(func=run_link_remove)
    sync = sub.add_parser("sync", help="share rules and decisions with a linked store, both ways (ADR-0023)")
    sync.add_argument("name", nargs="?", metavar="NAME", help="linked store (needed when more than one)")
    sync.add_argument("--store", help="this store's folder (default: from ~/.samepage/config)")
    sync.add_argument("--dry-run", action="store_true", help="show what would cross and write nothing")
    sync.add_argument("--yes", action="store_true", help="write without asking")
    sync.set_defaults(func=run_sync)
