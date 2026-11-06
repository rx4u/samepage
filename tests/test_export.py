"""Tests for WP-10: sp export --from-notion-csv (Notion CSV export to a GitHub store)."""
import csv
import datetime
import glob
import os
import shutil
import sys
import tempfile
import unittest
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp.__main__ import main  # noqa: E402
from sp.check import check_store  # noqa: E402
from sp.export import ExportError, checkbox, export, multi, number, parse_when, slugify  # noqa: E402
from sp.frontmatter import parse  # noqa: E402
from sp.index import build_index  # noqa: E402

SMALL = os.path.join(ROOT, "fixtures", "small")
NOW = "2026-11-06T06:00:00Z"
LINK_HOST = "https://www.notion.so/"

COLUMNS = {
    "Profile": ["Name", "Backend", "Bio", "Created", "Headline", "Link list", "Links", "Location",
                "Owner handle", "Schema version", "Updated", "Voice"],
    "Links": ["Label", "Created", "Link", "Order", "Profile", "UUID"],
    "Rules": ["Rule", "Active", "Created", "Surface", "UUID", "Updated"],
    "Projects": ["Name", "Archived", "Created", "Decisions", "Design Assets", "Handoffs", "Last shipped",
                 "Last verified", "Live URL", "One-liner", "Outcome", "Problem", "Repo URL", "Role",
                 "Ship Events", "Shipped on", "Slug", "Started", "Status", "Tags", "Type", "UUID", "Updated"],
    "Ship Events": ["Summary", "Created", "Kind", "Metric label", "Metric unit", "Metric value", "Occurred",
                    "Project", "Project slug", "Proof URL", "Surface", "UUID"],
    "Decisions": ["Title", "Created", "Decided", "Project", "Project slug", "Reason", "Status",
                  "Superseded by", "Surface", "UUID", "Updated"],
    "Design Assets": ["Title", "Created", "Kind", "Project", "Project slug", "Source URL", "Status", "Surface",
                      "Tokens path", "Tokens repo URL", "UUID", "Updated"],
    "Handoffs": ["Title", "Created", "Done", "From", "Picked up", "Project", "Project slug", "Status", "To",
                 "UUID"],
}


def hex_for(*parts):
    return uuid.uuid5(uuid.NAMESPACE_URL, "/".join(parts)).hex


def notion_date(value):
    """Format an ISO value the way Notion's CSV export writes it."""
    if not value:
        return ""
    if len(value) == 10:
        day = datetime.date.fromisoformat(value)
        return "%s %d, %d" % (day.strftime("%B"), day.day, day.year)
    moment = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    hour = moment.hour % 12 or 12
    return "%s %d, %d %d:%02d %s" % (moment.strftime("%B"), moment.day, moment.year, hour, moment.minute,
                                     "AM" if moment.hour < 12 else "PM")


def link(title, page_hex):
    return "%s (%s%s-%s)" % (title, LINK_HOST, title.replace(" ", "-"), page_hex)


def read_store(store):
    out = {}
    for path in sorted(glob.glob(os.path.join(store, "**", "*.md"), recursive=True)):
        rel = os.path.relpath(path, store).replace(os.sep, "/")
        if rel.startswith("index/"):
            continue
        with open(path, encoding="utf-8") as handle:
            out[rel] = parse(handle.read())
    return out


