"""Command line: python3 -m sp <command>."""
import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sp", description="samepage store tools")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("schema", help="regenerate schema/*.json from the architecture DDL")
    check = sub.add_parser("check", help="validate a store")
    check.add_argument("store", nargs="?", default=".", help="store folder (default: current folder)")
    check.add_argument("--only", help="check one entity, for example projects")
    check.add_argument("--page", type=int, default=1, help="failure page, 50 per page")
    index = sub.add_parser("index", help="check the store, then rebuild index/")
    index.add_argument("store", nargs="?", default=".", help="store folder (default: current folder)")
    index.add_argument("--now", help="build time to record, ISO with zone (tests and reproducible builds)")
    boot = sub.add_parser("boot", help="print this session's context (used by the SessionStart hook)")
    boot.add_argument("--surface", default="code", choices=["code", "chat", "cowork"])
    boot.add_argument("--cwd", help="project folder, to match its git remote to a project")
    boot.add_argument("--time", action="store_true", help="print the run time to stderr")
    init = sub.add_parser("init", help="create or connect a store")
    init.add_argument("--backend", default="github", choices=["github"])
    init.add_argument("--name", help="repo name for a new store (default samepage-store)")
    init.add_argument("--use-existing", metavar="REPO", help="connect an existing store repo instead")
    init.add_argument("--local", action="store_true", help="create a store with no GitHub repo")
    init.add_argument("--path", help="where the store lives on this machine (default ~/.samepage/store)")
    init.add_argument("--owner", help="owner handle for a --local store")
    init.add_argument("--display-name")
    init.add_argument("--headline")
    init.add_argument("--location")
    init.add_argument("--link", action="append", help="Label=https://url, repeatable")
    init.add_argument("--rule", action="append", help="a working rule, repeatable")
    init.add_argument("--force-config", action="store_true", help="replace this machine's existing config entry")
    fixtures = sub.add_parser("fixtures", help="generate the perf fixture store")
    fixtures.add_argument("--perf", action="store_true", required=True)
    fixtures.add_argument("--seed", type=int, default=42)
    fixtures.add_argument("--out", default="fixtures/perf")
    # ----- stream B: write and read commands (WP-08, WP-09, WP-12, WP-13)
    from . import brief as _brief, handoff as _handoff, log as _log, proof as _proof, rules as _rules
    for _module in (_log, _handoff, _proof, _rules, _brief):
        _module.register(sub)
    # ----- end stream B
    # ----- wave 5 (ADR-0018, ADR-0020, ADR-0023): sp context, sp setup, sp mcp, sp link, sp sync, sp start (ADR-0024). Each module registers its own parser.
    from . import context as _context, mcp as _mcp, setup as _setup, start as _start, sync as _sync
    for _module in (_context, _setup, _mcp, _sync, _start):
        _module.register(sub)
    # ----- end wave 5
    # export (stream D, WP-10): Notion "Markdown & CSV" export to a GitHub store
    export = sub.add_parser("export", help="convert a Notion CSV export into a GitHub store")
    export.add_argument("--from-notion-csv", required=True, metavar="DIR",
                        help="unzipped Notion Markdown & CSV export of the samepage page")
    export.add_argument("--out", required=True, metavar="STORE", help="new store folder (must not exist)")
    export.add_argument("--utc-offset", default="+00:00",
                        help="zone of dates without one in the CSV, like +05:30 (default +00:00)")
    args = parser.parse_args(argv)
    if args.command == "export":
        from .export import run as run_export
        return run_export(args.from_notion_csv, args.out, utc_offset=args.utc_offset)
    # ----- stream B dispatch
    if getattr(args, "func", None) is not None:
        return args.func(args)
    # ----- end stream B dispatch
    if args.command == "schema":
        from .schema import generate
        for path in generate():
            print("wrote", path)
        return 0
    if args.command == "check":
        from .check import run
        return run(args.store, only=args.only, page=args.page)
    if args.command == "index":
        from .index import run as run_index
        return run_index(args.store, now=args.now)
    if args.command == "boot":
        from .boot import run as run_boot
        return run_boot(args.surface, cwd=args.cwd, show_time=args.time)
    if args.command == "init":
        from .init import run as run_init
        return run_init(args)
    if args.command == "fixtures":
        from .fixtures import generate_perf
        print(generate_perf(args.out, seed=args.seed))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
