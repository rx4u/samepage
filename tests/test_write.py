"""Tests for stream B: the write path and the sp log, handoff, proof, project, rules, brief and nudge
commands (WP-08, WP-09, WP-12, WP-13, CLI edge cases of WP-14).

Each test runs on a temp copy of fixtures/small that is a git clone of a local bare remote, with
SAMEPAGE_HOME pointing at a temp config, so pull, commit and push are real.
"""
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

from sp import config  # noqa: E402
from sp.__main__ import main  # noqa: E402
from sp.check import check_store  # noqa: E402
from sp.frontmatter import parse  # noqa: E402
from sp.index import build_index  # noqa: E402
from sp.log import NUDGE, nudge  # noqa: E402
from sp.proof import proof  # noqa: E402

SMALL = os.path.join(ROOT, "fixtures", "small")
NOW = "2026-11-06T10:00:00Z"
PIN = "11111111-2222-4333-8444-555555555555"


def git(cwd, *args, env=None):
    full = dict(os.environ, **(env or {}))
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t"] + list(args), cwd=cwd, check=True,
                          capture_output=True, text=True, env=full).stdout


def snapshot(store):
    """Every file under the store except .git, with its text."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(store):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            full = os.path.join(dirpath, name)
            with open(full, encoding="utf-8") as handle:
                out[os.path.relpath(full, store)] = handle.read()
    return out


class Store(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old_home = os.environ.get("SAMEPAGE_HOME")
        os.environ["SAMEPAGE_HOME"] = os.path.join(self.tmp, "home")
        seed = os.path.join(self.tmp, "seed")
        shutil.copytree(SMALL, seed)
        git(seed, "init", "-q", "-b", "main")
        ok, message, _ = build_index(seed)
        self.assertTrue(ok, message)
        git(seed, "add", "-A")
        git(seed, "commit", "-qm", "seed")
        self.remote = os.path.join(self.tmp, "remote.git")
        git(self.tmp, "clone", "-q", "--bare", seed, self.remote)
        self.store = os.path.join(self.tmp, "store")
        git(self.tmp, "clone", "-q", self.remote, self.store)
        git(self.store, "config", "user.name", "t")
        git(self.store, "config", "user.email", "t@t")
        config.write({"backend": "github", "store_path": self.store})

    def tearDown(self):
        if self.old_home is None:
            os.environ.pop("SAMEPAGE_HOME", None)
        else:
            os.environ["SAMEPAGE_HOME"] = self.old_home
        shutil.rmtree(self.tmp)

    def sp(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def ok(self, *argv):
        code, out, err = self.sp(*argv)
        self.assertEqual(code, 0, out + err)
        return out

    def fails(self, *argv):
        code, out, err = self.sp(*argv)
        self.assertNotEqual(code, 0, out + err)
        return out + err

    def fields(self, rel):
        with open(os.path.join(self.store, rel), encoding="utf-8") as handle:
            return parse(handle.read())[0]

    def read(self, rel):
        with open(os.path.join(self.store, rel), encoding="utf-8") as handle:
            return handle.read()

    def remote_log(self):
        return subprocess.run(["git", "log", "--format=%s"], cwd=self.remote, capture_output=True, text=True).stdout

    def assert_clean(self):
        self.assertEqual(check_store(self.store).errors, [])
        self.assertEqual(git(self.store, "status", "--porcelain"), "")


class LogShipTest(Store):
    def test_ship_writes_indexes_commits_and_pushes(self):
        out = self.ok("log", "ship", "--project", "halcyon", "--kind", "deployed", "--summary", "Onboarding v2",
                      "--proof-url", "https://halcyon.example.com/v2", "--id", PIN, "--now", NOW)
        rel = "events/2026/2026-11-06-halcyon-11111111.md"
        self.assertEqual(out.strip(), "samepage: wrote %s, updated projects/halcyon.md" % rel)
        event = self.fields(rel)
        self.assertEqual((event["kind"], event["surface"], event["occurred_at"]), ("deployed", "code", NOW))
        project = self.fields("projects/halcyon.md")
        self.assertEqual((project["updated_at"], project["last_verified_at"]), (NOW, NOW))
        self.assertEqual(project["status"], "shipped")
        self.assertIn("- 2026-11-06 halcyon, deployed: Onboarding v2", self.read("index/boot/code.md"))
        self.assertIn("2026-11-06 deployed: Onboarding v2", self.read("index/project/halcyon.md"))
        self.assertIn("samepage: log ship halcyon deployed", self.remote_log())
        self.assert_clean()

    def test_b6_status_rules(self):
        cases = {"vault-cli": ("idea", "shipped"), "precis": ("active", "shipped"),
                 "notion-sync": ("unknown", "shipped"), "runsheet": ("parked", "parked"),
                 "freightflow": ("archived", "archived")}
        for slug, (before, after) in cases.items():
            self.assertEqual(self.fields("projects/%s.md" % slug)["status"], before)
            self.ok("log", "ship", "--project", slug, "--kind", "launched", "--summary", "go", "--now", NOW)
            project = self.fields("projects/%s.md" % slug)
            self.assertEqual(project["status"], after, slug)
            if after == "shipped":
                self.assertEqual(project["shipped_on"], "2026-11-06")
            else:
                self.assertIsNone(project.get("shipped_on"))
        self.ok("log", "ship", "--project", "quote-bot", "--kind", "deployed", "--summary", "go")
        self.assertEqual(self.fields("projects/quote-bot.md")["status"], "active")
        self.ok("log", "ship", "--project", "dagboard", "--kind", "shipped", "--summary", "go", "--now", NOW)
        self.assertEqual(self.fields("projects/dagboard.md")["shipped_on"], "2026-11-06")
        self.ok("log", "ship", "--project", "halcyon", "--kind", "shipped", "--summary", "go", "--now", NOW)
        self.assertEqual(self.fields("projects/halcyon.md")["shipped_on"], "2026-09-14")

    def test_new_project_and_tags(self):
        message = self.fails("log", "ship", "--project", "acme-site", "--kind", "launched", "--summary", "live")
        self.assertIn("--new-project-name", message)
        self.ok("log", "ship", "--project", "acme-site", "--kind", "launched", "--summary", "live",
                "--new-project-name", "Acme site", "--new-project-type", "client_site",
                "--new-project-one-liner", "Marketing site for Acme", "--tag", "nextjs", "--tag", "astro=Astro",
                "--now", NOW)
        project = self.fields("projects/acme-site.md")
        self.assertEqual((project["status"], project["shipped_on"], project["tags"]),
                         ("shipped", "2026-11-06", ["nextjs", "astro"]))
        self.assertEqual(self.fields("tags/astro.md")["label"], "Astro")
        self.assertIn("Acme site (acme-site)", self.read("index/tags/astro.md"))
        self.assert_clean()
        self.assertIn("already exists", self.fails(
            "log", "ship", "--project", "halcyon", "--kind", "launched", "--summary", "x",
            "--new-project-name", "H", "--new-project-type", "product", "--new-project-one-liner", "h"))

    def test_dry_run_writes_nothing_and_pins_reproduce_it(self):
        before = snapshot(self.store)
        out = self.ok("log", "ship", "--project", "halcyon", "--kind", "deployed", "--summary", "dry",
                      "--tag", "react", "--dry-run")
        self.assertEqual(snapshot(self.store), before)
        self.assertEqual(self.remote_log().count("samepage:"), 0)
        self.assertIn("== tags/react.md (new file)", out)
        pin = out.strip().splitlines()[-1].split("add: ", 1)[1].split()
        planned = out.split("== ")[1].split("\n", 1)
        rel = planned[0].split(" ")[0]
        self.ok("log", "ship", "--project", "halcyon", "--kind", "deployed", "--summary", "dry", "--tag", "react", *pin)
        self.assertEqual(self.read(rel).rstrip("\n"), planned[1].strip("\n"))

    def test_collision_regenerates_id(self):
        rel = "events/2026/2026-11-06-halcyon-11111111.md"
        os.makedirs(os.path.dirname(os.path.join(self.store, rel)), exist_ok=True)
        with open(os.path.join(self.store, rel), "w", encoding="utf-8") as handle:
            handle.write("---\nid: 11111111-0000-4000-8000-000000000000\nproject: halcyon\nkind: deployed\n"
                         "surface: code\nsummary: squatter\noccurred_at: %s\ncreated_at: %s\n---\n" % (NOW, NOW))
        git(self.store, "add", "-A")
        git(self.store, "commit", "-qm", "squatter")
        out = self.ok("log", "ship", "--project", "halcyon", "--kind", "deployed", "--summary", "x",
                      "--id", PIN, "--now", NOW)
        self.assertIn("generated a new id", out)
        written = out.strip().splitlines()[-1].split("wrote ")[1].split(",")[0]
        self.assertNotEqual(written, rel)
        self.assertNotEqual(self.fields(written)["id"], PIN)

    def test_check_failure_rolls_back(self):
        with open(os.path.join(self.store, "projects", "broken.md"), "w", encoding="utf-8") as handle:
            handle.write("---\nid: 00000000-0000-4000-8000-000000000000\nslug: broken\n---\n")
        before = snapshot(self.store)
        message = self.fails("log", "ship", "--project", "halcyon", "--kind", "launched", "--summary", "x",
                             "--tag", "brand-new")
        self.assertIn("sp check found", message)
        self.assertIn("projects/broken.md", message)
        self.assertEqual(snapshot(self.store), before)
        self.assertFalse(os.path.isdir(os.path.join(self.store, "events", "2026", "x")))
        self.assertNotIn("samepage:", self.remote_log())

    def test_invalid_entry_is_not_written(self):
        before = snapshot(self.store)
        message = self.fails("log", "ship", "--project", "halcyon", "--kind", "deployed", "--summary", "x" * 281)
        self.assertIn("maximum 280", message)
        self.assertIn("secrets never", self.fails(
            "log", "ship", "--project", "halcyon", "--kind", "deployed",
            "--summary", "key sk-ant-abcdefghijklmnopqrstuvwxyz0123"))
        self.assertIn("needs both", self.fails("log", "ship", "--project", "halcyon", "--kind", "metric",
                                               "--summary", "x", "--metric-value", "4"))
        self.assertIn("no project", self.fails("log", "ship", "--project", "nope", "--kind", "deployed",
                                               "--summary", "x", "--dry-run"))
        self.assertEqual(snapshot(self.store), before)

    def test_pull_conflict_stops_and_writes_nothing(self):
        other = os.path.join(self.tmp, "other")
        git(self.tmp, "clone", "-q", self.remote, other)
        path = os.path.join(other, "projects", "halcyon.md")
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text.replace("outcome: Live with 40 beta users", "outcome: Remote edit"))
        git(other, "commit", "-qam", "remote edit")
        git(other, "push", "-q")
        local = os.path.join(self.store, "projects", "halcyon.md")
        with open(local, "w", encoding="utf-8") as handle:
            handle.write(text.replace("outcome: Live with 40 beta users", "outcome: Local edit"))
        git(self.store, "commit", "-qam", "local edit")
        before = snapshot(self.store)
        message = self.fails("log", "ship", "--project", "ship-gate", "--kind", "deployed", "--summary", "x")
        self.assertIn("pull conflict in projects/halcyon.md", message)
        self.assertEqual(snapshot(self.store), before)
        self.assertFalse(os.path.isdir(os.path.join(self.store, ".git", "rebase-merge")))

    def test_pull_brings_remote_entries_first(self):
        other = os.path.join(self.tmp, "other")
        git(self.tmp, "clone", "-q", self.remote, other)
        os.environ["SAMEPAGE_HOME"], home = os.path.join(self.tmp, "home-other"), os.environ["SAMEPAGE_HOME"]
        config.write({"backend": "github", "store_path": other})
        git(other, "config", "user.name", "o")
        git(other, "config", "user.email", "o@o")
        self.ok("rules", "add", "--rule", "From the other machine.")
        os.environ["SAMEPAGE_HOME"] = home
        self.ok("log", "ship", "--project", "halcyon", "--kind", "deployed", "--summary", "x")
        self.assertIn("From the other machine.", self.read("index/rules.md"))
        log = self.remote_log()
        self.assertLess(log.index("log ship halcyon"), log.index("rule add"))

    def test_push_failure_keeps_commit(self):
        shutil.rmtree(self.remote)
        out = self.ok("log", "ship", "--project", "halcyon", "--kind", "deployed", "--summary", "offline")
        self.assertIn("could not pull", out)
        self.assertIn("committed; push failed", out)
        self.assertIn("samepage: log ship halcyon", git(self.store, "log", "-1", "--format=%s"))

    def test_store_flag_and_missing_config(self):
        os.remove(config.path())
        self.assertIn("no store configured", self.fails("rules", "add", "--rule", "x"))
        self.ok("rules", "add", "--rule", "x", "--store", self.store)


class DecisionDesignTest(Store):
    def test_decision_and_supersede(self):
        out = self.ok("log", "decision", "--project", "halcyon", "--title", "Use Supabase", "--reason", "RLS",
                      "--body", "Long detail.", "--supersedes", "7e80d946", "--id", PIN, "--now", NOW)
        new = "decisions/halcyon/2026-11-06-11111111.md"
        old = "decisions/halcyon/2026-10-03-7e80d946.md"
        self.assertIn("wrote %s, updated %s, projects/halcyon.md" % (new, old), out)
        self.assertIn("Long detail.", self.read(new))
        fields = self.fields(new)
        self.assertEqual((fields["status"], fields["surface"]), ("accepted", "code"))
        replaced = self.fields(old)
        self.assertEqual((replaced["status"], replaced["superseded_by"], replaced["updated_at"]),
                         ("superseded", PIN, NOW))
        section = self.read("index/project/halcyon.md")
        self.assertIn("Use Supabase: RLS", section)
        self.assertNotIn("Decision 2", section)
        self.assert_clean()

    def test_supersede_failures(self):
        self.assertIn("only an accepted", self.fails("log", "decision", "--project", "halcyon", "--title", "t",
                                                     "--reason", "r", "--supersedes", "f06af4b1"))
        self.assertIn("no decision", self.fails("log", "decision", "--project", "halcyon", "--title", "t",
                                                "--reason", "r", "--supersedes", "deadbeef"))
        self.assertIn("no decision", self.fails("log", "decision", "--project", "precis", "--title", "t",
                                                "--reason", "r", "--supersedes", "7e80d946"))
        self.assertIn("not an id", self.fails("log", "decision", "--project", "halcyon", "--title", "t",
                                              "--reason", "r", "--supersedes", "zz"))

    def test_approved_design_system_supersedes_previous(self):
        self.ok("log", "design", "--project", "halcyon", "--kind", "design_system", "--title", "Draft tokens",
                "--tokens-repo-url", "https://code.example.com/a/h", "--tokens-path", "t.json")
        self.assertEqual(self.fields("design/halcyon/b67d0155.md")["status"], "approved")
        out = self.ok("log", "design", "--project", "halcyon", "--kind", "design_system", "--title", "Tokens v2",
                      "--status", "approved", "--tokens-repo-url", "https://code.example.com/a/h",
                      "--tokens-path", "design/v2.json", "--now", NOW)
        self.assertIn("updated design/halcyon/b67d0155.md", out)
        self.assertEqual(self.fields("design/halcyon/b67d0155.md")["status"], "superseded")
        self.assertIn("Use the design tokens in design/v2.json on the default branch of https://code.example.com/a/h",
                      self.ok("brief", "halcyon"))
        self.assertIn("--tokens-repo-url", self.fails("log", "design", "--project", "halcyon", "--kind",
                                                      "design_system", "--title", "x"))
        self.assert_clean()

    def test_handoff_bundle_defaults_to_approved(self):
        out = self.ok("log", "design", "--project", "precis", "--kind", "handoff_bundle",
                      "--title", "Design handoff, no link", "--id", PIN)
        self.assertIn("design/precis/11111111.md", out)
        fields = self.fields("design/precis/11111111.md")
        self.assertEqual((fields["status"], fields["surface"]), ("approved", "code"))
        self.assertNotIn("source_url", fields)


class HandoffTest(Store):
    def test_new_list_show_and_transitions(self):
        out = self.ok("handoff", "new", "--project", "halcyon", "--to", "chat", "--title", "Report back",
                      "--body", "## Brief\n\nDone.", "--id", PIN, "--now", NOW)
        self.assertIn("wrote handoffs/11111111.md, updated projects/halcyon.md", out)
        fields = self.fields("handoffs/11111111.md")
        self.assertEqual((fields["status"], fields["from_surface"], fields["to_surface"]), ("open", "code", "chat"))
        self.assertIn("picked_up_at:", self.read("handoffs/11111111.md"))
        self.assertIn("11111111 [open] halcyon: Report back", self.ok("handoff", "list", "--surface", "chat"))
        self.assertIn("Done.", self.ok("handoff", "show", "11111111"))
        self.ok("handoff", "start", "11111111", "--now", NOW)
        fields = self.fields("handoffs/11111111.md")
        self.assertEqual((fields["status"], fields["picked_up_at"]), ("picked_up", NOW))
        self.assertIn("is picked_up", self.fails("handoff", "start", "11111111"))
        self.ok("handoff", "done", PIN)
        self.assertEqual(self.fields("handoffs/11111111.md")["status"], "done")
        self.assertIsNotNone(self.fields("handoffs/11111111.md")["done_at"])
        self.assertIn("is done", self.fails("handoff", "drop", "11111111"))
        self.assertNotIn("11111111", self.ok("handoff", "list", "--surface", "chat"))
        self.ok("handoff", "drop", "0e49799a", "--now", NOW)
        self.assertEqual(self.fields("handoffs/0e49799a.md")["status"], "dropped")
        self.assertEqual(self.fields("projects/general.md")["last_verified_at"], NOW)
        self.assert_clean()

    def test_rejects_design_and_unknown(self):
        before = snapshot(self.store)
        self.assertIn("B7", self.fails("handoff", "new", "--project", "halcyon", "--to", "design", "--title", "t",
                                       "--body", "b"))
        self.assertIn("no handoff", self.fails("handoff", "start", "abcdef12"))
        self.assertIn("maximum 4000", self.fails("handoff", "new", "--project", "halcyon", "--to", "code",
                                                 "--title", "t", "--body", "b" * 4001))
        self.assertEqual(snapshot(self.store), before)


class ReadCommandsTest(Store):
    def test_proof_pages_and_tag_and(self):
        out = self.ok("proof")
        self.assertIn("total:", out)
        self.assertNotIn("(general)", out)
        both = self.ok("proof", "--tag", "nextjs", "--tag", "supabase")
        self.assertIn("tags: nextjs AND supabase", both)
        self.assertIn("(halcyon)", both)
        nextjs = self.ok("proof", "--tag", "nextjs")
        three = self.ok("proof", "--tag", "nextjs", "--tag", "supabase", "--tag", "ai")
        self.assertIn("(halcyon)", three)
        self.assertLessEqual(three.count("\n- "), both.count("\n- "))
        self.assertLessEqual(both.count("\n- "), nextjs.count("\n- "))
        self.assertIn("at most 3", self.fails("proof", "--tag", "a", "--tag", "b", "--tag", "c", "--tag", "d"))
        self.assertIn("no tag index", self.fails("proof", "--tag", "nosuchtag"))
        self.assertIn("one tag", self.fails("proof", "--tag", "ai", "--tag", "nextjs", "--page", "2"))

    def test_proof_never_above_50_rows(self):
        rows = []
        for n in range(60):
            rows += ["- P%d (p%d) [shipped, product]: one" % (n, n), "  latest: 2026-01-01 shipped: x", "  proof: x"]
        os.makedirs(os.path.join(self.store, "index", "tags"), exist_ok=True)
        for tag in ("big", "huge"):
            with open(os.path.join(self.store, "index", "tags", tag + ".md"), "w", encoding="utf-8") as handle:
                handle.write("built: x\ntotal: 60\n\n" + "\n".join(rows) + "\n")
        _, single = proof(self.store, ["big"])
        self.assertEqual(single.count("\n- "), 50)
        _, both = proof(self.store, ["big", "huge"])
        self.assertEqual(both.count("\n- "), 50)

    def test_project_show_and_archive(self):
        self.assertIn("# Halcyon (shipped, product)", self.ok("project", "halcyon"))
        self.assertIn("no project", self.fails("project", "nope"))
        self.ok("project", "quote-bot", "--archive", "--now", NOW)
        fields = self.fields("projects/quote-bot.md")
        self.assertEqual((fields["status"], fields["archived_at"], fields["updated_at"]), ("archived", NOW, NOW))
        self.assertNotIn("quote-bot:", self.read("index/boot/code.md").split("## Recent ships")[0])
        self.assertIn("(quote-bot)", self.ok("proof"))
        self.assertIn("already archived", self.fails("project", "quote-bot", "--archive"))
        self.assertIn("reserved", self.fails("project", "general", "--archive"))
        self.assert_clean()

    def test_rules(self):
        out = self.ok("rules", "add", "--rule", "Always cite the brief.", "--surface", "chat", "--id", PIN)
        self.assertIn("rules/11111111.md", out)
        self.assertEqual(self.fields("rules/11111111.md")["is_active"], "true")
        self.assertIn("Always cite the brief.", self.ok("rules"))
        self.ok("rules", "pause", "11111111", "--now", NOW)
        self.assertEqual(self.fields("rules/11111111.md")["is_active"], "false")
        self.assertNotIn("Always cite the brief.", self.ok("rules", "list"))
        self.assertIn("already paused", self.fails("rules", "pause", "11111111"))
        self.assertIn("maximum 200", self.fails("rules", "add", "--rule", "x" * 201))
        self.assert_clean()

    def test_brief(self):
        out = self.ok("brief", "halcyon")
        self.assertIn("Project: Halcyon. Halcyon, a product", out)
        self.assertIn("Voice: Direct, lowercase, no fluff", out)
        self.assertIn("Decision 2", out)
        self.assertNotIn("Decision 0", out)
        self.assertIn("Use the design tokens in design/tokens.json on the default branch of "
                      "https://code.example.com/asha-rao/halcyon", out)
        self.assertIn("none approved yet", self.ok("brief", "precis"))
        self.assertIn("no project", self.fails("brief", "nope"))


class NudgeTest(Store):
    def setUp(self):
        super().setUp()
        self.project = os.path.join(self.tmp, "proj")
        os.makedirs(self.project)
        git(self.project, "init", "-q")

    def commit(self, when=None):
        env = {"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when} if when else None
        git(self.project, "commit", "-q", "--allow-empty", "-m", "work", env=env)

    def test_conditions(self):
        self.assertIsNone(nudge(self.project))
        self.commit("2020-01-01T10:00:00Z")
        self.assertIsNone(nudge(self.project))
        self.commit()
        self.assertEqual(nudge(self.project), NUDGE)
        self.ok("log", "ship", "--project", "halcyon", "--kind", "deployed", "--summary", "x")
        self.assertIsNone(nudge(self.project))
        os.remove(config.path())
        self.assertIsNone(nudge(self.project))

    def test_hook_script_prints_one_line_or_nothing(self):
        self.commit()
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=ROOT, CLAUDE_PROJECT_DIR=self.project)
        done = subprocess.run(["sh", os.path.join(ROOT, "hooks", "stop-nudge.sh")], env=env, capture_output=True,
                              text=True, timeout=5)
        self.assertEqual((done.returncode, json.loads(done.stdout)), (0, {"systemMessage": NUDGE}))
        env["CLAUDE_PROJECT_DIR"] = os.path.join(self.tmp, "missing")
        done = subprocess.run(["sh", os.path.join(ROOT, "hooks", "stop-nudge.sh")], env=env, capture_output=True,
                              text=True, timeout=5)
        self.assertEqual((done.returncode, done.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
