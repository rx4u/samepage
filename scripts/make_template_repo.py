"""Build the public template store for rx4u/samepage-store-template (ADR-0016).

Usage: python3 scripts/make_template_repo.py OUT_DIR

Writes a valid store with a placeholder profile (display_name "Your name"),
the reserved general project, the store template files and a built index.
"Use this template" on GitHub copies it into a private store; samepage setup
then replaces the placeholder profile.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp.check import check_store  # noqa: E402
from sp.init import PLACEHOLDER_NAME, scaffold  # noqa: E402

PLACEHOLDER = {"display_name": PLACEHOLDER_NAME,
               "headline": "New samepage store. Say set up samepage to Claude to fill this in.",
               "location": None}


def build(out):
    scaffold(out, "your-github-login", PLACEHOLDER, [], [])
    report = check_store(out)
    if report.errors:
        raise SystemExit("template store fails sp check: %s" % report.errors)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print("template store written to %s" % build(os.path.abspath(sys.argv[1])))
