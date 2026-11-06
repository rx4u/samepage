"""`sp export --from-notion-csv DIR --out STORE`: Notion store to GitHub layout.

Reads a Notion "Markdown & CSV" export (with subpages) of the eight samepage
databases and writes a GitHub store that passes `sp check` (ADR-0002). It
never calls Notion and never handles credentials (ADR-0006): the user exports the
page in the Notion UI and points this command at the unzipped folder.

Notion CSV quirks handled: UTF-8 BOM, `Name <32 hex>` file and folder names,
`_all.csv` variants (preferred), relation cells as page titles, as
`Title (https://notion URL)` or as bare URLs, multi-select as comma lists,
dates like `November 6, 2026 9:30 AM` (optional `(GMT+5:30)` or `(UTC)`),
`YYYY/MM/DD`, `MM/DD/YYYY` and ISO, ranges with an arrow (start kept),
checkbox `Yes`/`No`, empty cells. Page bodies (decision and handoff bodies,
the profile's long bio) come from the page Markdown files, matched by the
`UUID:` property line.

The output folder must not exist. The store is assembled in a temporary
folder next to it, checked with `sp check`, and only then renamed into place.
"""
import csv
import datetime
import io
import os
import re
import shutil
import sys
import tempfile
import uuid

from . import SCHEMA_VERSION
from .check import check_store, format_report
from .frontmatter import emit

DATABASES = ("Profile", "Links", "Rules", "Projects", "Ship Events", "Decisions", "Design Assets", "Handoffs")
HEX_SUFFIX = re.compile(r"\s+[0-9a-f]{32}$")
HEX_ID = re.compile(r"([0-9a-f]{32})(?:[^0-9a-f]|$)")
NOTION_LINK = re.compile(r"([^,()]*?)\s*\((https?://[^)\s]*notion\.(?:so|site|com)[^)\s]*)\)")
BARE_LINK = re.compile(r"https?://[^\s,]*notion\.(?:so|site|com)[^\s,]*")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
ZONE_RE = re.compile(r"\s*\((?:GMT|UTC)\s*(?:([+-])(\d{1,2})(?::(\d{2}))?)?\)\s*$")
NAMESPACE = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")  # RFC 4122 URL namespace
DATE_FORMATS = ("%B %d, %Y", "%b %d, %Y", "%Y/%m/%d", "%m/%d/%Y", "%Y-%m-%d", "%d %B %Y")
TIME_FORMATS = ("%I:%M %p", "%H:%M", "%I:%M:%S %p", "%H:%M:%S")


class ExportError(ValueError):
    """A problem in the Notion export that stops the conversion."""


