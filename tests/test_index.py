"""Tests for WP-03 and WP-04: sp index and the perf fixture."""
import os
import re
import shutil
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp.check import BOOT_MAX_CHARS, PROJECT_SECTION_MAX_CHARS  # noqa: E402
from sp.fixtures import generate_perf  # noqa: E402
from sp.index import build_index, read_builds  # noqa: E402

SMALL = os.path.join(ROOT, "fixtures", "small")
NOW = "2026-11-06T06:00:00Z"


def read(store, rel):
    with open(os.path.join(store, rel), encoding="utf-8") as handle:
        return handle.read()


class SmallIndexTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = tempfile.mkdtemp()
        shutil.copytree(SMALL, cls.store, dirs_exist_ok=True)
        ok, message, _ = build_index(cls.store, now=NOW)
        assert ok, message

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.store)

    def test_header_on_every_file(self):
        for dirpath, _, names in os.walk(os.path.join(self.store, "index")):
            for name in names:
                text = read(dirpath, name)
                self.assertRegex(text.split("\n")[0], r"^built: \S+Z from nogit schema 1\.0$", name)

    def test_code_boot_contents(self):
        boot = read(self.store, "index/boot/code.md")
        self.assertIn("Run tests before every commit.", boot)
        self.assertNotIn("Keep chat replies short.", boot)
        self.assertNotIn("Old rule, paused.", boot)
        self.assertNotIn("- general:", boot)
        self.assertIn("## Recent ships", boot)
        self.assertIn("Open handoffs to code (1)", boot)

    def test_chat_boot_contents(self):
        boot = read(self.store, "index/boot/chat.md")
        self.assertIn("Keep chat replies short.", boot)
        self.assertNotIn("Run tests before every commit.", boot)
        self.assertIn("Location: Pune, India", boot)
        self.assertNotIn("## Recent ships", boot)
        self.assertIn("Open handoffs to chat (2)", boot)
        self.assertIn("general: Handoff 4", boot)  # general handoffs still reach the inbox (B2)

    def test_active_projects_newest_first(self):
        boot = read(self.store, "index/boot/code.md")
        dates = re.findall(r"\(updated (\d{4}-\d{2}-\d{2})\)", boot)
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_proof_excludes_general_and_marks_missing_proof(self):
        proof = read(self.store, "index/proof-1.md")
        self.assertNotIn("(general)", proof)
        self.assertIn("proof: no public proof yet", proof)

    def test_project_section_and_repo_map(self):
        section = read(self.store, "index/project/halcyon.md")
        self.assertIn("design_system [approved] Halcyon tokens", section)
        self.assertNotIn("Decision 0:", section)  # superseded decisions are not in force
        self.assertIn("Decision 2:", section)
        repos = read(self.store, "index/repos.md")
        self.assertIn("https://code.example.com/asha-rao/halcyon halcyon", repos)

    def test_failed_check_keeps_old_index(self):
        before = read(self.store, "index/boot/code.md")
        path = os.path.join(self.store, "projects", "halcyon.md")
        original = read(self.store, "projects/halcyon.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(original.replace("status: shipped", "status: done"))
        try:
            ok, message, _ = build_index(self.store, now="2026-11-06T07:00:00Z")
            self.assertFalse(ok)
            self.assertEqual(read(self.store, "index/boot/code.md"), before)
            self.assertEqual(read_builds(self.store)[0]["status"], "failed")
        finally:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(original)


class PerfIndexTest(unittest.TestCase):
    def test_perf_fixture_targets(self):
        store = tempfile.mkdtemp()
        try:
            summary = generate_perf(store, seed=42)
            self.assertIn("project 1000", summary)
            start = time.monotonic()
            ok, message, stats = build_index(store, now=NOW)
            seconds = time.monotonic() - start
            self.assertTrue(ok, message)
            self.assertLess(seconds, 5.0, "sp index took %.2fs, target 5s" % seconds)
            for surface in ("code", "chat", "cowork"):
                self.assertLessEqual(len(read(store, "index/boot/%s.md" % surface)), BOOT_MAX_CHARS)
            project_dir = os.path.join(store, "index", "project")
            for name in os.listdir(project_dir):
                self.assertLessEqual(len(read(project_dir, name)), PROJECT_SECTION_MAX_CHARS, name)
            for dirpath, _, names in os.walk(os.path.join(store, "index")):
                for name in names:
                    text = read(dirpath, name)
                    match = re.search(r"^next: (\S+)$", text, re.M)
                    if match:
                        self.assertTrue(os.path.exists(os.path.join(store, match.group(1))), match.group(1))
                    rows = [l for l in text.split("\n") if l.startswith("- ")]
                    if re.search(r"(proof|projects|handoffs-\w+)-\d+\.md$", name):
                        self.assertLessEqual(len(rows), 20, name)
                    if os.path.basename(dirpath) == "tags":
                        self.assertLessEqual(len(rows), 50, name)
            builds = read_builds(store)
            self.assertEqual(len(builds), 50)
            self.assertEqual(sum(1 for b in builds if b["status"] == "failed"), 3)
        finally:
            shutil.rmtree(store)


if __name__ == "__main__":
    unittest.main()
