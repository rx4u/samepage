"""`sp handoff new|start|done|drop|list|show` (WP-09, Handoff inbox read model, US-08, US-09).

list reads `index/handoffs-{surface}-{n}.md`; show reads one `handoffs/{id8}.md`. Neither walks
the store. `--to design` is rejected: Claude Design cannot read the store in v1 (B7, ADR-0011).
"""
import sys

from .frontmatter import FrontmatterError, parse
from .write import (WriteError, add_write_flags, check_slug, new_file, norm_id8, read_index, read_project,
                    resolve_read_store, run_write, schema, touch_project, updated_file)

READ_SURFACES = ("code", "chat", "cowork")


def build_new(ctx, args):
    if args.to == "design":
        raise WriteError("handoffs to design are not possible: Claude Design cannot read the store in v1 "
                         "(B7). Use sp brief SLUG and paste it into Claude Design instead")
    slug = check_slug(args.project)
    project = read_project(ctx, slug)
    new_id, rel = ctx.new_path(lambda i: "handoffs/%s.md" % i[:8])
    fields = {"id": new_id, "project": slug, "from_surface": args.from_surface, "to_surface": args.to,
              "status": "open", "title": args.title, "created_at": ctx.now, "picked_up_at": None, "done_at": None}
    body = args.body or ""
    return [new_file("handoff", rel, fields, body, keep_empty=("picked_up_at", "done_at")),
            touch_project(ctx, slug, project)]


TRANSITIONS = {
    "start": (("open",), "picked_up", "picked_up_at"),
    "done": (("open", "picked_up"), "done", "done_at"),
    "drop": (("open", "picked_up"), "dropped", "done_at"),
}


def build_move(ctx, args):
    id8 = norm_id8(args.handoff_id, "handoff")
    rel = "handoffs/%s.md" % id8
    found = ctx.read(rel)
    if found is None:
        raise WriteError("no handoff %s (handoffs/%s.md)" % (id8, id8))
    fields, body = found
    allowed, status, stamp = TRANSITIONS[args.action]
    if fields.get("status") not in allowed:
        raise WriteError("handoff %s is %s; %s needs it to be %s" % (id8, fields.get("status"), args.action,
                                                                       " or ".join(allowed)))
    fields = dict(fields)
    fields["status"] = status
    fields[stamp] = ctx.now
    return [updated_file("handoff", rel, fields, body), touch_project(ctx, fields["project"])]


def run_list(args):
    store, problem = resolve_read_store(args.store)
    if problem:
        print("samepage: " + problem, file=sys.stderr)
        return 1
    if args.page < 1:
        print("samepage: --page starts at 1", file=sys.stderr)
        return 2
    text = read_index(store, "index/handoffs-%s-%d.md" % (args.surface, args.page))
    if text is None:
        print("samepage: no index/handoffs-%s-%d.md; run sp index or pick an earlier page" % (args.surface, args.page),
              file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0


def run_show(args):
    store, problem = resolve_read_store(args.store)
    if problem:
        print("samepage: " + problem, file=sys.stderr)
        return 1
    try:
        id8 = norm_id8(args.handoff_id, "handoff")
    except WriteError as exc:
        print("samepage: %s" % exc, file=sys.stderr)
        return 1
    text = read_index(store, "handoffs/%s.md" % id8)
    if text is None:
        print("samepage: no handoff %s" % id8, file=sys.stderr)
        return 1
    try:
        fields, body = parse(text)
    except FrontmatterError as exc:
        print("samepage: handoffs/%s.md is not valid (%s); run sp check" % (id8, exc), file=sys.stderr)
        return 1
    print("%s [%s] %s: %s (from %s to %s, %s)" % (id8, fields.get("status"), fields.get("project"),
                                                  fields.get("title"), fields.get("from_surface"),
                                                  fields.get("to_surface"), fields.get("created_at")))
    print("")
    print(body.strip())
    return 0


def register(sub):
    surfaces = schema()[1]["surface"]
    handoff = sub.add_parser("handoff", help="hand work to another surface and close it (US-08, US-09)")
    actions = handoff.add_subparsers(dest="action", required=True)
    new = actions.add_parser("new", help="leave a brief for another surface")
    new.add_argument("--project", required=True)
    new.add_argument("--to", required=True, choices=surfaces, help="code, chat or cowork (design is rejected, B7)")
    new.add_argument("--title", required=True, help="120 characters max")
    new.add_argument("--body", required=True, help="the brief, 4,000 characters max")
    new.add_argument("--from", dest="from_surface", default="code", choices=surfaces)
    add_write_flags(new)
    new.set_defaults(func=lambda a: run_write(a, build_new, lambda x: "handoff to %s for %s" % (x.to, x.project)))
    for action, text in (("start", "pick a handoff up"), ("done", "close a handoff as done"),
                         ("drop", "close a handoff as dropped")):
        move = actions.add_parser(action, help=text)
        move.add_argument("handoff_id", metavar="ID8")
        add_write_flags(move)
        move.set_defaults(func=lambda a: run_write(a, build_move, lambda x: "handoff %s %s" % (x.action, x.handoff_id[:8])))
    listing = actions.add_parser("list", help="open and picked-up handoffs to a surface")
    listing.add_argument("--surface", default="code", choices=READ_SURFACES)
    listing.add_argument("--page", type=int, default=1)
    listing.add_argument("--store")
    listing.set_defaults(func=run_list)
    show = actions.add_parser("show", help="print one handoff's brief")
    show.add_argument("handoff_id", metavar="ID8")
    show.add_argument("--store")
    show.set_defaults(func=run_show)
