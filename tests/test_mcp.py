"""Tests for sp mcp, the local stdio MCP server (WP-22, ADR-0018 item 3, read-models.md Screen: MCP session).

Each test class starts one server over stdio against a temp copy of fixtures/small (schema 1.1, index
built, no git remote) with SAMEPAGE_HOME pointing at a temp config, and drives it one line at a time.
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sp import config  # noqa: E402
from sp.index import build_index  # noqa: E402

SMALL = os.path.join(ROOT, "fixtures", "small")
META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}
READ_TOOLS = ("boot", "project", "proof", "handoffs", "handoff_show", "rules")
WRITE_TOOLS = ("log_ship", "log_decision", "handoff_new", "handoff_status", "rule_add")


def make_store(tmp):
    store = os.path.join(tmp, "store")
    shutil.copytree(SMALL, store)
    path = os.path.join(store, "store.md")
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    lines = [("schema_version: 1.1" if line.startswith("schema_version:") else line) for line in text.split("\n")]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    ok, message, _ = build_index(store)
    if not ok:
        raise AssertionError(message)
    return store


def tree(store):
    out = {}
    for dirpath, dirnames, filenames in os.walk(store):
        for name in filenames:
            full = os.path.join(dirpath, name)
            with open(full, encoding="utf-8") as handle:
                out[os.path.relpath(full, store)] = handle.read()
    return out


class Server(object):
    def __init__(self, home, *extra):
        env = dict(os.environ, PYTHONPATH=ROOT, SAMEPAGE_HOME=home)
        env.pop("SAMEPAGE_TOOL", None)
        self.proc = subprocess.Popen([sys.executable, "-m", "sp", "mcp", "--tool", "codex"] + list(extra),
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     env=env, cwd=ROOT)
        self.next_id = 0
        self.lines = []

    def send_raw(self, line):
        self.proc.stdin.write(line.encode("utf-8") + b"\n")
        self.proc.stdin.flush()

    def read(self):
        line = self.proc.stdout.readline().decode("utf-8")
        self.lines.append(line)
        return json.loads(line)

    def request(self, method, params=None):
        self.next_id += 1
        message = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        if params is not None:
            message["params"] = params
        self.send_raw(json.dumps(message))
        reply = self.read()
        assert reply["id"] == self.next_id, reply
        return reply

    def call(self, name, arguments=None, meta=None):
        params = {"name": name, "arguments": arguments or {}}
        if meta:
            params["_meta"] = meta
        return self.request("tools/call", params)

    def close(self):
        self.proc.stdin.close()
        rest = self.proc.stdout.read().decode("utf-8")
        self.proc.stdout.close()
        code = self.proc.wait(timeout=10)
        return code, rest


class Base(unittest.TestCase):
    backend = "github"

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.store = make_store(cls.tmp)
        cls.home = os.path.join(cls.tmp, "home")
        old = os.environ.get("SAMEPAGE_HOME")
        os.environ["SAMEPAGE_HOME"] = cls.home
        try:
            if cls.backend == "notion":
                config.write({"backend": "notion", "notion_page_id": "0" * 32})
            else:
                config.write({"backend": "github", "store_path": cls.store})
        finally:
            if old is None:
                os.environ.pop("SAMEPAGE_HOME", None)
            else:
                os.environ["SAMEPAGE_HOME"] = old
        cls.server = Server(cls.home)

    @classmethod
    def tearDownClass(cls):
        if cls.server.proc.poll() is None:
            cls.server.close()
        shutil.rmtree(cls.tmp)

    def init(self, version="2025-11-25"):
        reply = self.server.request("initialize", {"protocolVersion": version, "capabilities": {},
                                                   "clientInfo": {"name": "test", "version": "0"}})
        self.server.send_raw(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        return reply

    def text(self, reply):
        self.assertNotIn("error", reply)
        return reply["result"]["content"][0]["text"]


class LegacyTest(Base):
    def test_00_before_initialize_needs_a_version(self):
        reply = self.server.request("tools/list")
        self.assertEqual(reply["error"]["code"], -32022)
        self.assertIn("2026-07-28", reply["error"]["data"]["supported"])

    def test_01_initialize_echo_and_fallback(self):
        reply = self.init("2025-06-18")
        result = reply["result"]
        self.assertEqual(result["protocolVersion"], "2025-06-18")
        self.assertEqual(result["capabilities"], {"tools": {}})
        self.assertEqual(result["serverInfo"]["name"], "samepage")
        self.assertTrue(result["instructions"])
        self.assertEqual(self.init("1999-01-01")["result"]["protocolVersion"], "2025-11-25")
        self.assertEqual(self.init("2024-11-05")["result"]["protocolVersion"], "2024-11-05")

    def test_02_initialized_notification_gets_no_reply(self):
        self.init()
        self.server.send_raw(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.server.send_raw(json.dumps({"jsonrpc": "2.0", "method": "notifications/cancelled",
                                         "params": {"requestId": 99}}))
        # the next line on stdout is the ping reply, so neither notification was answered
        self.assertEqual(self.server.request("ping")["result"], {})

    def test_03_tools_list(self):
        self.init()
        tools = self.server.request("tools/list")["result"]["tools"]
        self.assertEqual(sorted(t["name"] for t in tools), sorted(READ_TOOLS + WRITE_TOOLS))
        for tool in tools:
            schema = tool["inputSchema"]
            self.assertEqual(schema["type"], "object")
            self.assertIs(schema["additionalProperties"], False)
            for key in schema.get("required", []):
                self.assertIn(key, schema["properties"])
            for spec in schema["properties"].values():
                self.assertIn(spec["type"], ("string", "integer", "number", "boolean", "array"))
            if tool["name"] in WRITE_TOOLS:
                self.assertIs(tool["annotations"]["readOnlyHint"], False)
                self.assertIs(tool["annotations"]["destructiveHint"], False)
                self.assertEqual(schema["properties"]["dry_run"], {
                    "type": "boolean", "default": True, "description": "true: preview only, nothing written"})
                self.assertEqual(schema["properties"]["confirm"]["type"], "string")
                self.assertIn("dry_run true first", tool["description"])
                self.assertIn("says yes in this turn", tool["description"])
                self.assertIn("Never put secrets", tool["description"])
            else:
                self.assertIs(tool["annotations"]["readOnlyHint"], True)
                self.assertNotIn("dry_run", schema["properties"])
        by_name = {t["name"]: t["inputSchema"] for t in tools}
        self.assertEqual(by_name["proof"]["properties"]["tags"]["maxItems"], 3)
        self.assertEqual(by_name["handoff_new"]["properties"]["to"]["enum"], ["code", "chat", "cowork"])
        self.assertEqual(by_name["handoff_status"]["properties"]["action"]["enum"], ["start", "done", "drop"])
        self.assertEqual(by_name["log_ship"]["required"], ["project", "kind", "summary"])
        self.assertIn("shipped", by_name["log_ship"]["properties"]["kind"]["enum"])
        self.assertEqual(by_name["project"]["required"], ["slug"])

    def test_04_every_read_tool_returns_text(self):
        self.init()
        calls = {"boot": {"project_dir": ROOT}, "project": {"slug": "quote-bot"}, "proof": {"tags": ["ai"]},
                 "handoffs": {"surface": "chat"}, "handoff_show": {"id": "0e49799a"}, "rules": {}}
        for name in READ_TOOLS:
            result = self.server.call(name, calls[name])["result"]
            self.assertIs(result["isError"], False, (name, result))
            text = result["content"][0]["text"]
            self.assertTrue(text.startswith("<samepage data>"), (name, text[:80]))
            self.assertTrue(text.rstrip().endswith("</samepage data>"), name)
        self.assertIn("Never use em dashes.", self.text(self.server.call("rules")))

    def test_05_errors(self):
        self.init()
        self.assertEqual(self.server.call("nope")["error"]["code"], -32602)
        self.assertEqual(self.server.call("project", {})["error"]["code"], -32602)
        self.assertEqual(self.server.call("project", {"slug": "a", "extra": 1})["error"]["code"], -32602)
        self.assertEqual(self.server.call("proof", {"tags": ["a", "b", "c", "d"]})["error"]["code"], -32602)
        self.assertEqual(self.server.request("resources/list")["error"]["code"], -32601)
        self.server.send_raw("{not json")
        reply = self.server.read()
        self.assertEqual((reply["id"], reply["error"]["code"]), (None, -32700))
        self.server.send_raw(json.dumps({"id": 5, "method": "ping"}))
        self.assertEqual(self.server.read()["error"]["code"], -32600)
        # a child exit other than 0 is a normal result with isError
        result = self.server.call("handoff_show", {"id": "ffffffff"})["result"]
        self.assertIs(result["isError"], True)
        self.assertTrue(result["content"][0]["text"])

    def test_06_modern_discover_and_call(self):
        reply = self.server.request("server/discover", {"_meta": META})["result"]
        self.assertEqual(reply["resultType"], "complete")
        self.assertIn("2026-07-28", reply["supportedVersions"])
        self.assertIn("2025-11-25", reply["supportedVersions"])
        self.assertEqual(reply["capabilities"], {"tools": {}})
        self.assertEqual(reply["_meta"]["io.modelcontextprotocol/serverInfo"]["name"], "samepage")
        self.assertEqual(reply["cacheScope"], "private")
        self.assertGreaterEqual(reply["ttlMs"], 0)
        self.assertTrue(reply["instructions"])
        listed = self.server.request("tools/list", {"_meta": META})["result"]
        self.assertEqual(len(listed["tools"]), 11)
        self.assertEqual((listed["resultType"], listed["cacheScope"]), ("complete", "private"))
        self.assertIn("ttlMs", listed)
        called = self.server.call("rules", {}, meta=META)["result"]
        self.assertEqual(called["resultType"], "complete")
        self.assertIn("io.modelcontextprotocol/serverInfo", called["_meta"])
        self.assertIn("<samepage data>", called["content"][0]["text"])

    def test_07_unsupported_modern_version(self):
        reply = self.server.call("rules", {}, meta={"io.modelcontextprotocol/protocolVersion": "1900-01-01"})
        self.assertEqual(reply["error"]["code"], -32022)
        self.assertEqual(reply["error"]["data"]["requested"], "1900-01-01")
        self.assertIn("2026-07-28", reply["error"]["data"]["supported"])

    def test_08_write_without_confirm_writes_nothing(self):
        self.init()
        before = tree(self.store)
        args = {"project": "quote-bot", "title": "Use SQLite", "reason": "small", "dry_run": False}
        result = self.server.call("log_decision", args)["result"]
        self.assertIs(result["isError"], True)
        bad = dict(args, confirm="not-a-token")
        result = self.server.call("log_decision", bad)["result"]
        self.assertIs(result["isError"], True)
        self.assertIn("preview first", result["content"][0]["text"])
        self.assertEqual(tree(self.store), before)

    def test_09_preview_then_confirm_writes(self):
        self.init()
        before = tree(self.store)
        args = {"project": "quote-bot", "title": "Use Postgres", "reason": "scale"}
        preview = self.server.call("log_decision", args)["result"]
        self.assertIs(preview["isError"], False)
        text = preview["content"][0]["text"]
        self.assertIn("dry run, nothing written", text)
        confirm = text.rsplit("\n", 1)[1][len("confirm: "):]
        self.assertEqual(preview["structuredContent"], {"confirm": confirm})
        payload = json.loads(base64.urlsafe_b64decode(confirm + "=" * (-len(confirm) % 4)))
        self.assertEqual(sorted(payload), ["hash", "id", "now"])
        self.assertEqual(len(payload["hash"]), 16)
        self.assertEqual(tree(self.store), before)
        # tampered arguments with a valid confirm are refused
        tampered = dict(args, reason="other", dry_run=False, confirm=confirm)
        refused = self.server.call("log_decision", tampered)["result"]
        self.assertIs(refused["isError"], True)
        self.assertIn("changed since the preview", refused["content"][0]["text"])
        self.assertEqual(tree(self.store), before)
        done = self.server.call("log_decision", dict(args, dry_run=False, confirm=confirm))["result"]
        self.assertIs(done["isError"], False, done)
        after = tree(self.store)
        new = [rel for rel in after if rel not in before]
        self.assertEqual(len(new), 1, new)
        written = after[new[0]]
        self.assertIn("id: %s" % payload["id"], written)
        self.assertIn("tool: codex", written)
        self.assertIn("surface: code", written)
        self.assertIn("title: Use Postgres", written)

    def test_10_handoff_status_start(self):
        self.init()
        path = os.path.join(self.store, "handoffs", "de3122d7.md")
        with open(path, encoding="utf-8") as handle:
            self.assertIn("status: open", handle.read())
        args = {"id": "de3122d7", "action": "start"}
        preview = self.server.call("handoff_status", args)["result"]
        self.assertIs(preview["isError"], False, preview)
        confirm = preview["structuredContent"]["confirm"]
        done = self.server.call("handoff_status", dict(args, dry_run=False, confirm=confirm))["result"]
        self.assertIs(done["isError"], False, done)
        with open(path, encoding="utf-8") as handle:
            self.assertIn("status: picked_up", handle.read())

    def test_10b_rule_add_defaults_to_every_surface(self):
        self.init()
        preview = self.text(self.server.call("rule_add", {"rule": "Write tests first."}))
        self.assertIn("rule: Write tests first.", preview)
        self.assertNotIn("\nsurface:", preview)
        scoped = self.text(self.server.call("rule_add", {"rule": "Use pnpm.", "surface": "code"}))
        self.assertIn("\nsurface: code", scoped)

    def test_11_boot_speed(self):
        self.init()
        times = []
        for _ in range(20):
            start = time.monotonic()
            reply = self.server.call("boot", {"project_dir": ROOT})
            times.append(time.monotonic() - start)
            self.assertIs(reply["result"]["isError"], False)
        times.sort()
        p95 = times[int(0.95 * len(times)) - 1]
        self.assertLess(p95, 1.0, "p95 of 20 boot calls is %.3f s (targets.md: 1 s)" % p95)

    def test_99_every_line_is_json_and_eof_exits(self):
        code, rest = self.server.close()
        self.assertEqual(code, 0)
        self.assertEqual(rest, "")
        self.assertTrue(self.server.lines)
        for line in self.server.lines:
            self.assertTrue(line.endswith("\n"))
            self.assertEqual(line.count("\n"), 1)
            json.loads(line)


class NotionTest(Base):
    backend = "notion"

    def test_notion_store_gets_one_line(self):
        self.init()
        for name, args in (("boot", {}), ("rules", {}), ("rule_add", {"rule": "x"})):
            result = self.server.call(name, args)["result"]
            self.assertIs(result["isError"], False)
            text = result["content"][0]["text"]
            self.assertEqual(text.count("\n"), 0)
            self.assertIn("GitHub stores", text)
            self.assertIn("skill", text)


if __name__ == "__main__":
    unittest.main()
