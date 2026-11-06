"""Schema 1.1: surfaces as roles and the optional tool field (WP-18, ADR-0017, B22, B23, B31)."""
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp import SCHEMA_VERSION, TOOL_ROLES  # noqa: E402
from sp.__main__ import main  # noqa: E402
from sp.check import check_store  # noqa: E402
from sp.frontmatter import parse  # noqa: E402
from sp.index import build_index  # noqa: E402

SMALL = os.path.join(ROOT, "fixtures", "small")
NOW = "2026-11-06T10:00:00Z"
PIN = "11111111-2222-4333-8444-555555555555"


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def set_version(store, version):
    path = os.path.join(store, "store.md")
    text = re.sub(r"schema_version: \S+", "schema_version: %s" % version, read(path))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


class Schema(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "schema", "fields.json"), encoding="utf-8") as handle:
            self.fields = json.load(handle)
        with open(os.path.join(ROOT, "schema", "lookups.json"), encoding="utf-8") as handle:
            self.lookups = json.load(handle)["lookups"]

    def test_version_and_lookup(self):
        self.assertEqual(SCHEMA_VERSION, "1.1")
        self.assertEqual(self.fields["schema_version"], "1.1")
        self.assertEqual(sorted(self.lookups["tool"]), sorted(TOOL_ROLES))
        self.assertNotIn("chatgpt", " ".join(self.lookups["tool"]))  # ADR-0019
        self.assertEqual(self.lookups["surface"], ["code", "chat", "cowork", "design"])

    def test_since_keys(self):
        since = {(t, k["key"]): k.get("since") for t, v in self.fields["tables"].items() for k in v["keys"]}
        for table, key in (("ship_event", "tool"), ("decision", "tool"), ("design_asset", "tool"),
                           ("handoff", "from_tool")):
            self.assertEqual(since[(table, key)], "1.1", (table, key))
        self.assertEqual(sum(1 for v in since.values() if v), 4)

    def test_roles_cover_surfaces(self):
        for tool, role in TOOL_ROLES.items():
            self.assertIn(role, self.lookups["surface"] + [None], tool)


