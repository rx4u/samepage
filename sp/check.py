"""`sp check`: validate a store against schema/fields.json (US-13, ADR-0007).

This is the only reader allowed to walk the whole store (guardrails.md). It
never runs at boot or recall. Exit 0 when there are no errors, 1 otherwise.
Warnings never fail the check.
"""
import datetime
import os
import re
import sys

from . import MAX_ROWS_PER_READ, SCHEMA_VERSION
from .frontmatter import FrontmatterError, parse
from .schema import load

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
BOOT_MAX_CHARS = 8000
PROJECT_SECTION_MAX_CHARS = 6000
MAX_ACTIVE_RULES = 50
WARN_RULES_PER_SURFACE = 20
RESERVED_PROJECT = "general"
SKIP_DIRS = {".git", ".github", "index", "index.tmp", "node_modules"}
ROOT_FILES_ALLOWED = {"README.md", "LICENSE", ".gitignore"}

SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
    ("API secret key", re.compile(r"\bsk-(ant-|proj-|live_|test_)?[A-Za-z0-9_-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]
CARD_RE = re.compile(r"(?<![\w-])(?:\d[ -]?){12,18}\d(?![\w-])")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.counts = {}
        self.sizes = {}

    def error(self, path, field, problem):
        self.errors.append((path, field, problem))

    def warn(self, path, field, problem):
        self.warnings.append((path, field, problem))


def _luhn(digits):
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def scan_secrets(text):
    """Return a list of secret kinds found in text."""
    found = [name for name, pattern in SECRET_PATTERNS if pattern.search(text)]
    for match in CARD_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19 and _luhn(digits) and len(set(digits)) > 1:
            found.append("card-like number")
            break
    return found


def _parse_datetime(value):
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("missing time zone")
    return parsed


def _check_type(field, value):
    """Return an error string or None."""
    kind = field["type"]
    if kind == "list":
        if not isinstance(value, list):
            return "must be an inline list like [a, b]"
        pattern = field.get("item_pattern")
        for item in value:
            if not isinstance(item, str) or (pattern and not re.match(pattern, item)):
                return "item %r must be a lowercase kebab slug" % (item,)
        return None
    if isinstance(value, list):
        return "lists are only allowed for tags"
    try:
        if kind == "uuid" and not UUID_RE.match(value):
            return "must be a lowercase uuid"
        if kind == "integer":
            int(value)
        elif kind == "number":
            float(value)
        elif kind == "boolean" and value not in ("true", "false"):
            return "must be true or false"
        elif kind == "date":
            datetime.date.fromisoformat(value)
        elif kind == "datetime":
            _parse_datetime(value)
    except ValueError:
        names = {"integer": "a whole number", "number": "a number", "date": "an ISO date like 2026-11-06",
                 "datetime": "an ISO date-time with a time zone like 2026-11-06T09:30:00Z"}
        return "must be %s" % names.get(kind, kind)
    if "max_length" in field and len(value) > field["max_length"]:
        return "is %d characters, maximum %d" % (len(value), field["max_length"])
    if "pattern" in field and not re.match(field["pattern"], value):
        return "must match %s" % field["pattern"]
    return None


def _id8(row):
    value = row.get("id")
    return value[:8] if isinstance(value, str) else None


def _date_part(value):
    try:
        return _parse_datetime(value).date().isoformat()
    except (ValueError, AttributeError):
        return None


def _expected_name(table, row):
    """Return the expected relative path for a row, or None if it cannot be computed."""
    project = row.get("project")
    if table == "project":
        return "projects/%s.md" % row.get("slug")
    if table == "tag":
        return "tags/%s.md" % row.get("slug")
    if table in ("profile_link", "preference", "handoff"):
        folder = {"profile_link": "profile/links", "preference": "rules", "handoff": "handoffs"}[table]
        return "%s/%s.md" % (folder, _id8(row))
    if table == "design_asset":
        return "design/%s/%s.md" % (project, _id8(row))
    if table == "ship_event":
        day = _date_part(row.get("occurred_at"))
        if not day:
            return None
        return "events/%s/%s-%s-%s.md" % (day[:4], day, project, _id8(row))
    if table == "decision":
        day = _date_part(row.get("decided_at"))
        if not day:
            return None
        return "decisions/%s/%s-%s.md" % (project, day, _id8(row))
    return None


def _table_for(rel):
    parts = rel.split("/")
    if rel == "store.md":
        return "store_meta"
    if rel == "profile.md":
        return "profile"
    if len(parts) == 3 and parts[0] == "profile" and parts[1] == "links":
        return "profile_link"
    if len(parts) == 2:
        return {"rules": "preference", "tags": "tag", "projects": "project", "handoffs": "handoff"}.get(parts[0])
    if len(parts) == 3:
        return {"events": "ship_event", "decisions": "decision", "design": "design_asset"}.get(parts[0])
    return None


def _walk(store):
    for dirpath, dirnames, filenames in os.walk(store):
        rel_dir = os.path.relpath(dirpath, store)
        top = rel_dir.split(os.sep)[0]
        if top in SKIP_DIRS:
            dirnames[:] = []
            continue
        dirnames[:] = sorted(d for d in dirnames if not (rel_dir == "." and d in SKIP_DIRS))
        for name in sorted(filenames):
            rel = os.path.normpath(os.path.join(rel_dir, name)).replace(os.sep, "/")
            yield rel, os.path.join(dirpath, name)


def _validate_row(table, spec, lookups, rel, fields, body, report):
    keys = {k["key"]: k for k in spec["keys"]}
    row = {}
    for key, value in fields.items():
        if key not in keys:
            report.error(rel, key, "unknown key (allowed: %s)" % ", ".join(k for k in keys if not keys[k].get("in_body")))
            continue
        field = keys[key]
        if field.get("in_body"):
            report.error(rel, key, "belongs in the Markdown body, not frontmatter")
            continue
        if value is None or value == "":
            continue
        if field["type"] == "lookup":
            allowed = lookups[field["lookup"]]
            if value not in allowed:
                report.error(rel, key, "%r is not allowed (allowed: %s)" % (value, ", ".join(allowed)))
                continue
        elif field["type"] == "ref":
            problem = _check_type({"type": "uuid"}, value) if field["ref_by"] == "id" else _check_type(
                {"type": "text", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"}, value)
            if problem:
                report.error(rel, key, problem)
                continue
        else:
            problem = _check_type(field, value)
            if problem:
                report.error(rel, key, problem)
                continue
        row[key] = value
    for key, field in keys.items():
        if field.get("in_body"):
            text = body.strip()
            if text:
                if "max_length" in field and len(text) > field["max_length"]:
                    report.error(rel, key, "body is %d characters, maximum %d" % (len(text), field["max_length"]))
                row[key] = text
            elif field["required"]:
                report.error(rel, key, "required, write it as the Markdown body")
            continue
        if field["required"] and fields.get(key) in (None, ""):
            report.error(rel, key, "required field is missing or empty")
    return row


def _cross_checks(rows, report):
    ids = {}
    for table, items in rows.items():
        for rel, row in items:
            value = row.get("id")
            if value:
                if value in ids:
                    report.error(rel, "id", "duplicate id, also in %s" % ids[value])
                else:
                    ids[value] = rel
    slugs = {row.get("slug") for _, row in rows.get("project", [])}
    tag_slugs = {row.get("slug") for _, row in rows.get("tag", [])}
    decision_ids = {row.get("id") for _, row in rows.get("decision", [])}
    for table, items in rows.items():
        for rel, row in items:
            if "project" in row and row["project"] not in slugs:
                report.error(rel, "project", "no project with slug %r" % row["project"])
            expected = _expected_name(table, row)
            if expected and expected != rel:
                report.error(rel, "path", "file should be at %s" % expected)
    for rel, row in rows.get("project", []):
        for tag in row.get("tags") or []:
            if tag not in tag_slugs:
                report.error(rel, "tags", "no tag file tags/%s.md" % tag)
    for rel, row in rows.get("decision", []):
        target = row.get("superseded_by")
        if target and target not in decision_ids:
            report.error(rel, "superseded_by", "no decision with id %s" % target)
        if target and row.get("status") != "superseded":
            report.error(rel, "status", "must be superseded when superseded_by is set")
    for rel, row in rows.get("handoff", []):
        if row.get("to_surface") == "design":
            report.error(rel, "to_surface", "design cannot read the store in v1 (ADR-0011, B7)")
    if rows.get("project") is not None and RESERVED_PROJECT not in slugs:
        report.error("projects/%s.md" % RESERVED_PROJECT, "slug", "reserved project %r is missing (B2)" % RESERVED_PROJECT)
    active = [(rel, row) for rel, row in rows.get("preference", []) if row.get("is_active", "true") == "true"]
    if len(active) > MAX_ACTIVE_RULES:
        report.error("rules/", "is_active", "%d active rules, maximum %d (B3)" % (len(active), MAX_ACTIVE_RULES))
    per_surface = {}
    for _, row in active:
        per_surface[row.get("surface") or "all"] = per_surface.get(row.get("surface") or "all", 0) + 1
    for surface, count in sorted(per_surface.items()):
        effective = count + (per_surface.get("all", 0) if surface != "all" else 0)
        if effective > WARN_RULES_PER_SURFACE:
            report.warn("rules/", "surface", "%d active rules apply to %s, recommended %d or fewer"
                        % (effective, surface, WARN_RULES_PER_SURFACE))


def _check_index(store, report):
    for folder, limit in (("boot", BOOT_MAX_CHARS), ("project", PROJECT_SECTION_MAX_CHARS)):
        path = os.path.join(store, "index", folder)
        if not os.path.isdir(path):
            continue
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            with open(full, encoding="utf-8") as handle:
                size = len(handle.read())
            rel = "index/%s/%s" % (folder, name)
            if folder == "boot":
                report.sizes[name[:-3]] = size
            if size > limit:
                report.error(rel, "size", "%d characters, maximum %d" % (size, limit))


def check_store(store, schema_dir=None, only=None, check_index=True):
    fields_spec, lookups = load(schema_dir) if schema_dir else load()
    tables = fields_spec["tables"]
    report = Report()
    rows = {}
    entity_of = {table: spec["entity"] for table, spec in tables.items()}
    if only and only not in entity_of.values():
        raise ValueError("unknown entity %r (choose from %s)" % (only, ", ".join(sorted(entity_of.values()))))
    for rel, full in _walk(store):
        try:
            with open(full, encoding="utf-8") as handle:
                text = handle.read()
        except UnicodeDecodeError:
            report.error(rel, "file", "not UTF-8 text")
            continue
        for kind in scan_secrets(text):
            report.error(rel, "content", "looks like a %s; secrets never go in a store (ADR-0007)" % kind)
        table = _table_for(rel)
        if table is None:
            if rel not in ROOT_FILES_ALLOWED and not rel.endswith(".gitkeep"):
                report.warn(rel, "path", "not a store file; ignored")
            continue
        try:
            fields, body = parse(text)
        except FrontmatterError as exc:
            report.error(rel, exc.field or "frontmatter", str(exc))
            continue
        row = _validate_row(table, tables[table], lookups, rel, fields, body, report)
        rows.setdefault(table, []).append((rel, row))
        report.counts[entity_of[table]] = report.counts.get(entity_of[table], 0) + 1
    if True:
        meta = dict(rows.get("store_meta", [(None, {})])[0][1]) if rows.get("store_meta") else None
        if meta is None:
            report.error("store.md", "file", "missing; every store needs store.md")
        else:
            version = meta.get("schema_version", "")
            if version.split(".")[0] != SCHEMA_VERSION.split(".")[0]:
                report.error("store.md", "schema_version", "%r is not readable by this sp (major %s)"
                             % (version, SCHEMA_VERSION.split(".")[0]))
        if not rows.get("profile"):
            report.error("profile.md", "file", "missing; every store needs profile.md")
        for table in ("project", "preference"):
            rows.setdefault(table, [])
        if check_index:
            _check_index(store, report)
    _cross_checks(rows, report)
    if only:
        def keep(item):
            table = _table_for(item[0]) if not item[0].endswith("/") else {"rules/": "preference"}.get(item[0])
            return table is not None and entity_of.get(table) == only
        report.errors = [e for e in report.errors if keep(e)]
        report.warnings = [w for w in report.warnings if keep(w)]
        report.counts = {k: v for k, v in report.counts.items() if k == only}
    return report


def format_report(report, page=1):
    lines = []
    status = "FAIL" if report.errors else "PASS"
    def plural(n, word):
        return "%d %s%s" % (n, word, "" if n == 1 else "s")
    lines.append("sp check: %s (%s, %s)" % (status, plural(len(report.errors), "error"), plural(len(report.warnings), "warning")))
    if report.counts:
        lines.append("counts: " + ", ".join("%s %d" % (k, v) for k, v in sorted(report.counts.items())))
    if report.sizes:
        lines.append("boot size (chars): " + ", ".join("%s %d" % (k, v) for k, v in sorted(report.sizes.items())))
    start = (page - 1) * MAX_ROWS_PER_READ
    shown = report.errors[start:start + MAX_ROWS_PER_READ]
    if shown:
        lines.append("errors:")
        lines.extend("  %s: %s: %s" % item for item in shown)
        remaining = len(report.errors) - start - len(shown)
        if remaining > 0:
            lines.append("  %d more, run with --page %d" % (remaining, page + 1))
    if report.warnings and page == 1:
        lines.append("warnings:")
        lines.extend("  %s: %s: %s" % item for item in report.warnings[:MAX_ROWS_PER_READ])
    return "\n".join(lines)


def run(store, only=None, page=1):
    if not os.path.isdir(store):
        print("sp check: %s is not a folder" % store, file=sys.stderr)
        return 2
    try:
        report = check_store(store, only=only)
    except ValueError as exc:
        print("sp check: %s" % exc, file=sys.stderr)
        return 2
    print(format_report(report, page=max(1, page)))
    return 1 if report.errors else 0
