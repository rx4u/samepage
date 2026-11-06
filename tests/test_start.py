"""`sp start` (ADR-0024): store and every tool found, with no questions.

PATH holds only a temp bin folder plus /usr/bin and /bin, so no real gh or claude is reached. A fake
`claude` records its arguments. HOME and SAMEPAGE_HOME point at temp folders.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp import config  # noqa: E402
from sp.__main__ import main  # noqa: E402
from sp.check import check_store  # noqa: E402

FAKE_CLAUDE = """#!/bin/sh
echo "$@" >> "%(log)s"
case "$*" in
  "plugin install samepage@samepage")
    if [ -f "%(log)s.done" ]; then echo 'Plugin "samepage@samepage" is already installed'; else touch "%(log)s.done"; echo ok; fi ;;
esac
exit 0
"""


class Start(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.home = os.path.join(self.tmp, "home")
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.home)
        os.makedirs(self.bin)
        self.saved = {k: os.environ.get(k) for k in ("HOME", "SAMEPAGE_HOME", "PATH")}
        os.environ.update(HOME=self.home, SAMEPAGE_HOME=os.path.join(self.home, ".samepage"),
                          PATH=self.bin + os.pathsep + "/usr/bin" + os.pathsep + "/bin")
        self.log = os.path.join(self.tmp, "claude.log")

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        shutil.rmtree(self.tmp)

    def sp(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue() + err.getvalue()

    def fake_claude(self):
        path = os.path.join(self.bin, "claude")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(FAKE_CLAUDE % {"log": self.log})
        os.chmod(path, 0o755)

    def test_no_gh_no_tools_makes_local_store(self):
        code, out = self.sp("start")
        self.assertEqual(code, 0, out)
        store = config.read()["store_path"]
        self.assertTrue(os.path.isfile(os.path.join(store, "store.md")))
        self.assertEqual(check_store(store).errors, [])
        self.assertIn("local store created", out)
        self.assertIn("tools: none found", out)
        self.assertIn("samepage.skill", out)

    def test_dry_run_writes_nothing(self):
        os.makedirs(os.path.join(self.home, ".codex"))
        code, out = self.sp("start", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("would create a local store", out)
        self.assertEqual(config.read(), {})
        self.assertFalse(os.path.exists(os.path.join(self.home, ".codex", "config.toml")))

    def test_claude_code_gets_the_plugin(self):
        self.fake_claude()
        code, out = self.sp("start")
        self.assertEqual(code, 0, out)
        with open(self.log, encoding="utf-8") as handle:
            calls = handle.read().splitlines()
        self.assertEqual(calls[:2], ["plugin marketplace add rx4u/samepage", "plugin install samepage@samepage"])
        self.assertIn("Claude Code: plugin installed", out)

    def test_claude_settings_get_session_start_entry(self):
        self.fake_claude()
        settings = os.path.join(self.home, ".claude", "settings.json")
        os.makedirs(os.path.dirname(settings))
        with open(settings, "w", encoding="utf-8") as handle:
            json.dump({"theme": "dark", "hooks": {"SessionStart": [{"hooks": [{"type": "command",
                                                                              "command": "echo hi"}]}]}}, handle)
        self.assertEqual(self.sp("start")[0], 0)
        with open(settings, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["theme"], "dark")
        commands = [h["command"] for g in data["hooks"]["SessionStart"] for h in g["hooks"]]
        self.assertIn("echo hi", commands)
        ours = [c for c in commands if "session-start.sh" in c]
        self.assertEqual(len(ours), 1)
        self.assertTrue(os.path.isfile(ours[0].split('"')[1]))
        self.assertTrue(os.path.isfile(settings + ".samepage-backup"))
        code, out = self.sp("start")
        self.assertIn("already loads samepage", out)
        with open(settings, encoding="utf-8") as handle:
            again = json.load(handle)
        self.assertEqual(again, data)

    def test_codex_folder_gets_mcp_entry(self):
        os.makedirs(os.path.join(self.home, ".codex"))
        with open(os.path.join(self.home, ".codex", "config.toml"), "w", encoding="utf-8") as handle:
            handle.write('model = "o3"\n')
        code, out = self.sp("start")
        self.assertEqual(code, 0, out)
        with open(os.path.join(self.home, ".codex", "config.toml"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("[mcp_servers.samepage]", text)
        self.assertIn('model = "o3"', text)
        self.assertTrue(os.path.isfile(os.path.join(self.home, ".codex", "config.toml.samepage-backup")))
        self.assertIn("connecting Codex", out)

    def test_second_run_reuses_store_and_updates_plugin(self):
        self.fake_claude()
        self.assertEqual(self.sp("start")[0], 0)
        store = config.read()["store_path"]
        code, out = self.sp("start")
        self.assertEqual(code, 0, out)
        self.assertIn("store: using %s" % store, out)
        self.assertIn("already installed, updated", out)
        with open(self.log, encoding="utf-8") as handle:
            self.assertIn("plugin update samepage@samepage", handle.read())

    def test_broken_config_stops(self):
        config.write({"backend": "github", "store_path": os.path.join(self.tmp, "gone")})
        code, out = self.sp("start")
        self.assertEqual(code, 1, out)
        self.assertIn("not a store", out)


if __name__ == "__main__":
    unittest.main()
