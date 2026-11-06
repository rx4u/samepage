"""`sp log ship|decision|design` and `sp project` (WP-08, WP-12, WP-13; Log entry, Decision record,
Design pointer, Design handoff capture and Project detail read models).

Every value comes from a flag and nothing prompts: Claude drafts the entry, shows the `--dry-run`
output and runs the real write only after the user says yes (ADR-0007).
"""
import json
import datetime
import os
import re
import sys

from .boot import _git as git_quick
from . import config
from .write import (RESERVED_PROJECT, SLUG_RE, WriteError, add_tool_flags, add_write_flags, check_slug, git, new_file,
                    norm_id8, parse_time, read_index, read_project, resolve_read_store, run_write, schema,
                    touch_project, updated_file, utc_date)

SHIPPING_KINDS = ("shipped", "launched")
STATUS_BECOMES_SHIPPED = ("idea", "active", "unknown")


def lookup(name):
    return schema()[1][name]


# ----- sp log ship (US-05, B6)

def build_ship(ctx, args):
    slug = check_slug(args.project)
    changes = []
    project_rel = "projects/%s.md" % slug
    creating = any([args.new_project_name, args.new_project_type, args.new_project_one_liner])
    if ctx.exists(project_rel):
        if creating:
            raise WriteError("project %r already exists; drop the --new-project flags" % slug)
        fields, body = read_project(ctx, slug)
        fields = dict(fields)
        new_project = False
    else:
        if not (args.new_project_name and args.new_project_type and args.new_project_one_liner):
            raise WriteError("no project %r yet; to create it pass --new-project-name, --new-project-type "
                             "and --new-project-one-liner" % slug)
        fields = {"id": ctx.new_id(), "slug": slug, "name": args.new_project_name, "status": "active",
                  "type": args.new_project_type, "one_liner": args.new_project_one_liner,
                  "last_verified_at": ctx.now, "created_at": ctx.now, "updated_at": ctx.now, "tags": []}
        body = ""
        new_project = True
    occurred = parse_time(args.occurred_at) if args.occurred_at else ctx.now
    day = utc_date(occurred)
    metric = [args.metric_label, args.metric_value, args.metric_unit]
    if any(v is not None for v in metric) and (args.metric_label is None or args.metric_value is None):
        raise WriteError("a metric needs both --metric-label and --metric-value")
    if args.metric_value is not None:
        try:
            float(args.metric_value)
        except ValueError:
            raise WriteError("--metric-value must be a number")
    event_id, event_rel = ctx.new_path(lambda i: "events/%s/%s-%s-%s.md" % (day[:4], day, slug, i[:8]))
    event = {"id": event_id, "project": slug, "kind": args.kind}
    event.update(ctx.provenance(args))
    event.update({"summary": args.summary, "proof_url": args.proof_url, "metric_label": args.metric_label,
             "metric_value": args.metric_value, "metric_unit": args.metric_unit, "occurred_at": occurred,
             "created_at": ctx.now})
    changes.append(new_file("ship_event", event_rel, event))
    # B6: shipped or launched moves idea, active or unknown to shipped; never parked or archived.
    if args.kind in SHIPPING_KINDS:
        if fields.get("status") in STATUS_BECOMES_SHIPPED:
            fields["status"] = "shipped"
        if not fields.get("shipped_on") and fields.get("status") == "shipped":
            fields["shipped_on"] = day
    tags = list(fields.get("tags") or [])
    for raw in args.tag or []:
        tag_slug, _, label = raw.partition("=")
        check_slug(tag_slug, "tag")
        if tag_slug not in tags:
            tags.append(tag_slug)
        tag_rel = "tags/%s.md" % tag_slug
        if not ctx.exists(tag_rel) and tag_rel not in [c.rel for c in changes]:
            changes.append(new_file("tag", tag_rel, {"id": ctx.new_id(), "slug": tag_slug,
                                                     "label": label.strip() or tag_slug, "created_at": ctx.now}))
    if args.tag:
        fields["tags"] = tags
    if new_project:
        changes.insert(0, new_file("project", project_rel, fields))
    else:
        changes.append(touch_project(ctx, slug, (fields, body)))
    return changes


# ----- sp log decision (US-12)

def _find_decision(ctx, slug, id8):
    """The decision file for id8 in one project folder. Lists that one folder through git, never the store."""
    folder = "decisions/%s" % slug
    done = git(ctx.store, ["ls-files", "--cached", "--others", "--exclude-standard", "--", folder], timeout=10)
    matches = [p for p in done.stdout.split() if p.endswith("-%s.md" % id8)]
    if not matches:
        raise WriteError("no decision %s in project %r (decisions/%s/)" % (id8, slug, slug))
    return matches[0]


