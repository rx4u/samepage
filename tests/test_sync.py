"""Tests for sp link and sp sync (ADR-0023): rules and decisions cross between two stores, both ways.

Each test builds two git clones of fixtures/small with their own bare remotes, so pull, commit and
push are real, and points SAMEPAGE_HOME at a temp config.
"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp import config  # noqa: E402
from sp.__main__ import main  # noqa: E402
from sp.check import check_store  # noqa: E402
from sp.frontmatter import emit, parse  # noqa: E402
from sp.index import build_index  # noqa: E402

SMALL = os.path.join(ROOT, "fixtures", "small")
RULE_A = "aaaaaaaa-2222-4333-8444-555555555555"
RULE_B = "bbbbbbbb-2222-4333-8444-555555555555"
DECISION = "decisions/pearl-dental/2026-10-04-1672b68f.md"


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t"] + list(args), cwd=cwd, check=True,
                          capture_output=True, text=True).stdout


class Sync(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old_home = os.environ.get("SAMEPAGE_HOME")
        os.environ["SAMEPAGE_HOME"] = os.path.join(self.tmp, "home")
        self.work = self.clone("work", drop_project=None)
        self.home = self.clone("home", drop_project="pearl-dental")
        config.write({"backend": "github", "store_path": self.work})

    def tearDown(self):
        if self.old_home is None:
            os.environ.pop("SAMEPAGE_HOME", None)
        else:
            os.environ["SAMEPAGE_HOME"] = self.old_home
        shutil.rmtree(self.tmp)

    def clone(self, name, drop_project):
        seed = os.path.join(self.tmp, name + "-seed")
        shutil.copytree(SMALL, seed)
        if drop_project:
            shutil.rmtree(os.path.join(seed, "decisions", drop_project))
            for folder in ("events", "design"):
                for dirpath, _, files in os.walk(os.path.join(seed, folder)):
                    for f in files:
                        full = os.path.join(dirpath, f)
                        with open(full, encoding="utf-8") as handle:
                            if "project: %s\n" % drop_project in handle.read():
                                os.remove(full)
            for dirpath, _, files in os.walk(os.path.join(seed, "handoffs")):
                for f in files:
                    full = os.path.join(dirpath, f)
                    with open(full, encoding="utf-8") as handle:
                        if "project: %s\n" % drop_project in handle.read():
                            os.remove(full)
            os.remove(os.path.join(seed, "projects", drop_project + ".md"))
        ok, message, _ = build_index(seed)
        self.assertTrue(ok, message)
        git(seed, "init", "-q", "-b", "main")
        git(seed, "add", "-A")
        git(seed, "commit", "-qm", "seed")
        remote = os.path.join(self.tmp, name + ".git")
        git(self.tmp, "clone", "-q", "--bare", seed, remote)
        store = os.path.join(self.tmp, name)
        git(self.tmp, "clone", "-q", remote, store)
        git(store, "config", "user.name", "t")
        git(store, "config", "user.email", "t@t")
        return store

    def sp(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue() + err.getvalue()

    def ok(self, *argv):
        code, text = self.sp(*argv)
        self.assertEqual(code, 0, text)
        return text

    def fails(self, *argv):
        code, text = self.sp(*argv)
        self.assertNotEqual(code, 0, text)
        return text

    def path(self, store, rel):
        return os.path.join(store, rel)

    def exists(self, store, rel):
        return os.path.isfile(self.path(store, rel))

    def read(self, store, rel):
        with open(self.path(store, rel), encoding="utf-8") as handle:
            return handle.read()

    def link(self):
        self.ok("link", "add", self.home, "--name", "personal")

    def seed_rules(self):
        self.ok("rules", "add", "--rule", "Work rule A", "--id", RULE_A, "--now", "2026-11-06T09:00:00Z")
        self.ok("rules", "add", "--rule", "Home rule B", "--store", self.home, "--id", RULE_B,
                "--now", "2026-11-06T09:00:00Z")

    def assert_clean(self, store):
        report = check_store(store)
        self.assertEqual(report.errors, [], report.errors)
        self.assertEqual(git(store, "status", "--porcelain"), "")

    # ----- sp link

    def test_link_add_list_remove(self):
        self.link()
        self.assertIn("personal", self.ok("link", "list"))
        self.assertIn("own store", self.fails("link", "add", self.work, "--name", "self"))
        self.assertIn("already linked", self.fails("link", "add", self.home, "--name", "again"))
        self.assertIn("not a samepage store", self.fails("link", "add", self.tmp, "--name", "nope"))
        self.assertIn("lowercase", self.fails("link", "add", self.home, "--name", "My Home"))
        self.ok("link", "remove", "personal")
        self.assertIn("no linked stores", self.ok("link", "list"))
        self.assertIn("no linked store", self.fails("link", "remove", "personal"))

    def test_link_maximum(self):
        for i in range(3):
            other = os.path.join(self.tmp, "extra%d" % i)
            shutil.copytree(SMALL, other)
            self.ok("link", "add", other, "--name", "s%d" % i)
        self.assertIn("maximum", self.fails("link", "add", self.home, "--name", "s3"))
        self.assertIn("name one", self.fails("sync", "--dry-run"))

    def test_config_write_keeps_links(self):
        self.link()
        config.write({"backend": "github", "store_path": self.work})
        self.assertEqual(config.links(), {"personal": self.home})

    # ----- sp sync

    def test_sync_needs_a_link(self):
        self.assertIn("no linked store", self.fails("sync"))

    def test_both_ways_then_nothing(self):
        self.seed_rules()
        self.link()
        before = git(self.home, "rev-parse", "HEAD")
        out = self.ok("sync", "--yes")
        self.assertIn("this store -> personal: 1 rule", out)
        self.assertIn("personal -> this store: 1 rule", out)
        self.assertIn("skip %s: personal has no project pearl-dental" % DECISION, out)
        self.assertEqual(self.read(self.home, "rules/aaaaaaaa.md"), self.read(self.work, "rules/aaaaaaaa.md"))
        self.assertTrue(self.exists(self.work, "rules/bbbbbbbb.md"))
        self.assertFalse(self.exists(self.home, DECISION))
        self.assertIn("Work rule A", self.read(self.home, "index/rules.md"))
        self.assertIn("sync from this store", git(self.home, "log", "-1", "--format=%s"))
        self.assertNotEqual(git(self.home, "rev-parse", "HEAD"), before)
        self.assertEqual(git(self.home, "rev-parse", "HEAD"), git(self.home, "rev-parse", "origin/main"))
        self.assert_clean(self.work)
        self.assert_clean(self.home)
        again = self.ok("sync", "--dry-run")
        self.assertIn("already share", again)

    def test_decision_crosses_when_project_exists(self):
        self.ok("link", "add", self.home, "--name", "personal")
        shutil.copy(self.path(self.work, "projects/pearl-dental.md"), self.path(self.home, "projects/pearl-dental.md"))
        build_index(self.home)
        git(self.home, "add", "-A")
        git(self.home, "commit", "-qm", "add project")
        out = self.ok("sync", "--yes")
        self.assertIn("copy decision %s" % DECISION, out)
        self.assertEqual(self.read(self.home, DECISION), self.read(self.work, DECISION))
        self.assert_clean(self.home)

    def test_pause_propagates_by_updated_at(self):
        self.seed_rules()
        self.link()
        self.ok("sync", "--yes")
        self.ok("rules", "pause", "aaaaaaaa", "--store", self.home, "--now", "2026-11-06T12:00:00Z")
        out = self.ok("sync", "--yes")
        self.assertIn("personal -> this store: 1 rule", out)
        self.assertIn("update rule rules/aaaaaaaa.md", out)
        self.assertEqual(parse(self.read(self.work, "rules/aaaaaaaa.md"))[0]["is_active"], "false")
        self.assertIn("already share", self.ok("sync", "--dry-run"))

    def test_same_stamp_conflict_is_skipped(self):
        self.seed_rules()
        self.link()
        self.ok("sync", "--yes")
        fields, body = parse(self.read(self.home, "rules/aaaaaaaa.md"))
        fields = dict(fields, rule="Edited at home")
        with open(self.path(self.home, "rules/aaaaaaaa.md"), "w", encoding="utf-8") as handle:
            handle.write(emit(fields, body))
        out = self.ok("sync", "--dry-run")
        self.assertIn("edited in both stores", out)

    def test_dry_run_writes_nothing(self):
        self.seed_rules()
        self.link()
        heads = (git(self.work, "rev-parse", "HEAD"), git(self.home, "rev-parse", "HEAD"))
        self.assertIn("dry run, nothing written", self.ok("sync", "personal", "--dry-run"))
        self.assertFalse(self.exists(self.home, "rules/aaaaaaaa.md"))
        self.assertEqual(heads, (git(self.work, "rev-parse", "HEAD"), git(self.home, "rev-parse", "HEAD")))

    def test_no_prompt_without_yes(self):
        self.seed_rules()
        self.link()
        self.assertIn("--yes", self.fails("sync"))
        self.assertFalse(self.exists(self.home, "rules/aaaaaaaa.md"))

    def test_newer_key_is_skipped_for_older_store(self):
        self.link()
        for store in (self.work,):
            meta, body = parse(self.read(store, "store.md"))
            with open(self.path(store, "store.md"), "w", encoding="utf-8") as handle:
                handle.write(emit(dict(meta, schema_version="1.1"), body))
            build_index(store)
            git(store, "add", "-A")
            git(store, "commit", "-qm", "1.1")
        self.ok("log", "decision", "--project", "general", "--title", "Tool decision", "--reason", "test",
                "--tool", "codex", "--id", RULE_A, "--now", "2026-11-06T09:00:00Z")
        out = self.ok("sync", "--dry-run")
        self.assertIn("uses tool (schema 1.1); upgrade personal first", out)


if __name__ == "__main__":
    unittest.main()
