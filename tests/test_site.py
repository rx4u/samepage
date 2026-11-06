"""Tests for the landing page release data (ADR-0021, ADR-0022)."""
import importlib.util
import json
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
sys.path.insert(0, ROOT)

_spec = importlib.util.spec_from_file_location("site_data", os.path.join(ROOT, "scripts", "site_data.py"))
site_data = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(site_data)


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return handle.read()


class SiteData(unittest.TestCase):
    def test_data_json_is_current(self):
        self.assertEqual(read("site", "data.json"), site_data.render(site_data.build()),
                         "run python3 scripts/site_data.py")

    def test_check_flag_passes(self):
        out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "site_data.py"), "--check"],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_version_matches_plugin(self):
        data = json.loads(read("site", "data.json"))
        plugin = json.loads(read(".claude-plugin", "plugin.json"))
        self.assertEqual(data["version"], plugin["version"])
        self.assertTrue(data["release_url"].endswith("/v" + plugin["version"]))

    def test_tools_match_mcp_server(self):
        from sp.mcp import tool_specs
        data = json.loads(read("site", "data.json"))
        self.assertEqual(data["tools"]["total"], len(tool_specs()))
        self.assertEqual(len(data["tools"]["read"]) + len(data["tools"]["write"]), data["tools"]["total"])

    def test_tested_only_where_readme_says_so(self):
        data = json.loads(read("site", "data.json"))
        tested = {a["name"] for a in data["adapters"] if a["tested"]}
        readme = read("README.md")
        for name in tested:
            self.assertRegex(readme, r"\| %s \|[^\n]*\| Tested \|" % re.escape(name))


class Page(unittest.TestCase):
    def setUp(self):
        self.html = read("site", "index.html")
        self.data = json.loads(read("site", "data.json"))

    def test_baked_values_match_data(self):
        self.assertIn('data-sp="version" ', self.html)
        self.assertIn(">v%s</span>" % self.data["version"], self.html)
        self.assertIn('href="%s" data-sp="release-link"' % self.data["release_url"], self.html)
        for adapter in self.data["adapters"]:
            self.assertIn(">%s</div>" % adapter["name"], self.html)

    def test_scripts_are_vendored(self):
        for src in re.findall(r'<script[^>]+src="([^"]+)"', self.html):
            self.assertTrue(src.startswith("vendor/"), src)
            self.assertTrue(os.path.isfile(os.path.join(SITE, src)), src)

    def test_no_third_party_hosts_but_fonts(self):
        hosts = set(re.findall(r'(?:src|href)="https?://([^/"]+)', self.html))
        allowed = {"fonts.googleapis.com", "fonts.gstatic.com", "github.com"}
        self.assertTrue(hosts <= allowed, hosts - allowed)

    def test_reduced_motion_is_honoured(self):
        self.assertIn("prefers-reduced-motion", self.html)


if __name__ == "__main__":
    unittest.main()
