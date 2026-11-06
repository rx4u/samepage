"""Tests for WP-02: frontmatter, schema generation and sp check."""
import glob
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp import frontmatter  # noqa: E402
from sp.check import check_store, scan_secrets  # noqa: E402
from sp.schema import generate  # noqa: E402

SMALL = os.path.join(ROOT, "fixtures", "small")
CASES = os.path.join(ROOT, "fixtures", "broken", "cases.json")


class FrontmatterTest(unittest.TestCase):
    def test_round_trip(self):
        fields = {"id": "x", "one_liner": "Answers: fast", "tags": ["a", "b"], "empty": None, "flag": "true"}
        parsed, body = frontmatter.parse(frontmatter.emit(fields, "Body text"))
        self.assertEqual(parsed, {"id": "x", "one_liner": "Answers: fast", "tags": ["a", "b"], "empty": None,
                                  "flag": "true"})
        self.assertEqual(body.strip(), "Body text")

    def test_rejects_nesting_and_multiline(self):
        for text in ("---\na:\n  b: c\n---\n", "---\na: |\n---\n", "---\na: {b: c}\n---\n", "---\na: b\n"):
            with self.assertRaises(frontmatter.FrontmatterError):
                frontmatter.parse(text)

    def test_rejects_line_breaks_on_emit(self):
        with self.assertRaises(frontmatter.FrontmatterError):
            frontmatter.emit({"a": "line\nbreak"})


class SchemaTest(unittest.TestCase):
    def test_generated_files_are_current(self):
        for path, text in generate(write=False).items():
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), text, "%s is stale, run python3 -m sp schema" % path)


class SecretScanTest(unittest.TestCase):
    def test_patterns(self):
        self.assertIn("AWS access key", scan_secrets("AKIAABCDEFGHIJKLMNOP"))
        self.assertIn("private key", scan_secrets("-----BEGIN RSA PRIVATE KEY-----"))
        self.assertIn("card-like number", scan_secrets("4111 1111 1111 1111"))
        self.assertEqual(scan_secrets("phone 2026-11-06 and id 1234567890123"), [])


class CheckTest(unittest.TestCase):
    def test_small_store_passes(self):
        report = check_store(SMALL)
        self.assertEqual(report.errors, [])
        self.assertEqual(report.counts["projects"], 20)
        self.assertEqual(report.counts["ship_events"], 40)

    def test_only_filters_to_one_entity(self):
        report = check_store(SMALL, only="ship_events")
        self.assertEqual(list(report.counts), ["ship_events"])

    def test_broken_cases_fail_on_named_field(self):
        with open(CASES, encoding="utf-8") as handle:
            cases = json.load(handle)["cases"]
        self.assertGreaterEqual(len(cases), 12)
        for case in cases:
            with self.subTest(case=case["name"]):
                store = tempfile.mkdtemp()
                try:
                    shutil.copytree(SMALL, store, dirs_exist_ok=True)
                    _apply(store, case)
                    report = check_store(store)
                    hits = [e for e in report.errors if e[1] == case["expect_field"]
                            and ("expect_path" not in case or e[0] == case["expect_path"])]
                    self.assertTrue(hits, "no error on %s; got %s" % (case["expect_field"], report.errors[:5]))
                finally:
                    shutil.rmtree(store)


def _target(store, case):
    if "file" in case:
        return os.path.join(store, case["file"])
    matches = sorted(glob.glob(os.path.join(store, case["glob"])))
    for path in matches:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        needle = (case.get("replace") or [None])[0] or (case.get("regex_replace") or [None])[0]
        if needle is None or re.search(needle if "regex_replace" in case else re.escape(needle), text):
            return path
    raise AssertionError("no file matches %s" % case)


def _apply(store, case):
    if "rename" in case:
        os.rename(os.path.join(store, case["rename"][0]), os.path.join(store, case["rename"][1]))
        return
    if "copy" in case:
        src, dst = (os.path.join(store, p) for p in case["copy"])
        with open(src, encoding="utf-8") as handle:
            text = handle.read().replace(*case["replace_in_copy"])
        with open(dst, "w", encoding="utf-8") as handle:
            handle.write(text)
        return
    if "create" in case:
        path = os.path.join(store, case["create"][0])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("x" * case["create"][1])
        return
    path = _target(store, case)
    if case.get("delete"):
        os.remove(path)
        return
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if "replace" in case:
        text = text.replace(*case["replace"])
    if "regex_replace" in case:
        pattern, repl = case["regex_replace"]
        text = re.sub(pattern, repl.replace("LONG281", "x" * 281), text, count=1)
    if "append" in case:
        text += case["append"]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


if __name__ == "__main__":
    unittest.main()
