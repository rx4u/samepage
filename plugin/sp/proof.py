"""`sp proof [--tag SLUG]... [--page N]` (WP-12, Proof lookup read model, US-07).

Without tags it prints `index/proof-{n}.md` (20 rows a page). With tags it reads
`index/tags/{slug}.md` per tag (one page of at most 50 rows each) and keeps the projects
present in every tag, in the first tag's order (newest ship first). Never more than 50 rows.
"""
import re
import sys

from . import MAX_ROWS_PER_READ
from .write import SLUG_RE, read_index, resolve_read_store

MAX_TAGS = 3
ROW_RE = re.compile(r"^- .* \(([a-z0-9]+(?:-[a-z0-9]+)*)\) \[")


def rows_of(text):
    """Split a proof or tag page into (header lines, [(slug, row lines)])."""
    header, rows = [], []
    for line in text.splitlines():
        match = ROW_RE.match(line)
        if match:
            rows.append((match.group(1), [line]))
        elif rows and line.startswith("  "):
            rows[-1][1].append(line)
        elif not rows:
            header.append(line)
    return header, rows


def tag_page(tag, page):
    return "index/tags/%s.md" % tag if page == 1 else "index/tags/%s-%d.md" % (tag, page)


def proof(store, tags=(), page=1):
    """Return (exit code, text)."""
    tags = list(dict.fromkeys(tags or []))
    if len(tags) > MAX_TAGS:
        return 2, "samepage: at most %d tags (AND), got %d" % (MAX_TAGS, len(tags))
    for tag in tags:
        if not SLUG_RE.match(tag):
            return 2, "samepage: %r is not a tag slug" % tag
    if page < 1:
        return 2, "samepage: --page starts at 1"
    if not tags:
        text = read_index(store, "index/proof-%d.md" % page)
        if text is None:
            return 1, "samepage: no index/proof-%d.md; run sp index or pick an earlier page" % page
        header, rows = rows_of(text)
        return 0, "\n".join(header + [l for _, lines in rows[:MAX_ROWS_PER_READ] for l in lines]) + _footer(text)
    if len(tags) > 1 and page != 1:
        return 2, "samepage: --page works with one tag; add a tag to narrow instead"
    pages = []
    for tag in tags:
        text = read_index(store, tag_page(tag, page))
        if text is None:
            return 1, "samepage: no tag index %s; known tags have files under index/tags/" % tag_page(tag, page)
        pages.append(text)
    header, first = rows_of(pages[0])
    keep = None
    for text in pages[1:]:
        slugs = {slug for slug, _ in rows_of(text)[1]}
        keep = slugs if keep is None else keep & slugs
    rows = [r for r in first if keep is None or r[0] in keep][:MAX_ROWS_PER_READ]
    built = header[0] if header else ""
    total = "total: %d" % len(rows)
    if len(tags) == 1:
        total = next((l for l in header if l.startswith("total: ")), total)
    out = [built, total, "tags: %s" % " AND ".join(tags), ""]
    if not rows:
        out.append("no shipped project has all of these tags")
    for _, lines in rows:
        out.extend(lines)
    footer = _footer(pages[0], "--tag %s " % tags[0]) if len(tags) == 1 else ""
    return 0, "\n".join(out) + footer


def _footer(text, flags=""):
    match = re.search(r"^next: (\S+)$", text, re.M)
    return "\n\nnext page: sp proof %s--page %s" % (flags, _page_number(match.group(1))) if match else ""


def _page_number(name):
    match = re.search(r"-(\d+)\.md$", name)
    return match.group(1) if match else "2"


def run(args):
    store, problem = resolve_read_store(args.store)
    if problem:
        print("samepage: " + problem, file=sys.stderr)
        return 1
    code, text = proof(store, args.tag or [], args.page)
    (sys.stdout if code == 0 else sys.stderr).write(text.rstrip("\n") + "\n")
    return code


def register(sub):
    parser = sub.add_parser("proof", help="shipped work with proof links, optionally by tags (US-07)")
    parser.add_argument("--tag", action="append", help="tag slug, repeat up to 3 times (AND)")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--store")
    parser.set_defaults(func=run)