# ----- reading the export folder (a Notion export, not a store; see guardrails note in the report)
def _files(folder):
    """Yield every file path under folder, sorted, using os.scandir."""
    stack = [folder]
    found = []
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    stack.append(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    found.append(entry.path)
    return sorted(found)


def _base_name(path):
    name = os.path.splitext(os.path.basename(path))[0]
    all_variant = name.endswith("_all")
    if all_variant:
        name = name[:-4]
    return HEX_SUFFIX.sub("", name).strip(), all_variant


def _read_text(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def _read_csv(path):
    reader = csv.DictReader(io.StringIO(_read_text(path)))
    rows = []
    for row in reader:
        rows.append({(k or "").strip().lstrip("﻿"): (v or "").strip() for k, v in row.items() if k is not None})
    return rows


def _parse_page(path):
    """Return (title, properties, body, hex id) from a Notion page Markdown file."""
    lines = _read_text(path).replace("\r\n", "\n").split("\n")
    title = ""
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].startswith("# "):
        title = lines[i][2:].strip()
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    props = {}
    start = i
    while i < len(lines) and lines[i].strip():
        match = re.match(r"^([^:]{1,60}):\s?(.*)$", lines[i])
        if not match:
            break
        props[match.group(1).strip()] = match.group(2).strip()
        i += 1
    if not props:
        i = start
    body = "\n".join(lines[i:]).strip()
    found = HEX_ID.search(os.path.basename(path))
    return title, props, body, found.group(1) if found else None


def read_export(folder):
    """Return {database: {"rows": [...], "pages": [...]}} for the eight databases."""
    if not os.path.isdir(folder):
        raise ExportError("%s is not a folder (unzip the Notion export first)" % folder)
    csvs = {}
    pages = {name: [] for name in DATABASES}
    for path in _files(folder):
        if path.endswith(".csv"):
            name, all_variant = _base_name(path)
            if name in DATABASES and (name not in csvs or all_variant):
                csvs[name] = path
        elif path.endswith(".md"):
            parent, _ = _base_name(os.path.dirname(path))
            if parent in DATABASES:
                pages[parent].append(_parse_page(path))
    missing = [name for name in DATABASES if name not in csvs]
    if missing:
        raise ExportError("no CSV for %s; export the page that holds the eight databases with "
                          "Markdown & CSV and Include subpages" % ", ".join(missing))
    return {name: {"rows": _read_csv(csvs[name]), "pages": pages[name]} for name in DATABASES}


# ----- value conversion
def _offset(text):
    match = re.match(r"^([+-])(\d{2}):?(\d{2})$", text.strip())
    if not match:
        raise ExportError("utc offset %r must look like +05:30" % text)
    sign = 1 if match.group(1) == "+" else -1
    return datetime.timezone(sign * datetime.timedelta(hours=int(match.group(2)), minutes=int(match.group(3))))


def parse_when(value, zone=datetime.timezone.utc):
    """Return (aware datetime, has_time) for a Notion CSV date cell, or None if empty."""
    text = (value or "").strip()
    if not text:
        return None
    text = re.split(r"\s*(?:→|->)\s*", text)[0].strip()
    match = ZONE_RE.search(text)
    if match:
        if match.group(1):
            sign = 1 if match.group(1) == "+" else -1
            zone = datetime.timezone(sign * datetime.timedelta(hours=int(match.group(2)), minutes=int(match.group(3) or 0)))
        else:
            zone = datetime.timezone.utc
        text = text[:match.start()].strip()
    iso = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.datetime.fromisoformat(iso)
        has_time = len(text) > 10
        return (parsed if parsed.tzinfo else parsed.replace(tzinfo=zone)), has_time
    except ValueError:
        pass
    for date_format in DATE_FORMATS:
        for time_format in (None,) + TIME_FORMATS:
            pattern = date_format if time_format is None else date_format + " " + time_format
            try:
                parsed = datetime.datetime.strptime(text, pattern)
            except ValueError:
                continue
            return parsed.replace(tzinfo=zone), time_format is not None
    raise ExportError("cannot read date %r" % value)


def iso_datetime(value, zone):
    parsed = parse_when(value, zone)
    if parsed is None:
        return None
    moment = parsed[0].astimezone(datetime.timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_date(value, zone):
    parsed = parse_when(value, zone)
    if parsed is None:
        return None
    return parsed[0].date().isoformat()


def checkbox(value):
    text = (value or "").strip().lower()
    if text in ("yes", "true", "checked", "1", "__yes__"):
        return "true"
    if text in ("", "no", "false", "unchecked", "0", "__no__"):
        return "false"
    raise ExportError("checkbox value %r is not Yes or No" % value)


def number(value):
    text = (value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        raise ExportError("number value %r is not a number" % value)
    return str(int(parsed)) if parsed.is_integer() else repr(parsed)


def multi(value):
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug or "untitled"


def plain_url(value):
    """Notion sometimes writes URL cells as Markdown links; keep the target."""
    text = (value or "").strip()
    match = re.match(r"^\[[^\]]*\]\(([^)]+)\)$", text)
    return match.group(1) if match else (text or None)


def stable_id(*parts):
    return str(uuid.uuid5(NAMESPACE, "samepage:" + ":".join(parts)))


# ----- relations
class Resolver:
    """Maps a relation cell (titles, `Title (url)` or bare URLs) to target rows."""

    def __init__(self, name, rows, title_key, pages):
        self.name = name
        self.by_title = {}
        for row in rows:
            self.by_title.setdefault(row.get(title_key, ""), []).append(row)
        by_uuid = {row.get("UUID"): row for row in rows if row.get("UUID")}
        self.by_hex = {}
        for title, props, _, hex_id in pages:
            target = by_uuid.get(props.get("UUID")) if props.get("UUID") else None
            if target is None and len(self.by_title.get(title, [])) == 1:
                target = self.by_title[title][0]
            if hex_id and target is not None:
                self.by_hex[hex_id] = target

    def _one(self, title, hex_id, where):
        if hex_id and hex_id in self.by_hex:
            return self.by_hex[hex_id]
        matches = self.by_title.get(title.strip(), [])
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise ExportError("%s: no %s row titled %r" % (where, self.name, title))
        raise ExportError("%s: %d %s rows are titled %r; include page files so the link can be matched"
                          % (where, len(matches), self.name, title))

    def resolve(self, cell, where):
        text = (cell or "").strip()
        if not text:
            return []
        found = NOTION_LINK.findall(text)
        if found:
            return [self._one(title, self._hex(url), where) for title, url in found]
        links = BARE_LINK.findall(text)
        if links:
            return [self._one(self._title_from_url(url), self._hex(url), where) for url in links]
        if text in self.by_title:
            return [self._one(text, None, where)]
        return [self._one(part, None, where) for part in text.split(", ") if part.strip()]

    @staticmethod
    def _hex(url):
        found = re.findall(r"[0-9a-f]{32}", url.replace("-", ""))
        return found[-1] if found else None

    @staticmethod
    def _title_from_url(url):
        last = url.rstrip("/").split("/")[-1].split("?")[0]
        return re.sub(r"-?[0-9a-f]{32}$", "", last).replace("-", " ")


# ----- conversion
def _need(row, key, where):
    value = row.get(key, "").strip()
    if not value:
        raise ExportError("%s: %s is empty" % (where, key))
    return value


def _body_for(pages, row):
    wanted = row.get("UUID")
    for title, props, body, _ in pages:
        if wanted and props.get("UUID") == wanted:
            return body
    titled = [body for title, props, body, _ in pages if title == row.get("_title")]
    return titled[0] if len(titled) == 1 else None


def convert(data, zone=datetime.timezone.utc, now=None):
    """Return {relative path: file text} for a GitHub store built from the export data."""
    now = now or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files = {}

    def when(row, key, fallback=None):
        return iso_datetime(row.get(key), zone) or fallback

    profiles = data["Profile"]["rows"]
    if len(profiles) != 1:
        raise ExportError("Profile must have exactly one row, found %d" % len(profiles))
    profile = profiles[0]
    profile_created = when(profile, "Created", now)
    profile_updated = when(profile, "Updated", profile_created)
    files["store.md"] = emit({
        "schema_version": profile.get("Schema version") or SCHEMA_VERSION,
        "backend": "github",
        "owner_handle": _need(profile, "Owner handle", "Profile"),
        "created_at": profile_created,
        "updated_at": profile_updated,
    })
    profile["_title"] = profile.get("Name", "")
    long_bio = _body_for(data["Profile"]["pages"], profile)
    files["profile.md"] = emit({
        "display_name": _need(profile, "Name", "Profile"),
        "headline": _need(profile, "Headline", "Profile"),
        "location": profile.get("Location") or None,
        "bio": profile.get("Bio") or None,
        "voice": profile.get("Voice") or None,
        "created_at": profile_created,
        "updated_at": profile_updated,
    }, long_bio or "")

    for index, row in enumerate(data["Links"]["rows"]):
        where = "Links row %d" % (index + 1)
        link_id = row.get("UUID") or stable_id("link", row.get("Label", ""), str(index))
        files["profile/links/%s.md" % link_id[:8]] = emit({
            "id": link_id,
            "label": _need(row, "Label", where),
            "url": plain_url(_need(row, "Link", where)),
            "sort_order": number(row.get("Order")) or str(index + 1),
            "created_at": when(row, "Created", profile_created),
        })

    for index, row in enumerate(data["Rules"]["rows"]):
        where = "Rules row %d" % (index + 1)
        rule_id = row.get("UUID") or stable_id("rule", row.get("Rule", ""), str(index))
        created = when(row, "Created", profile_created)
        files["rules/%s.md" % rule_id[:8]] = emit({
            "id": rule_id,
            "rule": _need(row, "Rule", where),
            "surface": row.get("Surface") or None,
            "is_active": checkbox(row.get("Active")),
            "created_at": created,
            "updated_at": when(row, "Updated", created),
        })

    projects = data["Projects"]["rows"]
    tags = {}
    for index, row in enumerate(projects):
        where = "Projects row %d" % (index + 1)
        row["_slug"] = row.get("Slug") or slugify(_need(row, "Name", where))
        if not SLUG_RE.match(row["_slug"]):
            raise ExportError("%s: slug %r must be lowercase words joined by hyphens" % (where, row["_slug"]))
        row["_id"] = row.get("UUID") or stable_id("project", row["_slug"])
    seen = {}
    for row in projects:
        if row["_slug"] in seen:
            raise ExportError("two projects use the slug %r" % row["_slug"])
        seen[row["_slug"]] = row
    project_resolver = Resolver("Projects", projects, "Name", data["Projects"]["pages"])

    for index, row in enumerate(projects):
        where = "Projects row %d" % (index + 1)
        created = when(row, "Created", profile_created)
        updated = when(row, "Updated", created)
        tag_slugs = []
        for label in multi(row.get("Tags")):
            slug = slugify(label)
            entry = tags.setdefault(slug, {"label": label, "created_at": created})
            entry["created_at"] = min(entry["created_at"], created)
            if slug not in tag_slugs:
                tag_slugs.append(slug)
        files["projects/%s.md" % row["_slug"]] = emit({
            "id": row["_id"],
            "slug": row["_slug"],
            "name": _need(row, "Name", where),
            "status": _need(row, "Status", where),
            "type": _need(row, "Type", where),
            "one_liner": _need(row, "One-liner", where),
            "problem": row.get("Problem") or None,
            "role": row.get("Role") or None,
            "outcome": row.get("Outcome") or None,
            "live_url": plain_url(row.get("Live URL")),
            "repo_url": plain_url(row.get("Repo URL")),
            "started_on": iso_date(row.get("Started"), zone),
            "shipped_on": iso_date(row.get("Shipped on"), zone),
            "last_verified_at": when(row, "Last verified", updated),
            "archived_at": when(row, "Archived"),
            "created_at": created,
            "updated_at": updated,
            "tags": tag_slugs,
        })
    for slug, entry in sorted(tags.items()):
        files["tags/%s.md" % slug] = emit({
            "id": stable_id("tag", slug),
            "slug": slug,
            "label": entry["label"],
            "created_at": entry["created_at"],
        })

    def project_of(row, where):
        slug = row.get("Project slug", "").strip()
        if slug:
            if slug not in seen:
                raise ExportError("%s: Project slug %r matches no project" % (where, slug))
            return slug
        targets = project_resolver.resolve(row.get("Project"), where)
        if len(targets) != 1:
            raise ExportError("%s: needs exactly one Project, found %d" % (where, len(targets)))
        return targets[0]["_slug"]

    for index, row in enumerate(data["Ship Events"]["rows"]):
        where = "Ship Events row %d" % (index + 1)
        slug = project_of(row, where)
        event_id = row.get("UUID") or stable_id("event", slug, row.get("Summary", ""), str(index))
        occurred = when(row, "Occurred")
        if not occurred:
            raise ExportError("%s: Occurred is empty" % where)
        files["events/%s/%s-%s-%s.md" % (occurred[:4], occurred[:10], slug, event_id[:8])] = emit({
            "id": event_id,
            "project": slug,
            "kind": _need(row, "Kind", where),
            "surface": _need(row, "Surface", where),
            "tool": row.get("Tool") or None,  # schema 1.1 (ADR-0017)
            "summary": _need(row, "Summary", where),
            "proof_url": plain_url(row.get("Proof URL")),
            "metric_label": row.get("Metric label") or None,
            "metric_value": number(row.get("Metric value")),
            "metric_unit": row.get("Metric unit") or None,
            "occurred_at": occurred,
            "created_at": when(row, "Created", occurred),
        })

    decisions = data["Decisions"]["rows"]
    for index, row in enumerate(decisions):
        row["_id"] = row.get("UUID") or stable_id("decision", row.get("Title", ""), str(index))
        row["_title"] = row.get("Title", "")
    decision_resolver = Resolver("Decisions", decisions, "Title", data["Decisions"]["pages"])
    for index, row in enumerate(decisions):
        where = "Decisions row %d" % (index + 1)
        slug = project_of(row, where)
        decided = when(row, "Decided")
        if not decided:
            raise ExportError("%s: Decided is empty" % where)
        created = when(row, "Created", decided)
        successors = decision_resolver.resolve(row.get("Superseded by"), where)
        if len(successors) > 1:
            raise ExportError("%s: Superseded by holds %d decisions, at most 1" % (where, len(successors)))
        files["decisions/%s/%s-%s.md" % (slug, decided[:10], row["_id"][:8])] = emit({
            "id": row["_id"],
            "project": slug,
            "status": _need(row, "Status", where),
            "surface": _need(row, "Surface", where),
            "tool": row.get("Tool") or None,  # schema 1.1 (ADR-0017)
            "superseded_by": successors[0]["_id"] if successors else None,
            "title": _need(row, "Title", where),
            "reason": _need(row, "Reason", where),
            "decided_at": decided,
            "created_at": created,
            "updated_at": when(row, "Updated", created),
        }, _body_for(data["Decisions"]["pages"], row) or "")

    for index, row in enumerate(data["Design Assets"]["rows"]):
        where = "Design Assets row %d" % (index + 1)
        slug = project_of(row, where)
        asset_id = row.get("UUID") or stable_id("design", slug, row.get("Title", ""), str(index))
        created = when(row, "Created", profile_created)
        files["design/%s/%s.md" % (slug, asset_id[:8])] = emit({
            "id": asset_id,
            "project": slug,
            "kind": _need(row, "Kind", where),
            "status": _need(row, "Status", where),
            "surface": _need(row, "Surface", where),
            "tool": row.get("Tool") or None,  # schema 1.1 (ADR-0017)
            "title": _need(row, "Title", where),
            "source_url": plain_url(row.get("Source URL")),
            "tokens_repo_url": plain_url(row.get("Tokens repo URL")),
            "tokens_path": row.get("Tokens path") or None,
            "created_at": created,
            "updated_at": when(row, "Updated", created),
        })

    for index, row in enumerate(data["Handoffs"]["rows"]):
        where = "Handoffs row %d" % (index + 1)
        slug = project_of(row, where)
        row["_title"] = row.get("Title", "")
        handoff_id = row.get("UUID") or stable_id("handoff", slug, row["_title"], str(index))
        body = _body_for(data["Handoffs"]["pages"], row)
        if not body:
            raise ExportError("%s: no page file with a body; export with Include subpages" % where)
        files["handoffs/%s.md" % handoff_id[:8]] = emit({
            "id": handoff_id,
            "project": slug,
            "from_surface": _need(row, "From", where),
            "from_tool": row.get("From tool") or None,  # schema 1.1 (ADR-0017)
            "to_surface": _need(row, "To", where),
            "status": _need(row, "Status", where),
            "title": _need(row, "Title", where),
            "created_at": when(row, "Created", profile_created),
            "picked_up_at": when(row, "Picked up"),
            "done_at": when(row, "Done"),
        }, body)
    for path, text in files.items():
        if not path.endswith(".md"):
            raise ExportError("internal: bad path %s" % path)
        files[path] = _drop_empty_since(text)
    return files


def _drop_empty_since(text):
    """Schema 1.1 keys (tool, from_tool) are left out when empty, so a 1.0 store stays readable by an
    older sp (B23)."""
    return "".join(line for line in text.splitlines(True) if line not in ("tool:\n", "from_tool:\n"))


def export(source, out, utc_offset="+00:00", now=None):
    """Convert and write. Returns (ok, message). Never writes into an existing path."""
    out = os.path.abspath(out)
    if os.path.lexists(out):
        return False, "%s already exists; choose a new folder" % out
    zone = _offset(utc_offset)
    try:
        files = convert(read_export(source), zone=zone, now=now)
    except ExportError as exc:
        return False, str(exc)
    parent = os.path.dirname(out)
    os.makedirs(parent, exist_ok=True)
    staging = tempfile.mkdtemp(prefix=".sp-export-", dir=parent)
    try:
        for rel, text in sorted(files.items()):
            path = os.path.join(staging, *rel.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        report = check_store(staging)
        if report.errors:
            return False, "export did not pass sp check, nothing written:\n" + format_report(report)
        os.rename(staging, out)
        staging = None
    finally:
        if staging:
            shutil.rmtree(staging, ignore_errors=True)
    return True, "samepage: exported %d entries to %s" % (len(files), out)


def run(source, out, utc_offset="+00:00"):
    ok, message = export(source, out, utc_offset=utc_offset)
    print(message, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1
