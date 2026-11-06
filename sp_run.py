"""Run sp by file path, with no PYTHONPATH: python3 /path/to/samepage/sp_run.py ARGS.

MCP configs written by `sp setup` use this, because some clients refuse a PYTHONPATH override in a
server's env (Gemini CLI blocks it as dangerous). Python puts this file's folder first on sys.path,
so the `sp` package next to it is the one imported (ADR-0020, B45).
"""
import sys

from sp.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
