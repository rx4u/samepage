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
    args = parser.parse_args(argv)
    if args.command == "schema":
        from .schema import generate
        for path in generate():
            print("wrote", path)
        return 0
    if args.command == "check":
        from .check import run
        return run(args.store, only=args.only, page=args.page)
    return 2


if __name__ == "__main__":
    sys.exit(main())