def build_notion_export(dest, store=SMALL, slug_column=True, relation_style="link"):
    """Write a Notion-style Markdown & CSV export of a store's eight databases into dest."""
    files = read_store(store)
    meta = files["store.md"][0]
    profile, profile_body = files["profile.md"]
    tag_labels = {f["slug"]: f["label"] for rel, (f, _) in files.items() if rel.startswith("tags/")}
    root = os.path.join(dest, "Export-%s" % hex_for("export"), "samepage %s" % hex_for("root"))
    rows = {name: [] for name in COLUMNS}
    pages = {name: [] for name in COLUMNS}
    projects = {}
    decisions = {}

    for rel, (f, _) in files.items():
        if rel.startswith("projects/"):
            projects[f["slug"]] = (f["name"], hex_for("project", f["slug"]))
        if rel.startswith("decisions/"):
            decisions[f["id"]] = (f["title"], hex_for("decision", f["id"]))

    def rel_cell(target):
        title, page_hex = target
        return link(title, page_hex) if relation_style == "link" else title

    rows["Profile"].append({
        "Name": profile["display_name"], "Backend": "notion", "Bio": profile.get("bio") or "",
        "Created": notion_date(profile["created_at"]), "Headline": profile["headline"],
        "Link list": "ignored serve-only copy", "Links": "", "Location": profile.get("location") or "",
        "Owner handle": meta["owner_handle"], "Schema version": meta["schema_version"],
        "Updated": notion_date(profile["updated_at"]), "Voice": profile.get("voice") or "",
    })
    pages["Profile"].append((profile["display_name"], hex_for("profile"), {}, profile_body.strip()))
    for rel, (f, body) in sorted(files.items()):
        top = rel.split("/")[0]
        if top == "profile" and rel.startswith("profile/links/"):
            rows["Links"].append({"Label": f["label"], "Created": notion_date(f["created_at"]), "Link": f["url"],
                                  "Order": f["sort_order"], "Profile": profile["display_name"], "UUID": f["id"]})
        elif top == "rules":
            rows["Rules"].append({"Rule": f["rule"], "Active": "No" if f.get("is_active") == "false" else "Yes",
                                  "Created": notion_date(f["created_at"]), "Surface": f.get("surface") or "",
                                  "UUID": f["id"], "Updated": notion_date(f["updated_at"])})
        elif top == "projects":
            rows["Projects"].append({
                "Name": f["name"], "Archived": notion_date(f.get("archived_at")), "Created": notion_date(f["created_at"]),
                "Decisions": "", "Design Assets": "", "Handoffs": "", "Last shipped": "October 24, 2026 8:00 AM",
                "Last verified": notion_date(f["last_verified_at"]), "Live URL": f.get("live_url") or "",
                "One-liner": f["one_liner"], "Outcome": f.get("outcome") or "", "Problem": f.get("problem") or "",
                "Repo URL": f.get("repo_url") or "", "Role": f.get("role") or "", "Ship Events": "",
                "Shipped on": notion_date(f.get("shipped_on")), "Slug": f["slug"], "Started": notion_date(f.get("started_on")),
                "Status": f["status"], "Tags": ", ".join(tag_labels[t] for t in f.get("tags") or []),
                "Type": f["type"], "UUID": f["id"], "Updated": notion_date(f["updated_at"])})
            pages["Projects"].append((f["name"], projects[f["slug"]][1], {"Slug": f["slug"], "UUID": f["id"]}, ""))
        elif top == "events":
            rows["Ship Events"].append({
                "Summary": f["summary"], "Created": notion_date(f["created_at"]), "Kind": f["kind"],
                "Metric label": f.get("metric_label") or "", "Metric unit": f.get("metric_unit") or "",
                "Metric value": f.get("metric_value") or "", "Occurred": notion_date(f["occurred_at"]),
                "Project": rel_cell(projects[f["project"]]), "Project slug": f["project"] if slug_column else "",
                "Proof URL": f.get("proof_url") or "", "Surface": f["surface"], "UUID": f["id"]})
        elif top == "decisions":
            successor = f.get("superseded_by")
            rows["Decisions"].append({
                "Title": f["title"], "Created": notion_date(f["created_at"]), "Decided": notion_date(f["decided_at"]),
                "Project": rel_cell(projects[f["project"]]), "Project slug": f["project"] if slug_column else "",
                "Reason": f["reason"], "Status": f["status"],
                "Superseded by": rel_cell(decisions[successor]) if successor else "",
                "Surface": f["surface"], "UUID": f["id"], "Updated": notion_date(f["updated_at"])})
            pages["Decisions"].append((f["title"], decisions[f["id"]][1],
                                       {"Reason": f["reason"], "Status": f["status"], "UUID": f["id"]}, body.strip()))
        elif top == "design":
            rows["Design Assets"].append({
                "Title": f["title"], "Created": notion_date(f["created_at"]), "Kind": f["kind"],
                "Project": rel_cell(projects[f["project"]]), "Project slug": f["project"] if slug_column else "",
                "Source URL": f.get("source_url") or "", "Status": f["status"], "Surface": f["surface"],
                "Tokens path": f.get("tokens_path") or "", "Tokens repo URL": f.get("tokens_repo_url") or "",
                "UUID": f["id"], "Updated": notion_date(f["updated_at"])})
        elif top == "handoffs":
            rows["Handoffs"].append({
                "Title": f["title"], "Created": notion_date(f["created_at"]), "Done": notion_date(f.get("done_at")),
                "From": f["from_surface"], "Picked up": notion_date(f.get("picked_up_at")),
                "Project": rel_cell(projects[f["project"]]), "Project slug": f["project"] if slug_column else "",
                "Status": f["status"], "To": f["to_surface"], "UUID": f["id"]})
            pages["Handoffs"].append((f["title"], hex_for("handoff", f["id"]),
                                      {"Status": f["status"], "UUID": f["id"]}, body.strip()))

    for name, columns in COLUMNS.items():
        db_hex = hex_for("db", name)
        os.makedirs(root, exist_ok=True)
        # the _all variant holds every row; the plain CSV holds the default view only (here: first row)
        for suffix, subset in (("_all", rows[name]), ("", rows[name][:1])):
            path = os.path.join(root, "%s %s%s.csv" % (name, db_hex, suffix))
            with open(path, "w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(subset)
        folder = os.path.join(root, "%s %s" % (name, db_hex))
        os.makedirs(folder, exist_ok=True)
        for title, page_hex, props, body in pages[name]:
            lines = ["# %s" % title, ""] + ["%s: %s" % item for item in props.items()]
            text = "\n".join(lines) + ("\n\n" + body if body else "") + "\n"
            with open(os.path.join(folder, "%s %s.md" % (title.replace("/", " "), page_hex)), "w",
                      encoding="utf-8") as handle:
                handle.write(text)
    return root


class ExportRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_export(self, **kw):
        build_notion_export(os.path.join(self.tmp, "notion"), **kw)
        out = os.path.join(self.tmp, "store")
        ok, message = export(os.path.join(self.tmp, "notion"), out, now=NOW)
        self.assertTrue(ok, message)
        return out

    def assert_matches_small(self, out):
        exported = check_store(out)
        self.assertEqual(exported.errors, [])
        original = check_store(SMALL)
        self.assertEqual(exported.counts, original.counts)
        self.assertEqual(sum(original.counts.values()), 94)
        want = read_store(SMALL)
        got = read_store(out)
        for rel, (fields, body) in want.items():
            if rel.startswith("tags/") or rel.startswith("projects/") or rel == "store.md":
                continue
            self.assertIn(rel, got)
            self.assertEqual({k: v for k, v in got[rel][0].items() if v not in (None, "")},
                             {k: v for k, v in fields.items() if v not in (None, "")}, rel)
            self.assertEqual(got[rel][1].strip(), body.strip(), rel)
        for rel, (fields, _) in want.items():
            if rel.startswith("projects/"):
                exported_fields = got[rel][0]
                self.assertEqual(len(exported_fields.get("tags") or []), len(fields.get("tags") or []), rel)
                for key in ("id", "slug", "status", "type", "updated_at", "shipped_on", "archived_at"):
                    self.assertEqual(exported_fields.get(key), fields.get(key), (rel, key))

    def test_round_trip_passes_check_and_counts_match(self):
        out = self.run_export()
        self.assert_matches_small(out)
        with open(os.path.join(out, "store.md"), encoding="utf-8") as handle:
            self.assertIn("backend: github", handle.read())

    def test_boot_files_match_github_index(self):
        out = self.run_export()
        original = os.path.join(self.tmp, "original")
        shutil.copytree(SMALL, original)
        for store in (out, original):
            ok, message, _ = build_index(store, now=NOW)
            self.assertTrue(ok, message)
        for surface in ("chat", "cowork", "code"):
            with open(os.path.join(original, "index", "boot", surface + ".md"), encoding="utf-8") as handle:
                want = handle.read()
            with open(os.path.join(out, "index", "boot", surface + ".md"), encoding="utf-8") as handle:
                got = handle.read()
            self.assertEqual(got, want, surface)

    def test_relations_from_titles_without_slug_column(self):
        out = self.run_export(slug_column=False, relation_style="title")
        self.assert_matches_small(out)

    def test_relations_from_links_without_slug_column(self):
        out = self.run_export(slug_column=False, relation_style="link")
        self.assert_matches_small(out)

    def test_cli_entry_point(self):
        build_notion_export(os.path.join(self.tmp, "notion"))
        out = os.path.join(self.tmp, "cli-store")
        self.assertEqual(main(["export", "--from-notion-csv", os.path.join(self.tmp, "notion"), "--out", out]), 0)
        self.assertEqual(check_store(out).errors, [])


class ExportRefusalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.notion = os.path.join(self.tmp, "notion")
        self.root = build_notion_export(self.notion)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_refuses_existing_path(self):
        out = os.path.join(self.tmp, "exists")
        os.makedirs(out)
        ok, message = export(self.notion, out, now=NOW)
        self.assertFalse(ok)
        self.assertIn("already exists", message)
        self.assertEqual(os.listdir(out), [])

    def test_missing_database_names_it(self):
        for path in glob.glob(os.path.join(self.root, "Handoffs *.csv")):
            os.remove(path)
        ok, message = export(self.notion, os.path.join(self.tmp, "out"), now=NOW)
        self.assertFalse(ok)
        self.assertIn("Handoffs", message)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "out")))

    def test_handoff_without_body_writes_nothing(self):
        for path in glob.glob(os.path.join(self.root, "Handoffs *", "*.md")):
            os.remove(path)
        ok, message = export(self.notion, os.path.join(self.tmp, "out"), now=NOW)
        self.assertFalse(ok)
        self.assertIn("Include subpages", message)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "out")))
        self.assertEqual([n for n in os.listdir(self.tmp) if n.startswith(".sp-export-")], [])

    def test_invalid_value_fails_check_and_writes_nothing(self):
        path = glob.glob(os.path.join(self.root, "Rules *_all.csv"))[0]
        with open(path, encoding="utf-8-sig") as handle:
            text = handle.read()
        with open(path, "w", encoding="utf-8-sig") as handle:
            handle.write(text.replace(",chat,", ",telepathy,", 1))
        ok, message = export(self.notion, os.path.join(self.tmp, "out"), now=NOW)
        self.assertFalse(ok)
        self.assertIn("telepathy", message)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "out")))


