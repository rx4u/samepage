"""`sp context` instruction blocks (WP-19, ADR-0018, B32, B37)."""
import contextlib
import io
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp import context  # noqa: E402
from sp.__main__ import main  # noqa: E402
from sp.index import build_index  # noqa: E402

USER = "# My project\n\nUse pnpm.\nTabs, not spaces.\n"


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def read(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


class Context(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def path(self, rel):
        return os.path.join(self.dir, rel)

    def ctx(self, *args):
        return run(["context", "--cwd", self.dir] + list(args))

    def test_block_matches_system_design(self):
        doc = read(os.path.join(ROOT, "docs", "architecture", "system-design.md"))
        documented = doc.split("### Instruction block", 1)[1].split("```\n", 1)[1].split("```", 1)[0]
        self.assertEqual(documented, context.TEMPLATE)
        self.assertLessEqual(len(context.block("gemini_cli")), 1500)  # targets.md

    def test_block_holds_no_store_content(self):
        store = os.path.join(self.dir, "store")
        shutil.copytree(os.path.join(ROOT, "fixtures", "small"), store)
        self.assertTrue(build_index(store)[0])
        text = context.block("codex")
        for surface in ("code", "chat", "cowork"):
            for line in read(os.path.join(store, "index", "boot", surface + ".md")).splitlines():
                if len(line.strip()) > 12:
                    self.assertNotIn(line.strip(), text)

    def test_appends_and_keeps_user_lines(self):
        write(self.path("AGENTS.md"), USER)
        code, out, _ = self.ctx("--tool", "codex")
        self.assertEqual(code, 0)
        self.assertIn("wrote AGENTS.md (block added)", out)
        text = read(self.path("AGENTS.md"))
        self.assertTrue(text.startswith(USER + "\n" + context.START))
        self.assertIn("--tool codex --dry-run", text)
        self.assertEqual(text.count(context.START), 1)

    def test_idempotent(self):
        write(self.path("AGENTS.md"), USER)
        self.ctx("--tool", "codex")
        first = read(self.path("AGENTS.md"))
        code, out, _ = self.ctx("--tool", "codex")
        self.assertEqual((code, read(self.path("AGENTS.md"))), (0, first))
        self.assertIn("AGENTS.md unchanged", out)

    def test_replaces_only_between_markers(self):
        after = "\n## Later notes\nKeep this.\n"
        old = USER + "\n" + context.START + "\nold text\n" + context.END + "\n" + after
        write(self.path("GEMINI.md"), old)
        code, _, _ = self.ctx("--tool", "gemini_cli")
        self.assertEqual(code, 0)
        text = read(self.path("GEMINI.md"))
        self.assertTrue(text.startswith(USER + "\n" + context.block("gemini_cli")))
        self.assertTrue(text.endswith(after))
        self.assertNotIn("old text", text)

    def test_no_trailing_newline_and_crlf(self):
        write(self.path("AGENTS.md"), "line one\r\nline two")
        self.ctx("--tool", "codex")
        text = read(self.path("AGENTS.md"))
        self.assertTrue(text.startswith("line one\r\nline two\r\n\r\n" + context.START + "\r\n"))
        self.assertNotRegex(text, r"[^\r]\n")

    def test_broken_markers_refused_and_unchanged(self):
        for broken in (USER + context.START + "\nno end\n",
                       USER + context.END + "\n",
                       USER + context.END + "\n" + context.START + "\n",
                       context.block("codex") + context.block("codex")):
            write(self.path("AGENTS.md"), broken)
            code, _, err = self.ctx("--tool", "codex")
            self.assertEqual(code, 1, broken)
            self.assertIn("not written", err)
            self.assertEqual(read(self.path("AGENTS.md")), broken)

    def test_new_files_and_frontmatter(self):
        for tool, rel in context.TARGETS.items():
            code, _, _ = self.ctx("--tool", tool)
            self.assertEqual(code, 0, tool)
            text = read(self.path(rel))
            self.assertIn("--tool %s --dry-run" % tool, text)
        self.assertTrue(read(self.path(".cursor/rules/samepage.mdc")).startswith("---\ndescription: samepage working context\nalwaysApply: true\n---\n\n" + context.START))
        self.assertTrue(read(self.path(".windsurf/rules/samepage.md")).startswith("---\ntrigger: always_on\n---\n\n" + context.START))

    def test_frontmatter_only_on_new_files(self):
        write(self.path(".cursor/rules/samepage.mdc"), "my own rule\n")
        self.ctx("--tool", "cursor")
        self.assertTrue(read(self.path(".cursor/rules/samepage.mdc")).startswith("my own rule\n\n" + context.START))

    def test_dry_run_writes_nothing(self):
        write(self.path("AGENTS.md"), USER)
        code, out, _ = self.ctx("--tool", "codex", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("would write AGENTS.md (block added)", out)
        self.assertEqual(read(self.path("AGENTS.md")), USER)
        self.assertFalse(os.path.exists(self.path("GEMINI.md")))

    def test_unknown_or_fileless_tool(self):
        for tool in ("claude_code", "chatgpt", "gemini"):
            code, _, err = self.ctx("--tool", tool)
            self.assertEqual(code, 2, tool)
            self.assertIn("codex", err)

    def test_refresh_rewrites_existing_and_creates_none(self):
        stale = USER + "\n" + context.START + "\nCLI: add `--tool copilot --dry-run`\n" + context.END + "\n"
        write(self.path("AGENTS.md"), stale)
        write(self.path("GEMINI.md"), USER + "\n" + context.START + "\nold\n" + context.END + "\n")
        code, out, _ = self.ctx("--refresh")
        self.assertEqual(code, 0)
        self.assertIn("--tool copilot --dry-run", read(self.path("AGENTS.md")))  # keeps the block's tool
        self.assertEqual(read(self.path("GEMINI.md")), USER + "\n" + context.block("gemini_cli"))  # inferred from path
        self.assertFalse(os.path.exists(self.path(".github")))
        self.assertFalse(os.path.exists(self.path(".cursor")))

    def test_refresh_with_no_blocks(self):
        write(self.path("AGENTS.md"), USER)
        code, out, _ = self.ctx("--refresh")
        self.assertEqual(code, 0)
        self.assertIn("no samepage block", out)
        self.assertEqual(read(self.path("AGENTS.md")), USER)


if __name__ == "__main__":
    unittest.main()
