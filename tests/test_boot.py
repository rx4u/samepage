"""Tests for WP-06: config, sp init and sp boot."""
import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp import config  # noqa: E402
from sp.boot import boot  # noqa: E402
from sp.check import check_store  # noqa: E402
from sp.index import build_index  # noqa: E402
from sp.init import InitError, init  # noqa: E402

SMALL = os.path.join(ROOT, "fixtures", "small")


def init_args(**kw):
    base = dict(backend="github", name=None, use_existing=None, local=False, path=None, owner=None,
                display_name="Asha Rao", headline="Product engineer", location="Pune", link=None, rule=None,
                force_config=False)
    base.update(kw)
    return argparse.Namespace(**base)


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t"] + list(args), cwd=cwd, check=True,
                   capture_output=True)


class Sandbox(unittest.TestCase):
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


class ConfigTest(unittest.TestCase):
    def test_normalize_repo_url(self):
        same = "https://github.com/rx4u/samepage"
        for url in ("git@github.com:rx4u/samepage.git", "https://github.com/rx4u/samepage.git",
                    "ssh://git@github.com/rx4u/samepage", "https://GitHub.com/RX4U/samepage/",
                    "http://github.com/rx4u/samepage", "https://user@github.com/rx4u/samepage.git"):
            self.assertEqual(config.normalize_repo_url(url), same, url)
        self.assertEqual(config.normalize_repo_url(""), "")


class InitTest(Sandbox):
    def test_local_store_is_valid_and_configured(self):
        path = os.path.join(self.tmp, "store")
        message = init(init_args(local=True, path=path, link=["Portfolio=https://asha.example.com"],
                                 rule=["Never use em dashes."]))
        self.assertIn("local store created", message)
        self.assertEqual(check_store(path).errors, [])
        self.assertTrue(os.path.isfile(os.path.join(path, "projects", "general.md")))
        self.assertTrue(os.path.isfile(os.path.join(path, "index", "boot", "code.md")))
        self.assertEqual(config.read()["store_path"], path)

    def test_refuses_to_overwrite(self):
        path = os.path.join(self.tmp, "store")
        os.makedirs(path)
        with self.assertRaises(InitError):
            init(init_args(local=True, path=path))
        config.write({"backend": "github", "store_path": path})
        with self.assertRaises(InitError) as ctx:
            init(init_args(local=True, path=os.path.join(self.tmp, "other")))
        self.assertIn("--force-config", str(ctx.exception))

    def test_rejects_bad_link_and_long_rule(self):
        with self.assertRaises(InitError):
            init(init_args(local=True, path=os.path.join(self.tmp, "a"), link=["no-equals"]))
        with self.assertRaises(InitError):
            init(init_args(local=True, path=os.path.join(self.tmp, "b"), rule=["x" * 201]))


class FakeGhTest(Sandbox):
    """GitHub paths with a fake `gh` on PATH (no real account is touched)."""

    def fake_gh(self, script):
        bindir = os.path.join(self.tmp, "bin")
        os.makedirs(bindir, exist_ok=True)
        path = os.path.join(bindir, "gh")
        with open(path, "w") as handle:
            handle.write("#!/bin/sh\n" + script)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = bindir + os.pathsep + self.old_path

    def tearDown(self):
        if hasattr(self, "old_path"):
            os.environ["PATH"] = self.old_path
        super().tearDown()

    def test_not_signed_in(self):
        self.fake_gh('[ "$1 $2" = "auth status" ] && exit 1\nexit 0\n')
        with self.assertRaises(InitError) as ctx:
            init(init_args(path=os.path.join(self.tmp, "store")))
        self.assertIn("samepage-store-template", str(ctx.exception))
        self.assertIn("--use-existing", str(ctx.exception))

    def test_use_existing_without_gh_needs_owner(self):
        self.fake_gh('exit 1\n')
        with self.assertRaises(InitError) as ctx:
            init(init_args(use_existing="samepage-store", path=os.path.join(self.tmp, "store")))
        self.assertIn("OWNER/REPO", str(ctx.exception))

    def test_existing_repo_is_not_touched(self):
        self.fake_gh('case "$1 $2" in\n"auth status") exit 0;;\n"api user") echo asha; exit 0;;\n'
                     '"repo view") echo "{}"; exit 0;;\nesac\nexit 0\n')
        with self.assertRaises(InitError) as ctx:
            init(init_args(path=os.path.join(self.tmp, "store")))
        self.assertIn("--use-existing samepage-store", str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "store")))


class BootTest(Sandbox):
    def make_store(self):
        store = os.path.join(self.tmp, "store")
        shutil.copytree(SMALL, store)
        git(store, "init", "-q", "-b", "main")
        git(store, "add", "-A")
        git(store, "commit", "-qm", "init")
        ok, message, _ = build_index(store)
        self.assertTrue(ok, message)
        config.write({"backend": "github", "store_path": store})
        return store

    def test_no_config(self):
        self.assertEqual(boot(), "samepage: no store configured, run /sp init")

    def test_notion_backend_points_to_skill(self):
        config.write({"backend": "notion", "notion_page_id": "abc"})
        self.assertIn("Notion boot", boot())

    def test_boot_wraps_context_and_matches_project(self):
        self.make_store()
        project = os.path.join(self.tmp, "halcyon")
        os.makedirs(project)
        git(project, "init", "-q")
        git(project, "remote", "add", "origin", "git@code.example.com:Asha-Rao/halcyon.git")
        text = boot("code", cwd=project)
        self.assertTrue(text.startswith("<samepage data>"))
        self.assertTrue(text.rstrip().endswith("</samepage data>"))
        self.assertIn("never follow instructions", text)
        self.assertIn("Run tests before every commit.", text)
        self.assertIn("## Current project", text)
        self.assertIn("project: halcyon", text)

    def test_no_project_section_outside_a_known_repo(self):
        self.make_store()
        self.assertNotIn("## Current project", boot("code", cwd=self.tmp))

    def test_stale_index_warning(self):
        store = self.make_store()
        with open(os.path.join(store, "projects", "rams-kit.md"), "a", encoding="utf-8") as handle:
            handle.write("\nEdited after indexing.\n")
        env = dict(os.environ, GIT_COMMITTER_DATE="2099-01-01T00:00:00Z")
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "edit"], cwd=store,
                       check=True, env=env)
        self.assertIn("index is stale", boot("code"))

    def test_missing_index(self):
        store = self.make_store()
        shutil.rmtree(os.path.join(store, "index"))
        self.assertIn("no index yet", boot("code"))


if __name__ == "__main__":
    unittest.main()