def build_decision(ctx, args):
    slug = check_slug(args.project)
    project = read_project(ctx, slug)
    decided = ctx.now
    day = utc_date(decided)
    new_id, rel = ctx.new_path(lambda i: "decisions/%s/%s-%s.md" % (slug, day, i[:8]))
    fields = {"id": new_id, "project": slug, "status": "accepted", **ctx.provenance(args), "title": args.title,
              "reason": args.reason, "decided_at": decided, "created_at": ctx.now, "updated_at": ctx.now}
    changes = [new_file("decision", rel, fields, args.body or "")]
    if args.supersedes:
        id8 = norm_id8(args.supersedes, "decision")
        old_rel = _find_decision(ctx, slug, id8)
        old, old_body = ctx.read(old_rel)
        if old.get("status") != "accepted":
            raise WriteError("decision %s is %s, only an accepted decision can be superseded"
                             % (id8, old.get("status")))
        old = dict(old)
        old.update({"status": "superseded", "superseded_by": new_id, "updated_at": ctx.now})
        changes.append(updated_file("decision", old_rel, old, old_body))
    changes.append(touch_project(ctx, slug, project))
    return changes


# ----- sp log design (US-10, US-11)

def _design_files(ctx, slug):
    done = git(ctx.store, ["ls-files", "--cached", "--others", "--exclude-standard", "--", "design/%s" % slug],
               timeout=10)
    return [p for p in done.stdout.split() if p.endswith(".md")][:50]


def build_design(ctx, args):
    slug = check_slug(args.project)
    project = read_project(ctx, slug)
    status = args.status or ("approved" if args.kind == "handoff_bundle" else "draft")
    if args.kind == "design_system" and not (args.tokens_repo_url and args.tokens_path):
        raise WriteError("a design_system needs --tokens-repo-url and --tokens-path (where the tokens file lives)")
    if bool(args.tokens_repo_url) != bool(args.tokens_path):
        raise WriteError("--tokens-repo-url and --tokens-path go together")
    new_id, rel = ctx.new_path(lambda i: "design/%s/%s.md" % (slug, i[:8]))
    fields = {"id": new_id, "project": slug, "kind": args.kind, "status": status, **ctx.provenance(args),
              "title": args.title, "source_url": args.source_url, "tokens_repo_url": args.tokens_repo_url,
              "tokens_path": args.tokens_path, "created_at": ctx.now, "updated_at": ctx.now}
    changes = [new_file("design_asset", rel, fields)]
    if args.kind == "design_system" and status == "approved":
        for other in _design_files(ctx, slug):
            if other == rel:
                continue
            found = ctx.read(other)
            if not found:
                continue
            old, body = found
            if old.get("kind") == "design_system" and old.get("status") == "approved":
                old = dict(old)
                old.update({"status": "superseded", "updated_at": ctx.now})
                changes.append(updated_file("design_asset", other, old, body))
    changes.append(touch_project(ctx, slug, project))
    return changes


# ----- sp project SLUG [--archive] (US-14)

def build_archive(ctx, args):
    slug = check_slug(args.slug)
    if slug == RESERVED_PROJECT:
        raise WriteError("the reserved project %r cannot be archived (B2)" % slug)
    fields, body = read_project(ctx, slug)
    if fields.get("status") == "archived":
        raise WriteError("project %r is already archived" % slug)
    return [touch_project(ctx, slug, (fields, body), {"status": "archived", "archived_at": ctx.now})]


