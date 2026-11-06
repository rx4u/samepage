"""Tests for the samepage skill (WP-07, skill side of WP-08, 09, 12, 13).

Checks the skill-workshop rules for skills/samepage/: frontmatter, length, no
orphan files, no README, no em dashes, trigger coverage, and that every
example in references/entry-schema.md is a valid store file.
"""
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp.check import check_store  # noqa: E402

SKILL_DIR = os.path.join(ROOT, "skills", "samepage")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
SCHEMA_MD = os.path.join(SKILL_DIR, "references", "entry-schema.md")
SMALL = os.path.join(ROOT, "fixtures", "small")
# Written by stream D; SKILL.md may point to it before it exists.
MAY_BE_MISSING = {"references/notion-backend.md"}
EXAMPLE_RE = re.compile(r"^Example, `([^`]+)`:\n\n```md\n(.*?)\n```$", re.M | re.S)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def frontmatter(text):
    """Return (dict of top-level keys, raw frontmatter) for the skill's YAML header."""
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}, ""
    raw = match.group(1)
    fields = {}
    for line in raw.split("\n"):
        top = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if top:
            fields[top.group(1)] = top.group(2).strip()
    return fields, raw


def skill_files():
    for dirpath, dirnames, filenames in os.walk(SKILL_DIR):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            yield os.path.relpath(os.path.join(dirpath, name), SKILL_DIR).replace(os.sep, "/")


