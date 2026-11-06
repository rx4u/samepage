"""`sp index`: build the serve layer under index/ (ADR-0004, ADR-0005).

Every serve file starts with `built: {time} from {sha8} schema {version}`.
Lists are pre-sorted pages of 20 rows (tag pages 50), sorted by the screen's
key DESC then id DESC; a `next: {path}` footer is the cursor. Boot files are
fitted to their character budgets by trimming the lowest-priority sections.
The index is only built from a store that passes `sp check`; on failure the
old index stays and the failure is recorded in index/builds.md.
"""
import datetime
import os
import shutil
import sys
import time

from . import DEFAULT_PAGE_SIZE, MAX_ROWS_PER_READ, SCHEMA_VERSION
from .check import BOOT_MAX_CHARS, PROJECT_SECTION_MAX_CHARS, RESERVED_PROJECT, check_store
from .check import _table_for, _walk
from .frontmatter import parse
from .schema import load as load_schema

# ----- store loading (only check.py and index.py may walk raw folders, guardrails.md)
def to_time(value):
    """Parse an ISO date-time with a zone into an aware datetime (UTC on Z)."""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.datetime.fromisoformat(text)


def load(store):
    fields_spec, _ = load_schema()
    tables = fields_spec["tables"]
    rows = {table: [] for table in tables}
    for rel, full in _walk(store):
        table = _table_for(rel)
        if table is None:
            continue
        with open(full, encoding="utf-8") as handle:
            fields, body = parse(handle.read())
        row = {k: v for k, v in fields.items() if v not in (None, "")}
        for key in tables[table]["keys"]:
            if key.get("in_body"):
                text = body.strip()
                if text:
                    row[key["key"]] = text
        row["_path"] = rel
        rows[table].append(row)
    return rows


def git_head(store):
    """Return the store's HEAD commit sha, or None when it is not a git repo."""
    head = os.path.join(store, ".git", "HEAD")
    if not os.path.isfile(head):
        return None
    with open(head, encoding="utf-8") as handle:
        ref = handle.read().strip()
    if not ref.startswith("ref:"):
        return ref
    ref_path = os.path.join(store, ".git", ref[5:].strip())
    if os.path.isfile(ref_path):
        with open(ref_path, encoding="utf-8") as handle:
            return handle.read().strip()
    packed = os.path.join(store, ".git", "packed-refs")
    if os.path.isfile(packed):
        with open(packed, encoding="utf-8") as handle:
            for line in handle:
                parts = line.strip().split(" ")
                if len(parts) == 2 and parts[1] == ref[5:].strip():
                    return parts[0]
    return None


BOOT_SURFACES = ("code", "chat", "cowork")
TAG_PAGE_SIZE = MAX_ROWS_PER_READ
BUILD_HISTORY = 50
EPOCH = "1970-01-01T00:00:00Z"


def clip(text, limit):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def newest_first(rows, key):
    return sorted(rows, key=lambda r: (to_time(r.get(key) or EPOCH), r.get("id", r.get("slug", ""))), reverse=True)


def oldest_first(rows, key):
    return sorted(rows, key=lambda r: (to_time(r.get(key) or EPOCH), r.get("id", "")))


def day(value):
    return to_time(value).date().isoformat() if value else "?"


