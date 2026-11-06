"""`sp setup` and install.sh (WP-21, ADR-0020, B29, B33 to B35)."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp import context, setup  # noqa: E402
from sp.__main__ import main  # noqa: E402

OTHER = {"mcpServers": {"other": {"command": "node", "args": ["server.js"]}}, "theme": "dark"}


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    code = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


class Setup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        self.project = os.path.join(self.tmp, "project")
        os.makedirs(self.project)
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        self.old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.tmp)

    def h(self, rel):
        return os.path.join(self.home, rel)

    def setup_tool(self, tool, *extra):
        return run(["setup", tool, "--cwd", self.project] + list(extra))

    def test_gemini_adds_entry_keeps_others_and_backs_up(self):
        write(self.h(".gemini/settings.json"), json.dumps(OTHER, indent=4) + "\n")
        before = read(self.h(".gemini/settings.json"))
        code, out, _ = self.setup_tool("gemini")
        self.assertEqual(code, 0, out)
        data = json.loads(read(self.h(".gemini/settings.json")))
        self.assertEqual(list(data), ["mcpServers", "theme"])
        self.assertEqual(list(data["mcpServers"]), ["other", "samepage"])
        self.assertEqual(data["mcpServers"]["other"], OTHER["mcpServers"]["other"])
        entry = data["mcpServers"]["samepage"]
        self.assertEqual(entry["command"], sys.executable)
        self.assertEqual(entry["args"], [os.path.join(ROOT, "sp_run.py"), "mcp", "--tool", "gemini_cli"])
        self.assertNotIn("PYTHONPATH", entry["env"])  # Gemini CLI blocks it (B45)
        self.assertIn("PATH", entry["env"])
        self.assertIn('\n    "mcpServers"', read(self.h(".gemini/settings.json")))  # keeps the file's indent
        self.assertEqual(read(self.h(".gemini/settings.json.samepage-backup")), before)
        self.assertTrue(os.path.isfile(self.h(".agents/skills/samepage/SKILL.md")))
        self.assertIn("--tool gemini_cli", read(os.path.join(self.project, "GEMINI.md")))

    def test_idempotent_and_backup_never_overwritten(self):
        write(self.h(".gemini/settings.json"), json.dumps(OTHER) + "\n")
        self.setup_tool("gemini")
        first = read(self.h(".gemini/settings.json"))
        backup = read(self.h(".gemini/settings.json.samepage-backup"))
        code, out, _ = self.setup_tool("gemini")
        self.assertEqual(code, 0)
        self.assertIn("already has the samepage entry", out)
        self.assertIn("skill already current", out)
        self.assertIn("GEMINI.md unchanged", out)
        self.assertEqual(read(self.h(".gemini/settings.json")), first)
        self.assertEqual(read(self.h(".gemini/settings.json.samepage-backup")), backup)
        self.assertEqual(len(json.loads(first)["mcpServers"]), 2)

    def test_jsonc_is_never_touched(self):
        text = '{\n  // my comment\n  "mcpServers": {}\n}\n'
        write(self.h(".gemini/settings.json"), text)
        code, out, _ = self.setup_tool("gemini")
        self.assertEqual(code, 1)
        self.assertIn("does not parse as plain JSON", out)
        self.assertIn('"samepage"', out)  # the snippet
        self.assertEqual(read(self.h(".gemini/settings.json")), text)
        self.assertFalse(os.path.exists(self.h(".gemini/settings.json.samepage-backup")))

    def test_dry_run_writes_nothing(self):
        code, out, _ = self.setup_tool("gemini", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("dry run", out)
        self.assertEqual(os.listdir(self.home), [])
        self.assertEqual(sorted(os.listdir(self.project)), [".git"])

    def test_codex_toml_append_and_replace(self):
        user = 'model = "o5"\n\n[mcp_servers.other]\ncommand = "node"\n'
        write(self.h(".codex/config.toml"), user)
        code, out, _ = self.setup_tool("codex")
        self.assertEqual(code, 0, out)
        text = read(self.h(".codex/config.toml"))
        self.assertTrue(text.startswith(user + "\n[mcp_servers.samepage]\n"))
        self.assertIn('"mcp", "--tool", "codex"]', text)
        self.assertIn("env = { PATH = ", text)
        # An old samepage block with an env subtable, followed by user tables, is replaced whole (B29).
        old = (user + '\n[mcp_servers.samepage]\ncommand = "old"\n\n[mcp_servers.samepage.env]\nX = "1"\n\n'
               '[profiles.work]\nmodel = "o5"\n')
        write(self.h(".codex/config.toml"), old)
        self.setup_tool("codex")
        text = read(self.h(".codex/config.toml"))
        self.assertNotIn('"old"', text)
        self.assertNotIn("[mcp_servers.samepage.env]", text)
        self.assertEqual(text.count("[mcp_servers.samepage]"), 1)
        self.assertTrue(text.startswith(user))
        self.assertTrue(text.endswith('\n[profiles.work]\nmodel = "o5"\n'))
        self.assertIn("AGENTS.md", os.listdir(self.project))

    def test_copilot_cli_always_vscode_when_present(self):
        self.setup_tool("copilot")
        cli = json.loads(read(self.h(".copilot/mcp-config.json")))["mcpServers"]["samepage"]
        self.assertEqual((cli["type"], cli["tools"]), ("local", ["*"]))
        vscode_dir = os.path.expanduser(setup._vscode_user())
        self.assertFalse(os.path.exists(os.path.join(vscode_dir, "mcp.json")))
        os.makedirs(vscode_dir)
        self.setup_tool("copilot")
        vs = json.loads(read(os.path.join(vscode_dir, "mcp.json")))["servers"]["samepage"]
        self.assertEqual(vs["type"], "stdio")
        self.assertEqual(vs["args"][-1], "copilot")
        self.assertIn("--tool copilot", read(os.path.join(self.project, ".github", "copilot-instructions.md")))

    def test_unverified_paths_print_snippet_only(self):
        for tool, rel in (("cursor", ".cursor/mcp.json"), ("windsurf", ".codeium/windsurf/mcp_config.json")):
            code, out, _ = self.setup_tool(tool)
            self.assertEqual(code, 0, tool)
            self.assertIn("not verified", out)
            self.assertIn('"samepage"', out)
            self.assertFalse(os.path.exists(self.h(rel)), tool)
        # Instruction files are samepage-owned new files, written for every listed tool (B33).
        self.assertTrue(os.path.isfile(os.path.join(self.project, ".cursor", "rules", "samepage.mdc")))
        self.assertTrue(os.path.isfile(os.path.join(self.project, ".windsurf", "rules", "samepage.md")))

    def test_claude_code_and_desktop(self):
        code, out, _ = self.setup_tool("claude-code")
        self.assertEqual(code, 0)
        self.assertIn(setup.PLUGIN_COMMAND, out)
        self.assertEqual(os.listdir(self.home), [".claude"])  # only the session-start entry (ADR-0026)
        with open(self.h(".claude/settings.json"), encoding="utf-8") as handle:
            self.assertIn("session-start.sh", handle.read())
        code, out, _ = self.setup_tool("claude-desktop")
        self.assertEqual(code, 0)
        self.assertIn("upload", out)
        path = self.h("Library/Application Support/Claude/claude_desktop_config.json")
        self.assertEqual(os.path.exists(path), sys.platform == "darwin")

    def test_unknown_tools_exit_2(self):
        for tool in ("chatgpt", "gemini_cli", "vscode"):
            code, _, err = self.setup_tool(tool)
            self.assertEqual(code, 2, tool)
            self.assertIn("codex", err)

    def test_outside_a_git_repo(self):
        outside = os.path.join(self.tmp, "plain")
        os.makedirs(outside)
        code, out, _ = run(["setup", "codex", "--cwd", outside])
        self.assertEqual(code, 0)
        self.assertIn("not inside a git repo", out)
        self.assertEqual(os.listdir(outside), [])

    def test_samepage_home_passed_on(self):
        os.environ["SAMEPAGE_HOME"] = os.path.join(self.tmp, "sph")
        try:
            self.setup_tool("gemini")
        finally:
            os.environ.pop("SAMEPAGE_HOME")
        env = json.loads(read(self.h(".gemini/settings.json")))["mcpServers"]["samepage"]["env"]
        self.assertEqual(env["SAMEPAGE_HOME"], os.path.join(self.tmp, "sph"))


@unittest.skipUnless(shutil.which("git") and shutil.which("sh"), "needs git and sh")
class Launcher(unittest.TestCase):
    def test_sp_run_works_without_pythonpath(self):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        done = subprocess.run([sys.executable, os.path.join(ROOT, "sp_run.py"), "--help"], env=env,
                              cwd=tempfile.gettempdir(), capture_output=True, text=True, timeout=30)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("samepage store tools", done.stdout)


class Installer(unittest.TestCase):
    def test_install_creates_shim_that_runs_sp(self):
        tmp = tempfile.mkdtemp()
        try:
            home = os.path.join(tmp, "home")
            os.makedirs(home)
            env = dict(os.environ, HOME=home, SAMEPAGE_HOME=os.path.join(home, ".samepage"),
                       SAMEPAGE_REPO=ROOT, SAMEPAGE_REF="HEAD", SAMEPAGE_NO_START="1")
            done = subprocess.run(["sh", os.path.join(ROOT, "install.sh")], env=env, capture_output=True, text=True,
                                  timeout=120)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            shim = os.path.join(home, ".local", "bin", "sp")
            self.assertTrue(os.access(shim, os.X_OK))
            self.assertIn("sp start", done.stdout)
            ran = subprocess.run([shim, "--help"], env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(ran.returncode, 0, ran.stderr)
            self.assertIn("samepage store tools", ran.stdout)
            decoy = os.path.join(tmp, "decoy")
            os.makedirs(os.path.join(decoy, "sp"))
            with open(os.path.join(decoy, "sp", "__init__.py"), "w", encoding="utf-8") as handle:
                handle.write("raise SystemExit('wrong sp imported')\n")
            ran = subprocess.run([shim, "--help"], env=env, cwd=decoy, capture_output=True, text=True, timeout=30)
            self.assertEqual(ran.returncode, 0, ran.stderr)  # the shim never imports sp from the current folder
            self.assertTrue(os.path.isfile(os.path.join(home, ".samepage", "tool", "sp", "__init__.py")))
            again = subprocess.run(["sh", os.path.join(ROOT, "install.sh")], env=env, capture_output=True,
                                   text=True, timeout=120)
            self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
            self.assertIn("updated", again.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_default_ref_is_newest_release_tag(self):
        tmp = tempfile.mkdtemp()
        try:
            src = os.path.join(tmp, "src")
            os.makedirs(src)
            git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
            subprocess.run(["git", "init", "-q", src], check=True)
            shas = {}
            for tag in ("v1.2.0", "v1.10.0", None):
                subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", str(tag)], cwd=src, check=True)
                if tag:
                    subprocess.run(git + ["tag", tag], cwd=src, check=True)
                    shas[tag] = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=src, capture_output=True,
                                               text=True, check=True).stdout.strip()
            home = os.path.join(tmp, "home")
            os.makedirs(home)
            env = {k: v for k, v in os.environ.items() if k != "SAMEPAGE_REF"}
            env.update(HOME=home, SAMEPAGE_HOME=os.path.join(home, ".samepage"), SAMEPAGE_REPO=src, SAMEPAGE_NO_START="1")
            done = subprocess.run(["sh", os.path.join(ROOT, "install.sh")], env=env, capture_output=True, text=True,
                                  timeout=120)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            self.assertIn("installed v1.10.0 (%s)" % shas["v1.10.0"], done.stdout)  # version order, not text order
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