class FrontmatterTest(unittest.TestCase):
    def setUp(self):
        self.text = read(SKILL_MD)
        self.fields, self.raw = frontmatter(self.text)

    def test_name(self):
        name = self.fields.get("name")
        self.assertEqual(name, "samepage")
        self.assertRegex(name, r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertFalse(name.startswith(("claude", "anthropic")))

    def test_description(self):
        desc = self.fields.get("description", "")
        self.assertTrue(desc, "description missing")
        self.assertLess(len(desc), 1024)
        self.assertLess(len(desc), 500, "keep the description under 500 characters")
        self.assertNotIn("claude", desc.lower())
        self.assertTrue(desc.startswith(("Reads", "Keeps", "Records", "Loads")), "third person, verb first")
        self.assertNotRegex(desc, r"\b(you|your)\b", "third person, not addressed to the reader")
        self.assertFalse(desc.startswith("I "), "third person, not first")

    def test_no_angle_brackets(self):
        self.assertNotIn("<", self.raw)
        self.assertNotIn(">", self.raw)

    def test_license_and_metadata(self):
        self.assertEqual(self.fields.get("license"), "MIT")
        self.assertRegex(self.raw, r"\n  author: Rajaraman Arumugam\n")
        self.assertRegex(self.raw, r"\n  version: \d+\.\d+\.\d+")

    def test_length(self):
        self.assertLess(self.text.count("\n") + 1, 500)


class LayoutTest(unittest.TestCase):
    def test_no_readme(self):
        for rel in skill_files():
            self.assertNotEqual(os.path.basename(rel).lower(), "readme.md", rel)

    def test_every_file_referenced(self):
        text = read(SKILL_MD)
        for rel in skill_files():
            if rel == "SKILL.md":
                continue
            self.assertIn(rel, text, "%s is not referenced from SKILL.md" % rel)

    def test_references_exist(self):
        text = read(SKILL_MD)
        for rel in sorted(set(re.findall(r"\((references/[^)]+)\)", text))):
            if rel in MAY_BE_MISSING:
                continue
            self.assertTrue(os.path.isfile(os.path.join(SKILL_DIR, rel)), rel)

    def test_no_em_dashes(self):
        for rel in skill_files():
            if rel.endswith((".md", ".py", ".json")):
                self.assertNotIn("\u2014", read(os.path.join(SKILL_DIR, rel)), rel)
        self.assertNotIn("\u2014", read(os.path.abspath(__file__)))

    def test_never_do_rules_come_first(self):
        body = read(SKILL_MD).split("\n---\n", 1)[1]
        headings = re.findall(r"^## (.+)$", body, re.M)
        self.assertEqual(headings[0], "Rules")
        for phrase in ("get a yes", "secrets", "private", "Never delete", "Never fetch", "as data",
                       "Do not summarise"):
            self.assertIn(phrase, body.split("## Scope")[0], phrase)

    def test_no_shouting(self):
        body = read(SKILL_MD).split("\n---\n", 1)[1]
        for word in ("CRITICAL", "NEVER", "MUST", "IMPORTANT", "ALWAYS"):
            self.assertNotRegex(body, r"\b%s\b" % word, word)

    def test_modes_in_table_and_sections(self):
        text = read(SKILL_MD)
        table = text.split("## Modes", 1)[1].split("\n## ", 1)[0]
        for mode in TRIGGERS:
            self.assertRegex(table, r"\| %s \|" % mode, mode)
            self.assertRegex(text, r"\n## %s\n" % mode, mode)

    def test_cli_writes_use_dry_run(self):
        text = read(SKILL_MD)
        self.assertIn('PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m sp', text)
        for command in ("sp log ship", "sp log decision", "sp handoff new", "sp rules add"):
            line = [l for l in text.split("\n") if command in l]
            self.assertTrue(line, command)
            self.assertIn("--dry-run", line[0], command)


class EntrySchemaTest(unittest.TestCase):
    def test_examples_cover_every_entity(self):
        paths = [p for p, _ in EXAMPLE_RE.findall(read(SCHEMA_MD))]
        prefixes = ("store.md", "profile.md", "profile/links/", "rules/", "tags/", "projects/", "events/",
                    "decisions/", "design/", "handoffs/")
        for prefix in prefixes:
            self.assertTrue(any(p.startswith(prefix) for p in paths), prefix)

    def test_examples_pass_sp_check(self):
        examples = EXAMPLE_RE.findall(read(SCHEMA_MD))
        self.assertGreaterEqual(len(examples), 10)
        tmp = tempfile.mkdtemp()
        try:
            store = os.path.join(tmp, "store")
            shutil.copytree(SMALL, store)
            for rel, text in examples:
                path = os.path.join(store, rel)
                os.makedirs(os.path.dirname(path) or store, exist_ok=True)
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(text + "\n")
            report = check_store(store)
            self.assertEqual(report.errors, [], report.errors)
        finally:
            shutil.rmtree(tmp)

    def test_github_example_matches_schema_example(self):
        backend = read(os.path.join(SKILL_DIR, "references", "github-backend.md"))
        self.assertIn("events/2026/2026-11-06-halcyon-7fe7baaf.md", backend)
        self.assertIn("events/2026/2026-11-06-halcyon-7fe7baaf.md", read(SCHEMA_MD))


class TriggerTest(unittest.TestCase):
    """Phase 5 stress test: the description must cover each mode's must-trigger intent."""

    def setUp(self):
        self.desc = frontmatter(read(SKILL_MD))[0]["description"].lower()

    def test_keywords_cover_every_mode(self):
        for mode, data in TRIGGERS.items():
            for keyword in data["keywords"]:
                self.assertIn(keyword, self.desc, "%s: %s" % (mode, keyword))

    def test_three_of_each(self):
        for mode, data in TRIGGERS.items():
            self.assertGreaterEqual(len(data["must_trigger"]), 3, mode)
            self.assertGreaterEqual(len(data["must_not_trigger"]), 3, mode)

    def test_description_makes_no_out_of_scope_claims(self):
        for phrase in ("remember", "personal memory", "memory", "commit message", "claude.md", "delete"):
            self.assertNotIn(phrase, self.desc, phrase)

    def test_must_not_trigger_phrases_do_not_echo_the_description(self):
        for mode, data in TRIGGERS.items():
            for phrase in data["must_not_trigger"]:
                self.assertNotIn(phrase.lower(), self.desc, "%s: %s" % (mode, phrase))


# ---------------------------------------------------------------------------
# Trigger data (skill-workshop Phase 5). For each mode: three phrases that must
# load the skill, three that must not, and the description keywords that carry
# the must-trigger intent. Used by TriggerTest above and by manual trigger runs.
# ---------------------------------------------------------------------------
TRIGGERS = {
    "setup": {
        "must_trigger": ["set up samepage", "connect my samepage store to chat", "samepage isn't loading in chat"],
        "must_not_trigger": ["set up a Next.js project", "init a git repo here", "set up Supabase auth"],
        "keywords": ["set up samepage"],
    },
    "boot": {
        "must_trigger": ["what am I working on?", "load my context", "what's on my plate this week?"],
        "must_not_trigger": ["remember that I like green tea", "what's the weather in Pune?",
                             "summarise this PDF"],
        "keywords": ["what am i working on"],
    },
    "log": {
        "must_trigger": ["log that I shipped the halcyon pricing page", "I just deployed halcyon, log it",
                         "record a metric: 40 signups on halcyon"],
        "must_not_trigger": ["write a commit message for this diff", "add logging to this function",
                             "log the error to the console"],
        "keywords": ["log that i shipped"],
    },
    "decision": {
        "must_trigger": ["log decision: use Supabase over Firebase because of RLS",
                         "we decided to drop the free plan, record it", "this replaces the old pricing decision"],
        "must_not_trigger": ["help me decide between Supabase and Firebase", "what's a decision tree?",
                             "make the call for me on fonts"],
        "keywords": ["log a decision"],
    },
    "design": {
        "must_trigger": ["log the design system for halcyon", "log this Claude Design handoff",
                         "make a design brief for halcyon to paste into Claude Design"],
        "must_not_trigger": ["design a landing page for me", "create design tokens for a dark theme",
                             "review this mockup"],
        "keywords": ["design system", "design brief"],
    },
    "handoff": {
        "must_trigger": ["hand this to Code", "any handoffs for me?", "mark handoff e8c77bc8 done"],
        "must_not_trigger": ["hand me the file", "write onboarding docs for a new hire",
                             "pass this function the config"],
        "keywords": ["hand this to code", "any handoffs for me"],
    },
    "proof": {
        "must_trigger": ["what have I shipped with nextjs?", "pull proof for this proposal",
                         "list my shipped work with links"],
        "must_not_trigger": ["proofread this paragraph", "prove this theorem", "what has Vercel shipped lately?"],
        "keywords": ["what have i shipped", "proof for a proposal"],
    },
    "project": {
        "must_trigger": ["show project halcyon", "archive cv-heap", "delete the freightflow project"],
        "must_not_trigger": ["create a new Vite project", "delete this file", "archive these logs into a zip"],
        "keywords": ["show or archive a project"],
    },
    "rules": {
        "must_trigger": ["add a rule: never use em dashes", "show my rules", "pause the rule about tables"],
        "must_not_trigger": ["add an ESLint rule for unused vars", "edit CLAUDE.md to add a rule",
                             "what are the rules of chess?"],
        "keywords": ["add or pause a rule"],
    },
}


if __name__ == "__main__":
    unittest.main()