class Store(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = os.path.join(self.tmp, "store")
        shutil.copytree(SMALL, self.store)
        self.old_tool = os.environ.pop("SAMEPAGE_TOOL", None)

    def tearDown(self):
        shutil.rmtree(self.tmp)
        if self.old_tool is not None:
            os.environ["SAMEPAGE_TOOL"] = self.old_tool

    def event_with_tool(self):
        rel = "events/2026/2026-10-24-north-star-ds-2cc10cb6.md"
        path = os.path.join(self.store, rel)
        text = read(path).replace("\nsummary:", "\ntool: cursor\nsummary:", 1)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return rel

    def ship(self, *extra):
        return run(["log", "ship", "--store", self.store, "--project", "halcyon", "--kind", "milestone",
                    "--summary", "Pricing page drafted", "--now", NOW, "--id", PIN] + list(extra))

    def written_event(self):
        rel = "events/2026/2026-11-06-halcyon-%s.md" % PIN[:8]
        return parse(read(os.path.join(self.store, rel)))[0]

    def test_small_fixture_is_1_0_and_valid(self):
        self.assertIn("schema_version: 1.0", read(os.path.join(self.store, "store.md")))
        self.assertEqual(check_store(self.store).errors, [])

    def test_tool_key_on_1_0_store_fails(self):
        rel = self.event_with_tool()
        errors = check_store(self.store, check_index=False).errors
        self.assertEqual(len(errors), 1, errors)
        self.assertEqual(errors[0][:2], (rel, "tool"))
        self.assertIn("needs schema 1.1", errors[0][2])

    def test_tool_key_on_1_1_store_passes(self):
        self.event_with_tool()
        set_version(self.store, "1.1")
        self.assertEqual(check_store(self.store, check_index=False).errors, [])

    def test_unknown_tool_code_fails(self):
        self.event_with_tool()
        set_version(self.store, "1.1")
        path = os.path.join(self.store, "events/2026/2026-10-24-north-star-ds-2cc10cb6.md")
        text = read(path).replace("tool: cursor", "tool: chatgpt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        self.assertEqual([e[1] for e in check_store(self.store, check_index=False).errors], ["tool"])

    def test_write_records_tool_on_1_1(self):
        set_version(self.store, "1.1")
        self.assertTrue(build_index(self.store)[0])
        code, out, err = self.ship("--tool", "cursor")
        self.assertEqual(code, 0, out + err)
        event = self.written_event()
        self.assertEqual((event["surface"], event["tool"]), ("code", "cursor"))

    def test_write_drops_tool_on_1_0_with_note(self):
        code, out, _ = self.ship("--tool", "cursor", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("samepage: note: store is schema 1.0; tool not recorded", out)
        self.assertNotIn("tool: cursor", out)
        code, out, err = self.ship("--tool", "cursor")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("tool", self.written_event())
        self.assertEqual(check_store(self.store).errors, [])

    def test_env_default_and_roles(self):
        set_version(self.store, "1.1")
        os.environ["SAMEPAGE_TOOL"] = "claude_desktop"
        code, out, err = self.ship("--dry-run")
        os.environ.pop("SAMEPAGE_TOOL")
        self.assertEqual(code, 0, out + err)
        self.assertIn("surface: chat", out)
        self.assertIn("tool: claude_desktop", out)

    def test_explicit_surface_wins(self):
        set_version(self.store, "1.1")
        code, out, _ = self.ship("--tool", "cursor", "--surface", "cowork", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("surface: cowork", out)
        self.assertIn("tool: cursor", out)

    def test_other_needs_a_surface(self):
        set_version(self.store, "1.1")
        code, _, err = self.ship("--tool", "other", "--dry-run")
        self.assertEqual(code, 1)
        self.assertIn("--tool other has no default surface", err)
        code, out, _ = self.ship("--tool", "other", "--surface", "chat", "--dry-run")
        self.assertEqual(code, 0)

    def test_no_tool_means_code_and_no_key(self):
        set_version(self.store, "1.1")
        code, out, _ = self.ship("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("surface: code", out)
        self.assertNotIn("tool:", out)

    def test_handoff_from_tool_shows_on_inbox_lines(self):
        set_version(self.store, "1.1")
        self.assertTrue(build_index(self.store)[0])
        code, out, err = run(["handoff", "new", "--store", self.store, "--project", "halcyon", "--to", "chat",
                              "--title", "Write the launch post", "--body", "Goal: a post. Done when: drafted.",
                              "--tool", "codex", "--now", NOW, "--id", PIN])
        self.assertEqual(code, 0, out + err)
        fields = parse(read(os.path.join(self.store, "handoffs", PIN[:8] + ".md")))[0]
        self.assertEqual((fields["from_surface"], fields["from_tool"]), ("code", "codex"))
        inbox = read(os.path.join(self.store, "index", "handoffs-chat-1.md"))
        self.assertIn("(from code via codex, 2026-11-06)", inbox)
        boot = read(os.path.join(self.store, "index", "boot", "chat.md"))
        self.assertIn("(from code via codex)", boot)

    def test_decision_and_design_record_tool(self):
        set_version(self.store, "1.1")
        code, out, _ = run(["log", "decision", "--store", self.store, "--project", "halcyon", "--title", "Use Postgres",
                            "--reason", "RLS", "--tool", "gemini_cli", "--now", NOW, "--dry-run"])
        self.assertEqual(code, 0, out)
        self.assertIn("tool: gemini_cli", out)
        code, out, _ = run(["log", "design", "--store", self.store, "--project", "halcyon", "--kind", "prototype",
                            "--title", "Pricing", "--tool", "windsurf", "--now", NOW, "--dry-run"])
        self.assertEqual(code, 0, out)
        self.assertIn("tool: windsurf", out)

    def test_index_header_carries_store_version(self):
        self.assertTrue(build_index(self.store)[0])
        self.assertIn(" schema 1.0\n", read(os.path.join(self.store, "index", "boot", "code.md")).split("\n", 1)[0] + "\n")
        set_version(self.store, "1.1")
        self.assertTrue(build_index(self.store)[0])
        self.assertTrue(read(os.path.join(self.store, "index", "boot", "chat.md")).split("\n", 1)[0].endswith(" schema 1.1"))


if __name__ == "__main__":
    unittest.main()