class Index:
    def __init__(self, rows, built, sha):
        self.rows = rows
        self.header = "built: %s from %s schema %s" % (built, (sha or "nogit")[:8], SCHEMA_VERSION)
        self.files = {}
        projects = rows["project"]
        self.projects = {p["slug"]: p for p in projects}
        self.listed = [p for p in projects if p["slug"] != RESERVED_PROJECT]
        self.events_by_project = {}
        for event in newest_first(rows["ship_event"], "occurred_at"):
            self.events_by_project.setdefault(event["project"], []).append(event)

    # ----- helpers
    def page_files(self, base, lines_per_row, size, extra_header=""):
        total = len(lines_per_row)
        pages = [lines_per_row[i:i + size] for i in range(0, total, size)] or [[]]
        names = [base % 1 if n == 0 else base % (n + 1) for n in range(len(pages))]
        if "%d" not in base:
            raise ValueError(base)
        for n, rows in enumerate(pages):
            out = [self.header, "total: %d%s" % (total, extra_header), ""]
            for row in rows:
                out.extend(row)
            if n + 1 < len(pages):
                out += ["", "next: %s" % names[n + 1]]
            self.files[names[n]] = "\n".join(out).rstrip() + "\n"

    def proof_row(self, project):
        events = self.events_by_project.get(project["slug"], [])
        latest = events[0]
        proof = next((e["proof_url"] for e in events if e.get("proof_url")), None) or project.get("live_url")
        metric = next((e for e in events if e.get("metric_value") is not None and e.get("metric_label")), None)
        lines = ["- %s (%s) [%s, %s]: %s" % (project["name"], project["slug"], project["status"], project["type"],
                                             clip(project["one_liner"], 140))]
        lines.append("  latest: %s %s: %s" % (day(latest["occurred_at"]), latest["kind"], clip(latest["summary"], 200)))
        if project.get("role"):
            lines.append("  role: %s" % clip(project["role"], 120))
        if project.get("outcome"):
            lines.append("  outcome: %s" % clip(project["outcome"], 160))
        if metric:
            lines.append("  metric: %s %s %s" % (metric["metric_label"], metric["metric_value"], metric.get("metric_unit", "")))
        lines.append("  proof: %s" % (proof or "no public proof yet"))
        return lines

    def shipped_projects(self):
        shipped = [p for p in self.listed if p["slug"] in self.events_by_project]
        return sorted(shipped, key=lambda p: (to_time(self.events_by_project[p["slug"]][0]["occurred_at"]), p["id"]),
                      reverse=True)

    # ----- serve files
    def build_lists(self):
        rows = [["- %s: %s [%s, %s] %s (updated %s)" % (p["slug"], p["name"], p["status"], p["type"],
                                                         clip(p["one_liner"], 140), day(p["updated_at"]))]
                for p in newest_first(self.listed, "updated_at")]
        self.page_files("index/projects-%d.md", rows, DEFAULT_PAGE_SIZE)
        shipped = self.shipped_projects()
        self.page_files("index/proof-%d.md", [self.proof_row(p) for p in shipped], DEFAULT_PAGE_SIZE)
        tagged = {}
        for p in shipped:
            for tag in p.get("tags") or []:
                tagged.setdefault(tag, []).append(p)
        for tag in self.rows["tag"]:
            items = tagged.get(tag["slug"], [])
            base = "index/tags/%s" % tag["slug"]
            self.page_files(base + "-%d.md", [self.proof_row(p) for p in items], TAG_PAGE_SIZE,
                            extra_header="\ntag: %s" % tag["label"])
            # The first tag page is named tags/{slug}.md (read-models.md).
            first = self.files.pop(base + "-1.md")
            self.files[base + ".md"] = first
            for name in list(self.files):
                if name.startswith(base + "-"):
                    self.files[name] = self.files[name].replace("next: " + base + "-1.md", "next: " + base + ".md")
        for surface in BOOT_SURFACES:
            items = [h for h in self.rows["handoff"] if h["to_surface"] == surface and h["status"] in ("open", "picked_up")]
            open_count = sum(1 for h in items if h["status"] == "open")
            rows = [["- %s [%s] %s: %s (from %s, %s) file: handoffs/%s.md" % (
                h["id"][:8], h["status"], h["project"], clip(h["title"], 120), h["from_surface"], day(h["created_at"]),
                h["id"][:8])] for h in newest_first(items, "created_at")]
            self.page_files("index/handoffs-" + surface + "-%d.md", rows, DEFAULT_PAGE_SIZE,
                            extra_header="\nopen: %d" % open_count)
        active = self.active_rules()
        out = [self.header, "total: %d" % len(active), ""]
        for surface in [None] + list(BOOT_SURFACES) + ["design"]:
            group = [r for r in active if r.get("surface") == surface]
            if group:
                out.append("## %s" % ("All surfaces" if surface is None else surface))
                out.extend("- %s %s" % (r["id"][:8], clip(r["rule"], 200)) for r in group)
                out.append("")
        self.files["index/rules.md"] = "\n".join(out).rstrip() + "\n"
        repos = sorted((p["repo_url"], p["slug"]) for p in self.rows["project"] if p.get("repo_url"))
        self.files["index/repos.md"] = "\n".join([self.header, "total: %d" % len(repos), ""] +
                                                 ["%s %s" % pair for pair in repos]) + "\n"

    def active_rules(self):
        active = [r for r in self.rows["preference"] if r.get("is_active", "true") == "true"]
        return oldest_first(active, "created_at")[:MAX_ROWS_PER_READ]

    def boot(self, surface):
        profile = self.rows["profile"][0] if self.rows["profile"] else {}
        rules = [r for r in self.active_rules() if r.get("surface") in (None, surface)]
        active = newest_first([p for p in self.listed if p["status"] == "active"], "updated_at")
        events = newest_first([e for e in self.rows["ship_event"] if e["project"] != RESERVED_PROJECT], "occurred_at")
        handoffs = newest_first([h for h in self.rows["handoff"] if h["to_surface"] == surface and h["status"] == "open"],
                                "created_at")
        links = sorted(self.rows["profile_link"], key=lambda l: (int(l["sort_order"]), l["id"]))[:5]
        # Trim levels, applied in order until the file fits (lowest priority first).
        levels = [dict(projects=10, events=5, handoffs=5, liner=140, summary=200),
                  dict(projects=10, events=5, handoffs=5, liner=140, summary=120),
                  dict(projects=10, events=3, handoffs=5, liner=100, summary=120),
                  dict(projects=6, events=3, handoffs=5, liner=80, summary=100),
                  dict(projects=6, events=0, handoffs=5, liner=80, summary=100),
                  dict(projects=3, events=0, handoffs=3, liner=60, summary=100),
                  dict(projects=0, events=0, handoffs=3, liner=60, summary=100)]
        for n, level in enumerate(levels):
            out = [self.header, "surface: %s" % surface, "", "# samepage context", ""]
            out.append("## Profile")
            if profile:
                out.append("%s. %s" % (profile.get("display_name", ""), clip(profile.get("headline", ""), 200)))
                if surface != "code" and profile.get("location"):
                    out.append("Location: %s" % clip(profile["location"], 80))
                if surface != "code" and profile.get("bio"):
                    out.append("Bio: %s" % clip(profile["bio"], 400))
                if profile.get("voice"):
                    out.append("Voice: %s" % clip(profile["voice"], 300))
                if surface != "code":
                    out.extend("- %s: %s" % (l["label"], l["url"]) for l in links)
            out += ["", "## Rules"]
            out.extend("- %s" % clip(r["rule"], 200) for r in rules[:20])
            if len(rules) > 20:
                out.append("- and %d more in index/rules.md" % (len(rules) - 20))
            out += ["", "## Active projects (%d of %d)" % (min(level["projects"], len(active)), len(active))]
            out.extend("- %s: %s. %s (updated %s)" % (p["slug"], p["name"], clip(p["one_liner"], level["liner"]),
                                                       day(p["updated_at"])) for p in active[:level["projects"]])
            if len(active) > level["projects"]:
                out.append("- full list: index/projects-1.md")
            if surface == "code" and level["events"]:
                out += ["", "## Recent ships"]
                out.extend("- %s %s, %s: %s" % (day(e["occurred_at"]), e["project"], e["kind"],
                                                clip(e["summary"], level["summary"])) for e in events[:level["events"]])
            out += ["", "## Open handoffs to %s (%d)" % (surface, len(handoffs))]
            out.extend("- %s %s: %s (from %s) file: handoffs/%s.md" % (h["id"][:8], h["project"], clip(h["title"], 120),
                                                                       h["from_surface"], h["id"][:8])
                       for h in handoffs[:level["handoffs"]])
            if len(handoffs) > level["handoffs"]:
                out.append("- and %d more in index/handoffs-%s-1.md" % (len(handoffs) - level["handoffs"], surface))
            if n:
                out += ["", "(trimmed to fit the boot budget)"]
            text = "\n".join(out).rstrip() + "\n"
            if len(text) <= BOOT_MAX_CHARS:
                return text
        raise ValueError("boot file for %s cannot fit %d characters" % (surface, BOOT_MAX_CHARS))

    def project_section(self, project):
        slug = project["slug"]
        events = self.events_by_project.get(slug, [])
        decisions = newest_first([d for d in self.rows["decision"] if d["project"] == slug and d["status"] == "accepted"],
                                 "decided_at")
        assets = [a for a in self.rows["design_asset"] if a["project"] == slug and a["status"] != "superseded"]
        assets = sorted(newest_first(assets, "updated_at"), key=lambda a: a["status"] != "approved")
        handoffs = newest_first([h for h in self.rows["handoff"] if h["project"] == slug
                                 and h["status"] in ("open", "picked_up")], "created_at")
        all_decisions = sum(1 for d in self.rows["decision"] if d["project"] == slug)
        levels = [(10, 10, 5, 300, 160), (10, 10, 5, 160, 100), (6, 6, 5, 120, 80), (3, 3, 3, 100, 60), (0, 3, 3, 80, 60)]
        for n, (n_events, n_decisions, n_assets, text_cap, reason_cap) in enumerate(levels):
            out = [self.header, "project: %s" % slug,
                   "counts: events %d, decisions %d, design assets %d" % (len(events), all_decisions, len(assets)), ""]
            out.append("# %s (%s, %s)" % (project["name"], project["status"], project["type"]))
            out.append(clip(project["one_liner"], 140))
            for key in ("problem", "role", "outcome"):
                if project.get(key):
                    out.append("%s: %s" % (key, clip(project[key], text_cap)))
            for key in ("live_url", "repo_url", "started_on", "shipped_on", "archived_at"):
                if project.get(key):
                    out.append("%s: %s" % (key, project[key]))
            if project.get("tags"):
                out.append("tags: %s" % ", ".join(project["tags"]))
            out.append("last verified: %s" % day(project["last_verified_at"]))
            if n_events:
                out += ["", "## Ship events"]
                out.extend("- %s %s: %s%s" % (day(e["occurred_at"]), e["kind"], clip(e["summary"], 200),
                                              " (proof: %s)" % e["proof_url"] if e.get("proof_url") else "")
                           for e in events[:n_events])
            out += ["", "## Decisions in force"]
            out.extend("- %s %s %s: %s" % (day(d["decided_at"]), d["id"][:8], clip(d["title"], 120),
                                           clip(d["reason"], reason_cap)) for d in decisions[:n_decisions])
            out += ["", "## Design"]
            for a in assets[:n_assets]:
                where = ""
                if a.get("tokens_repo_url"):
                    where = " tokens: %s %s" % (a["tokens_repo_url"], a.get("tokens_path", ""))
                if a.get("source_url"):
                    where += " source: %s" % a["source_url"]
                out.append("- %s %s [%s] %s%s" % (a["id"][:8], a["kind"], a["status"], clip(a["title"], 120), where))
            out += ["", "## Open handoffs"]
            out.extend("- %s [%s] to %s: %s file: handoffs/%s.md" % (h["id"][:8], h["status"], h["to_surface"],
                                                                     clip(h["title"], 120), h["id"][:8])
                       for h in handoffs[:5])
            if n:
                out += ["", "(trimmed to fit the project section budget)"]
            text = "\n".join(out).rstrip() + "\n"
            if len(text) <= PROJECT_SECTION_MAX_CHARS:
                return text
        raise ValueError("project section for %s cannot fit %d characters" % (slug, PROJECT_SECTION_MAX_CHARS))

    def build(self):
        self.build_lists()
        for surface in BOOT_SURFACES:
            self.files["index/boot/%s.md" % surface] = self.boot(surface)
        for project in self.rows["project"]:
            self.files["index/project/%s.md" % project["slug"]] = self.project_section(project)
        return self.files