def run_project(args):
    if args.archive:
        return run_write(args, build_archive, lambda a: "archive %s" % a.slug)
    store, problem = resolve_read_store(args.store)
    if problem:
        print("samepage: " + problem, file=sys.stderr)
        return 1
    if not SLUG_RE.match(args.slug or ""):
        print("samepage: %r is not a project slug" % args.slug, file=sys.stderr)
        return 1
    text = read_index(store, "index/project/%s.md" % args.slug)
    if text is None:
        print("samepage: no project %r in the index (index/project/%s.md); check the slug or run sp index"
              % (args.slug, args.slug), file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0


# ----- Stop hook nudge (WP-08)

NUDGE = "samepage: you committed today but logged nothing; run /sp log to record it"


def nudge(cwd, now=None):
    """Return the nudge line or None. Reads one serve file and runs one quick git command."""
    cfg = config.read()
    if cfg.get("backend") != "github":
        return None
    store = cfg.get("store_path", "")
    boot = read_index(store, "index/boot/code.md") if store else None
    if boot is None or not cwd or not os.path.isdir(cwd):
        return None
    if os.path.abspath(cwd) == os.path.abspath(store):
        return None
    commits = git_quick(["log", "--since=midnight", "-1", "--format=%h"], cwd, 1.0)
    if not commits:
        return None
    now = now or datetime.datetime.now().astimezone()
    days = {now.date().isoformat(), now.astimezone(datetime.timezone.utc).date().isoformat()}
    section = boot.split("## Recent ships", 1)
    if len(section) == 2:
        for line in section[1].split("\n## ", 1)[0].splitlines():
            match = re.match(r"^- (\d{4}-\d{2}-\d{2}) ", line)
            if match and match.group(1) in days:
                return None
    return NUDGE


def run_nudge(args):
    try:
        line = nudge(args.cwd)
    except Exception:  # the hook must never break a session
        line = None
    if line:
        if getattr(args, "json", False):
            # Stop hook stdout goes to the debug log; systemMessage is what Claude Code shows the user.
            print(json.dumps({"systemMessage": line}))
        else:
            print(line)
    return 0


# ----- argparse

def register(sub):
    log = sub.add_parser("log", help="log a ship, decision or design asset (writes after --dry-run review)")
    kinds = log.add_subparsers(dest="log_kind", required=True)
    ship = kinds.add_parser("ship", help="log a ship event (US-05)")
    ship.add_argument("--project", required=True, help="project slug")
    ship.add_argument("--kind", required=True, choices=lookup("event_kind"))
    ship.add_argument("--summary", required=True, help="what shipped, 280 characters max")
    ship.add_argument("--proof-url", help="stored as given, never fetched")
    ship.add_argument("--metric-label")
    ship.add_argument("--metric-value")
    ship.add_argument("--metric-unit")
    ship.add_argument("--occurred-at", help="ISO date-time with zone (default: now)")
    ship.add_argument("--new-project-name", help="create the project first")
    ship.add_argument("--new-project-type", choices=lookup("project_type"))
    ship.add_argument("--new-project-one-liner", help="140 characters max")
    ship.add_argument("--tag", action="append", metavar="SLUG[=Label]", help="tag the project, repeatable")
    add_tool_flags(ship)
    add_write_flags(ship)
    ship.set_defaults(func=lambda a: run_write(a, build_ship, lambda x: "log ship %s %s" % (x.project, x.kind)))
    decision = kinds.add_parser("decision", help="record a decision (US-12)")
    decision.add_argument("--project", required=True)
    decision.add_argument("--title", required=True, help="120 characters max")
    decision.add_argument("--reason", required=True)
    decision.add_argument("--body", help="longer detail, written as the Markdown body")
    decision.add_argument("--supersedes", metavar="ID", help="id (8 characters) of the decision this replaces")
    add_tool_flags(decision)
    add_write_flags(decision)
    decision.set_defaults(func=lambda a: run_write(a, build_decision, lambda x: "decision %s" % x.project))
    design = kinds.add_parser("design", help="record a design asset pointer (US-10, US-11)")
    design.add_argument("--project", required=True)
    design.add_argument("--kind", required=True, choices=lookup("asset_kind"))
    design.add_argument("--title", required=True)
    design.add_argument("--status", choices=["draft", "approved"],
                        help="default approved for handoff_bundle, draft otherwise")
    design.add_argument("--source-url")
    design.add_argument("--tokens-repo-url")
    design.add_argument("--tokens-path")
    add_tool_flags(design)
    add_write_flags(design)
    design.set_defaults(func=lambda a: run_write(a, build_design, lambda x: "design %s %s" % (x.project, x.kind)))
    project = sub.add_parser("project", help="show a project, or archive it with --archive (US-14)")
    project.add_argument("slug")
    project.add_argument("--archive", action="store_true", help="set status archived (never deletes)")
    add_write_flags(project)
    project.set_defaults(func=run_project)
    hook = sub.add_parser("nudge", help="Stop hook: one line when you committed today and logged nothing")
    hook.add_argument("--cwd", help="project folder (default: current folder)")
    hook.add_argument("--json", action="store_true", help="print {\"systemMessage\": ...} for the Stop hook")
    hook.set_defaults(func=lambda a: run_nudge(a) if a.cwd else run_nudge(_with_cwd(a)))


def _with_cwd(args):
    args.cwd = os.getcwd()
    return args
