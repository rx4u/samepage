"""`sp rules [list] | add --rule TEXT [--surface S] | pause ID8` (Rules read model, US-15).

list prints `index/rules.md`. add writes `rules/{id8}.md`; pause sets is_active false and
updated_at on one rule file at a known path.
"""
import sys

from .write import (WriteError, add_write_flags, new_file, norm_id8, read_index, resolve_read_store, run_write,
                    schema, updated_file)


def build_add(ctx, args):
    rule = (args.rule or "").strip()
    if not rule:
        raise WriteError("--rule is empty")
    new_id, rel = ctx.new_path(lambda i: "rules/%s.md" % i[:8])
    fields = {"id": new_id, "rule": rule, "surface": args.surface, "is_active": "true",
              "created_at": ctx.now, "updated_at": ctx.now}
    return [new_file("preference", rel, fields)]


def build_pause(ctx, args):
    id8 = norm_id8(args.rule_id, "rule")
    rel = "rules/%s.md" % id8
    found = ctx.read(rel)
    if found is None:
        raise WriteError("no rule %s (rules/%s.md)" % (id8, id8))
    fields, body = found
    if fields.get("is_active", "true") == "false":
        raise WriteError("rule %s is already paused" % id8)
    fields = dict(fields)
    fields["is_active"] = "false"
    fields["updated_at"] = ctx.now
    return [updated_file("preference", rel, fields, body)]


def run_list(args):
    store, problem = resolve_read_store(args.store)
    if problem:
        print("samepage: " + problem, file=sys.stderr)
        return 1
    text = read_index(store, "index/rules.md")
    if text is None:
        print("samepage: no index/rules.md; run sp index", file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0


def register(sub):
    rules = sub.add_parser("rules", help="list, add or pause working rules (US-15)")
    rules.add_argument("--store")
    rules.set_defaults(func=run_list)
    actions = rules.add_subparsers(dest="action")
    listing = actions.add_parser("list", help="active rules by surface")
    listing.add_argument("--store")
    listing.set_defaults(func=run_list)
    add = actions.add_parser("add", help="add a rule every surface (or one) applies")
    add.add_argument("--rule", required=True, help="200 characters max")
    add.add_argument("--surface", choices=schema()[1]["surface"], help="default: every surface")
    add_write_flags(add)
    add.set_defaults(func=lambda a: run_write(a, build_add, lambda x: "rule add"))
    pause = actions.add_parser("pause", help="stop applying a rule (never deletes it)")
    pause.add_argument("rule_id", metavar="ID8")
    add_write_flags(pause)
    pause.set_defaults(func=lambda a: run_write(a, build_pause, lambda x: "rule pause %s" % x.rule_id[:8]))