# ----- build history (index/builds.md)

BUILD_COLUMNS = ("started_at", "status", "commit_sha", "entry_count", "boot_chars", "finished_at", "error")


def read_builds(store):
    path = os.path.join(store, "index", "builds.md")
    rows = []
    if not os.path.isfile(path):
        return rows
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.startswith("| ") or line.startswith("| started_at") or line.startswith("|---"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == len(BUILD_COLUMNS):
                rows.append(dict(zip(BUILD_COLUMNS, cells)))
    return rows


def render_builds(rows, header):
    out = [header, "", "| " + " | ".join(BUILD_COLUMNS) + " |", "|" + "---|" * len(BUILD_COLUMNS)]
    for row in rows[:BUILD_HISTORY]:
        out.append("| " + " | ".join(str(row.get(c, "")).replace("|", "/") for c in BUILD_COLUMNS) + " |")
    return "\n".join(out) + "\n"


def _write_index(store, files):
    index_dir = os.path.join(store, "index")
    tmp = os.path.join(store, "index.tmp")
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    for rel, text in files.items():
        path = os.path.join(tmp, os.path.relpath(rel, "index"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    if os.path.isdir(index_dir):
        shutil.rmtree(index_dir)
    os.rename(tmp, index_dir)


def _record_failure(store, row, header):
    index_dir = os.path.join(store, "index")
    os.makedirs(index_dir, exist_ok=True)
    history = [row] + read_builds(store)
    with open(os.path.join(index_dir, "builds.md"), "w", encoding="utf-8") as handle:
        handle.write(render_builds(history, header))


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_index(store, now=None):
    """Check, then rebuild index/. Returns (ok, message, stats)."""
    started = now or now_utc()
    clock = time.monotonic()
    sha = git_head(store)
    header = "built: %s from %s schema %s" % (started, (sha or "nogit")[:8], SCHEMA_VERSION)
    report = check_store(store, check_index=False)
    if report.errors:
        path, field, problem = report.errors[0]
        message = "%d check errors, first: %s: %s: %s" % (len(report.errors), path, field, problem)
        _record_failure(store, {"started_at": started, "status": "failed", "commit_sha": sha or "nogit",
                                "entry_count": "", "boot_chars": "", "finished_at": now or now_utc(),
                                "error": message}, header)
        return False, "sp index: not built, old index kept. " + message, {}
    rows = load(store)
    files = Index(rows, started, sha).build()
    entries = sum(len(v) for v in rows.values())
    boot_chars = max(len(files["index/boot/%s.md" % s]) for s in BOOT_SURFACES)
    history = [{"started_at": started, "status": "succeeded", "commit_sha": sha or "nogit", "entry_count": entries,
                "boot_chars": boot_chars, "finished_at": now or now_utc(), "error": ""}] + read_builds(store)
    files["index/builds.md"] = render_builds(history, header)
    _write_index(store, files)
    seconds = time.monotonic() - clock
    stats = {"files": len(files), "entries": entries, "boot_chars": boot_chars, "seconds": round(seconds, 2)}
    return True, "sp index: built %(files)d files from %(entries)d entries in %(seconds).2fs, largest boot %(boot_chars)d chars" % stats, stats


def run(store, now=None):
    if not os.path.isdir(store):
        print("sp index: %s is not a folder" % store, file=sys.stderr)
        return 2
    ok, message, _ = build_index(store, now=now)
    print(message)
    return 0 if ok else 1
