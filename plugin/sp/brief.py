"""`sp brief SLUG`: a design brief to paste into Claude Design (WP-13, ADR-0011).

Claude Design cannot read the store, so the brief carries what it needs: the profile voice
(from `index/boot/code.md`), the project name and one-liner, the decisions in force and the
approved design_system pointer (from `index/project/{slug}.md`). A1 showed the tokens file
and branch must be named, so the pointer says both.
"""
import re
import sys

from .write import SLUG_RE, read_index, resolve_read_store


def _section(text, title):
    parts = re.split(r"^## ", text, flags=re.M)
    for part in parts[1:]:
        heading, _, rest = part.partition("\n")
        if heading.strip() == title:
            return [l for l in rest.splitlines() if l.startswith("- ")]
    return []


def brief(store, slug):
    """Return (exit code, text)."""
    if not SLUG_RE.match(slug or ""):
        return 2, "samepage: %r is not a project slug" % slug
    project = read_index(store, "index/project/%s.md" % slug)
    if project is None:
        return 1, "samepage: no project %r in the index (index/project/%s.md)" % (slug, slug)
    boot = read_index(store, "index/boot/code.md") or ""
    lines = project.splitlines()
    title = next((i for i, l in enumerate(lines) if l.startswith("# ")), None)
    name = re.sub(r" \([^()]*\)$", "", lines[title][2:]) if title is not None else slug
    one_liner = lines[title + 1] if title is not None and title + 1 < len(lines) else ""
    voice = next((l[len("Voice: "):] for l in boot.splitlines() if l.startswith("Voice: ")), None)
    out = ["Design brief: %s" % name, "", "Project: %s. %s" % (name, one_liner)]
    out.append("Voice: %s" % (voice or "not set in the profile"))
    decisions = _section(project, "Decisions in force")
    out += ["", "Decisions in force:"]
    out.extend(decisions or ["- none recorded"])
    pointer = None
    for line in _section(project, "Design"):
        match = re.match(r"^- (?:[0-9a-f]{8} )?design_system \[approved\] .*? tokens: (\S+) (\S+)", line)
        if match:
            pointer = (match.group(1), match.group(2))
            break
    out.append("")
    if pointer:
        out.append("Design system: Use the design tokens in %s on the default branch of %s" % (pointer[1], pointer[0]))
    else:
        out.append("Design system: none approved yet. Log one with: sp log design --project %s --kind design_system "
                   "--status approved --tokens-repo-url URL --tokens-path PATH" % slug)
    return 0, "\n".join(out)


def run(args):
    store, problem = resolve_read_store(args.store)
    if problem:
        print("samepage: " + problem, file=sys.stderr)
        return 1
    code, text = brief(store, args.slug)
    (sys.stdout if code == 0 else sys.stderr).write(text + "\n")
    return code


def register(sub):
    parser = sub.add_parser("brief", help="design brief to paste into Claude Design (WP-13)")
    parser.add_argument("slug")
    parser.add_argument("--store")
    parser.set_defaults(func=run)