class QuirkTest(unittest.TestCase):
    def test_dates(self):
        utc = datetime.timezone.utc
        cases = {
            "November 6, 2026 9:30 AM": ("2026-11-06T09:30:00+00:00", True),
            "November 6, 2026 9:30 PM": ("2026-11-06T21:30:00+00:00", True),
            "November 6, 2026": ("2026-11-06T00:00:00+00:00", False),
            "Nov 6, 2026 12:05 AM": ("2026-11-06T00:05:00+00:00", True),
            "2026/11/06": ("2026-11-06T00:00:00+00:00", False),
            "11/06/2026 14:00": ("2026-11-06T14:00:00+00:00", True),
            "2026-11-06T09:30:00Z": ("2026-11-06T09:30:00+00:00", True),
            "2026-11-06T09:30:00.000Z": ("2026-11-06T09:30:00+00:00", True),
            "2026-11-06": ("2026-11-06T00:00:00+00:00", False),
            "November 6, 2026 3:00 PM (GMT+5:30)": ("2026-11-06T15:00:00+05:30", True),
            "November 6, 2026 3:00 PM (UTC)": ("2026-11-06T15:00:00+00:00", True),
            "November 6, 2026 → November 9, 2026": ("2026-11-06T00:00:00+00:00", False),
        }
        for text, (iso, has_time) in cases.items():
            moment, timed = parse_when(text, utc)
            self.assertEqual((moment.isoformat(), timed), (iso, has_time), text)
        self.assertIsNone(parse_when("  ", utc))
        with self.assertRaises(ExportError):
            parse_when("Yesterday", utc)

    def test_offset_applies_to_zoneless_dates(self):
        zone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        moment, _ = parse_when("November 6, 2026 9:30 AM", zone)
        self.assertEqual(moment.astimezone(datetime.timezone.utc).isoformat(), "2026-11-06T04:00:00+00:00")

    def test_checkbox_number_multi_slug(self):
        self.assertEqual(checkbox("Yes"), "true")
        self.assertEqual(checkbox("No"), "false")
        self.assertEqual(checkbox(""), "false")
        with self.assertRaises(ExportError):
            checkbox("maybe")
        self.assertEqual(number("1,280"), "1280")
        self.assertEqual(number("2.5"), "2.5")
        self.assertIsNone(number(""))
        self.assertEqual(multi("AI, Next.js,  Design system"), ["AI", "Next.js", "Design system"])
        self.assertEqual(multi(""), [])
        self.assertEqual(slugify("Next.js"), "next-js")
        self.assertEqual(slugify("Design system"), "design-system")
        self.assertEqual(slugify("AI"), "ai")


if __name__ == "__main__":
    unittest.main()
