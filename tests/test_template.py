"""Tests for WP-11: the store template and its index Action."""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp.check import check_store  # noqa: E402
from sp.init import TEMPLATE_DIR, init  # noqa: E402

TEMPLATE = os.path.join(ROOT, "store-template")
WORKFLOW = os.path.join(TEMPLATE, ".github", "workflows", "index.yml")
TEMPLATE_FILES = ("README.md", ".gitignore", ".github/workflows/index.yml")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def init_args(**kw):
    base = dict(backend="github", name=None, use_existing=None, local=False, path=None, owner=None,
                display_name="Asha Rao", headline="Product engineer", location="Pune", link=None, rule=None,
                force_config=False)
    base.update(kw)
    return argparse.Namespace(**base)


def steps(text):
    """Return the step names of the workflow in order (simple text parse, stdlib only)."""
    return re.findall(r"^\s+- name:\s*(.+)$", text, re.M)


class TemplateFilesTest(unittest.TestCase):
    def test_template_files_exist(self):
        self.assertEqual(os.path.realpath(TEMPLATE_DIR), os.path.realpath(TEMPLATE))
        for rel in TEMPLATE_FILES:
            self.assertTrue(os.path.isfile(os.path.join(TEMPLATE, rel)), rel)

    def test_gitignore_entries(self):
        lines = read(os.path.join(TEMPLATE, ".gitignore")).split()
        self.assertIn("index.tmp/", lines)
        self.assertIn(".samepage-tool/", lines)

    def test_no_em_dashes(self):
        for rel in TEMPLATE_FILES:
            self.assertNotIn(chr(0x2014), read(os.path.join(TEMPLATE, rel)), rel)

    def test_readme_says_protection_must_allow_the_action(self):
        text = read(os.path.join(TEMPLATE, "README.md"))
        self.assertIn("branch protection", text)
        self.assertIn("index: rebuild", text)


class WorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(WORKFLOW)

    def test_no_tabs_and_required_top_level_keys(self):
        self.assertNotIn("\t", self.text)
        for key in ("name", "on", "permissions", "concurrency", "jobs"):
            self.assertRegex(self.text, r"(?m)^%s:" % key)

    def test_trigger_is_push_skipping_index_only_changes(self):
        self.assertRegex(self.text, r"(?m)^on:\n  push:\n")
        self.assertRegex(self.text, r"paths-ignore:\n\s+- \"index/\*\*\"")
        self.assertIn("github.ref_name == github.event.repository.default_branch", self.text)

    def test_skips_its_own_commits(self):
        self.assertIn("github.actor != 'github-actions[bot]'", self.text)

    def test_limits(self):
        self.assertRegex(self.text, r"(?m)^\s+timeout-minutes: 3$")
        self.assertRegex(self.text, r"(?m)^permissions:\n  contents: write$")
        self.assertRegex(self.text, r"(?m)^concurrency:\n  group: \S+")

    def test_every_action_pinned_by_sha(self):
        uses = re.findall(r"uses:\s*([^\s#]+)", self.text)
        self.assertGreaterEqual(len(uses), 3)
        for use in uses:
            self.assertRegex(use, r"@[0-9a-f]{40}$")
        self.assertIn("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", uses)
        self.assertIn("actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0", uses)

    def test_tool_checkout(self):
        self.assertIn("repository: rx4u/samepage", self.text)
        self.assertIn("path: .samepage-tool", self.text)

    def test_check_before_index_before_commit(self):
        names = steps(self.text)
        order = [names.index("sp check"), names.index("sp index"), names.index("Commit and push index/ only")]
        self.assertEqual(order, sorted(order))
        self.assertIn("python -m sp check .", self.text)
        self.assertIn("python -m sp index .", self.text)

    def test_commits_only_index_with_message(self):
        commit = self.text.split("- name: Commit and push index/ only", 1)[1]
        self.assertIn("git add -- index", commit)
        self.assertNotIn("git add -A", commit)
        self.assertNotIn("git add .", commit)
        self.assertIn('git commit -q -m "index: rebuild $(git rev-parse --short=8 HEAD)"', commit)
        # A failed check step stops the job before this step: no continue-on-error, no always().
        self.assertNotIn("continue-on-error", self.text)
        self.assertNotIn("always()", self.text)


class InitCopiesTemplateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old_home = os.environ.get("SAMEPAGE_HOME")
        os.environ["SAMEPAGE_HOME"] = os.path.join(self.tmp, "home")

    def tearDown(self):
        if self.old_home is None:
            os.environ.pop("SAMEPAGE_HOME", None)
        else:
            os.environ["SAMEPAGE_HOME"] = self.old_home
        shutil.rmtree(self.tmp)

    def test_local_store_gets_template_and_passes_check(self):
        path = os.path.join(self.tmp, "store")
        init(init_args(local=True, path=path))
        for rel in TEMPLATE_FILES:
            self.assertEqual(read(os.path.join(path, rel)), read(os.path.join(TEMPLATE, rel)), rel)
        report = check_store(path)
        self.assertEqual(report.errors, [])
        self.assertEqual([w for w in report.warnings if ".github" in w[0]], [])
        tracked = subprocess.run(["git", "ls-files"], cwd=path, capture_output=True, text=True, check=True).stdout
        self.assertIn(".github/workflows/index.yml", tracked.split())
        self.assertIn(".gitignore", tracked.split())

    def test_sp_check_cli_passes_on_new_store(self):
        path = os.path.join(self.tmp, "store")
        init(init_args(local=True, path=path))
        done = subprocess.run([sys.executable, "-m", "sp", "check", path], cwd=ROOT, capture_output=True,
                              text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


if __name__ == "__main__":
    unittest.main()
