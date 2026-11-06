"""plugin/ is the folder the marketplace installs and the directory reviews (ADR-0025). It must match its sources."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class PluginBundle(unittest.TestCase):
    def test_plugin_folder_matches_sources(self):
        done = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_plugin.py"), "--check"],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_marketplace_installs_plugin_folder(self):
        import json
        with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json"), encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["plugins"][0]["source"], "./plugin")

    def test_nothing_test_only_ships(self):
        for top in ("tests", "fixtures", "docs", "site", "dist"):
            self.assertFalse(os.path.exists(os.path.join(ROOT, "plugin", top)), top)


if __name__ == "__main__":
    unittest.main()
