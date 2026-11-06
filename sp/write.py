"""The shared write path for every `sp` write command (WP-08, data-architecture.md B9, B12).

A command builds a list of file changes. `apply` then, in this order:
pulls the store (`git pull --rebase`, stop on conflict, B9), writes the files,
runs `sp check` (on errors the write is undone), rebuilds the index, commits
and pushes when a remote exists. `--dry-run` prints the exact paths and file
text and writes nothing. Reads here are single files at known paths; only
check.py and index.py walk the store (guardrails.md).
"""
import datetime
import os
import re
import subprocess
import sys
import uuid

from . import config
from .check import Report, _validate_row, check_store, scan_secrets
from .frontmatter import FrontmatterError, emit, parse
from .index import build_index
from .schema import load as load_schema

GIT_SECONDS = 60
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ID8_RE = re.compile(r"^[0-9a-f]{8}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
RESERVED_PROJECT = "general"


class WriteError(Exception):
    """A write that cannot go ahead. The message is shown to the user as is."""


# ----- time and ids

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value):
    """Accept an ISO date-time with a zone, or a plain date (taken as 00:00Z). Return the canonical text."""
    text = (value or "").strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        text += "T00:00:00Z"
    probe = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.datetime.fromisoformat(probe)
    except ValueError:
        raise WriteError("%r is not an ISO date-time like 2026-11-06T09:30:00Z" % value)
    if parsed.tzinfo is None:
        raise WriteError("%r needs a time zone, for example a trailing Z" % value)
    return text


def utc_date(value):
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.datetime.fromisoformat(text).astimezone(datetime.timezone.utc).date().isoformat()


class Context:
    """Per-command state: store path, the time stamp and the id source.

    `--id` pins the main entity's uuid and `--now` the time, so a dry run and
    the confirmed run produce the same paths and text. Secondary ids (a new
    project or tag in the same write) derive from the pinned id.
    """

    def __init__(self, store, now=None, pin_id=None):
        self.store = store
        self.now = parse_time(now) if now else now_iso()
        if pin_id and not UUID_RE.match(pin_id):
            raise WriteError("--id must be a lowercase uuid")
        self.pin_id = pin_id or str(uuid.uuid4())
        self.issued = 0
        self.notes = []

    def new_id(self):
        self.issued += 1
        if self.issued == 1:
            return self.pin_id
        return str(uuid.uuid5(uuid.UUID(self.pin_id), str(self.issued)))

    def new_path(self, make_path):
        """Return (id, rel) for a new entity whose path depends on its id. B12: on a path collision
        the id is regenerated."""
        new = self.new_id()
        for _ in range(20):
            rel = make_path(new)
            if not os.path.exists(os.path.join(self.store, rel)):
                return new, rel
            self.notes.append("%s already existed, generated a new id" % rel)
            new = str(uuid.uuid4())
        raise WriteError("could not find a free path for %s" % make_path(new))

    def path(self, rel):
        return os.path.join(self.store, rel)

    def exists(self, rel):
        return os.path.isfile(self.path(rel))

    def read(self, rel):
        """Read one store file at a known path. Returns (fields, body) or None."""
        full = self.path(rel)
        if not os.path.isfile(full):
            return None
        with open(full, encoding="utf-8") as handle:
            text = handle.read()
        try:
            return parse(text)
        except FrontmatterError as exc:
            raise WriteError("%s is not a valid store file: %s; fix it or run sp check" % (rel, exc))


# ----- file rendering in schema key order (B18)

_SCHEMA = None


def schema():
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = load_schema()
    return _SCHEMA


def ordered(table, fields, keep_empty=()):
    """Order fields by schema/fields.json. Absent or None values are dropped unless named in
    keep_empty (or already present as empty in a file being updated). Unknown keys keep their place at the end."""
    keys = [k["key"] for k in schema()[0]["tables"][table]["keys"] if not k.get("in_body")]
    out = {}
    for key in keys:
        if key in fields and (fields[key] is not None or key in keep_empty):
            out[key] = fields[key]
        elif key in keep_empty:
            out[key] = None
    for key, value in fields.items():
        if key not in out and (value is not None or key in keep_empty):
            out[key] = value
    return out


class Change:
    def __init__(self, table, rel, fields, body="", new=True):
        self.table = table
        self.rel = rel
        self.fields = fields
        self.body = body
        self.new = new
        self.text = emit(fields, body)


def new_file(table, rel, fields, body="", keep_empty=()):
    return Change(table, rel, ordered(table, fields, keep_empty), body, new=True)


def updated_file(table, rel, fields, body):
    empty = tuple(k for k, v in fields.items() if v is None)
    return Change(table, rel, ordered(table, fields, empty), body, new=False)


# ----- project helpers shared by every command

def check_slug(slug, what="project"):
    if not slug or not SLUG_RE.match(slug):
        raise WriteError("%r is not a valid %s slug (lowercase letters, digits and single hyphens)" % (slug, what))
    return slug


def read_project(ctx, slug):
    check_slug(slug)
    found = ctx.read("projects/%s.md" % slug)
    if found is None:
        raise WriteError("no project %r in the store (projects/%s.md)" % (slug, slug))
    return found


def touch_project(ctx, slug, project=None, extra=None):
    """Return the project file change that every write to a project or its children makes:
    updated_at and last_verified_at set to now, plus any `extra` fields."""
    fields, body = project if project is not None else read_project(ctx, slug)
    fields = dict(fields)
    fields.update(extra or {})
    fields["updated_at"] = ctx.now
    fields["last_verified_at"] = ctx.now
    return updated_file("project", "projects/%s.md" % slug, fields, body)


def norm_id8(value, what):
    text = (value or "").strip().lower()
    if UUID_RE.match(text):
        text = text[:8]
    if not ID8_RE.match(text):
        raise WriteError("%r is not an id; use the 8 characters shown in the %s list" % (value, what))
    return text


# ----- store resolution and git

def resolve_store(arg=None):
    if arg:
        store = os.path.abspath(os.path.expanduser(arg))
    else:
        cfg = config.read()
        if not cfg.get("backend"):
            raise WriteError("no store configured, run /sp init (or pass --store PATH)")
        if cfg["backend"] == "notion":
            raise WriteError("this machine uses a Notion store; write through the samepage skill")
        store = cfg.get("store_path", "")
    if not os.path.isfile(os.path.join(store, "store.md")):
        raise WriteError("%s is not a samepage store (no store.md)" % store)
    return store


def git(store, args, timeout=GIT_SECONDS, identity=False):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    cmd = ["git"]
    if identity:
        cmd += ["-c", "user.name=samepage", "-c", "user.email=samepage@localhost"]
    try:
        return subprocess.run(cmd + args, cwd=store, capture_output=True, text=True, timeout=timeout, env=env,
                              stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise WriteError("git is not installed")
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd + args, 124, "", "timed out after %ds" % timeout)


def is_repo(store):
    return os.path.exists(os.path.join(store, ".git"))


def has_remote(store):
    return is_repo(store) and bool(git(store, ["remote"]).stdout.strip())


def pull(store, out):
    """B9: pull --rebase before writing. A conflict stops the write; being offline does not."""
    done = git(store, ["pull", "--rebase", "--autostash", "-q"])
    if done.returncode == 0:
        return
    conflicts = git(store, ["diff", "--name-only", "--diff-filter=U"]).stdout.split()
    in_rebase = os.path.isdir(os.path.join(store, ".git", "rebase-merge")) or os.path.isdir(
        os.path.join(store, ".git", "rebase-apply"))
    if conflicts or in_rebase:
        if in_rebase:
            git(store, ["rebase", "--abort"])
        raise WriteError("pull conflict in %s; nothing written. Resolve it in %s (git pull --rebase) and run again"
                         % (", ".join(conflicts) or "the store", store))
    reason = (done.stderr or done.stdout).strip().splitlines()
    out("samepage: note: could not pull the store (%s), writing on the local copy"
        % (reason[-1][:120] if reason else "unknown error"))


# ----- validation, apply and rollback

def validate(changes):
    fields_spec, lookups = schema()
    report = Report()
    for change in changes:
        for kind in scan_secrets(change.text):
            report.error(change.rel, "content", "looks like a %s; secrets never go in a store (ADR-0007)" % kind)
        fields, body = parse(change.text)
        _validate_row(change.table, fields_spec["tables"][change.table], lookups, change.rel, fields, body, report)
    return report.errors


def _format_errors(errors):
    return "\n".join("  %s: %s: %s" % e for e in errors[:50])


def _write_files(store, changes):
    """Write changes; return an undo record."""
    undo = {"created": [], "dirs": [], "originals": {}}
    for change in changes:
        full = os.path.join(store, change.rel)
        folder = os.path.dirname(full)
        missing = []
        while not os.path.isdir(folder):
            missing.append(folder)
            folder = os.path.dirname(folder)
        for path in reversed(missing):
            os.mkdir(path)
            undo["dirs"].append(path)
        if os.path.isfile(full):
            with open(full, encoding="utf-8") as handle:
                undo["originals"][full] = handle.read()
        else:
            undo["created"].append(full)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(change.text)
    return undo


def _rollback(undo):
    for path in undo["created"]:
        if os.path.isfile(path):
            os.remove(path)
    for path, text in undo["originals"].items():
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    for path in reversed(undo["dirs"]):
        try:
            os.rmdir(path)
        except OSError:
            pass


def result_line(changes):
    new = [c.rel for c in changes if c.new]
    upd = [c.rel for c in changes if not c.new]
    parts = []
    if new:
        parts.append("wrote " + ", ".join(new))
    if upd:
        parts.append("updated " + ", ".join(upd))
    return "samepage: " + ", ".join(parts)


def print_dry_run(ctx, changes, out):
    out("samepage: dry run, nothing written")
    for change in changes:
        out("")
        out("== %s (%s)" % (change.rel, "new file" if change.new else "update"))
        out(change.text.rstrip("\n"))
    out("")
    pin = "--now %s" % ctx.now
    if ctx.issued:
        pin = "--id %s %s" % (ctx.pin_id, pin)
    out("samepage: to write exactly this, run the same command without --dry-run and add: %s" % pin)


def apply(ctx, changes, summary, dry_run=False, out=print):
    """Write changes through the full write path. Returns an exit code."""
    errors = validate(changes)
    if errors:
        out("samepage: not written, the entry is not valid:\n" + _format_errors(errors))
        return 1
    if dry_run:
        print_dry_run(ctx, changes, out)
        return 0
    store = ctx.store
    undo = _write_files(store, changes)
    try:
        report = check_store(store, check_index=False)
    except Exception as exc:  # never leave a half write behind
        _rollback(undo)
        raise WriteError("check failed to run (%s); nothing written" % exc)
    if report.errors:
        _rollback(undo)
        out("samepage: not written, sp check found %d errors in the store:\n%s"
            % (len(report.errors), _format_errors(report.errors)))
        return 1
    try:
        ok, message, _ = build_index(store)
    except Exception as exc:
        _rollback(undo)
        raise WriteError("index rebuild failed (%s); nothing written" % exc)
    if not ok:
        _rollback(undo)
        out("samepage: not written. " + message)
        return 1
    for note in ctx.notes:
        out("samepage: note: " + note)
    line = result_line(changes)
    if not is_repo(store):
        out(line + " (store is not a git repo, nothing committed)")
        return 0
    git(store, ["add", "-A"])
    identity = not git(store, ["config", "user.email"]).stdout.strip()
    done = git(store, ["commit", "-q", "-m", "samepage: " + summary], identity=identity)
    if done.returncode != 0:
        out(line + " but the commit failed: %s" % (done.stderr or done.stdout).strip()[:200])
        return 1
    if has_remote(store):
        pushed = git(store, ["push", "-q"])
        if pushed.returncode != 0:
            reason = (pushed.stderr or pushed.stdout).strip().splitlines()
            out(line + " (committed; push failed: %s. Run git push in %s)"
                % (reason[-1][:120] if reason else "unknown error", store))
            return 0
    out(line)
    return 0


def run_write(args, build, summary_of):
    """Shared driver: resolve the store, pull, build the changes, apply. `build(ctx, args)` returns
    the changes; `summary_of(args)` the commit summary."""
    try:
        store = resolve_store(getattr(args, "store", None))
        ctx = Context(store, now=getattr(args, "now", None), pin_id=getattr(args, "id", None))
        if not args.dry_run and has_remote(store):
            pull(store, print)
        changes = build(ctx, args)
        return apply(ctx, changes, summary_of(args), dry_run=args.dry_run)
    except WriteError as exc:
        print("samepage: %s" % exc, file=sys.stderr)
        return 1


def add_write_flags(parser):
    parser.add_argument("--store", help="store folder (default: from ~/.samepage/config)")
    parser.add_argument("--dry-run", action="store_true", help="print the exact files and write nothing")
    parser.add_argument("--id", help="pin the new entry's uuid (printed by --dry-run)")
    parser.add_argument("--now", help="pin the time stamp, ISO with zone (printed by --dry-run)")


# ----- serve file reads (read commands never walk raw folders)

def read_index(store, rel):
    full = os.path.join(store, rel)
    if not os.path.isfile(full):
        return None
    with open(full, encoding="utf-8") as handle:
        return handle.read()


def resolve_read_store(arg=None):
    try:
        return resolve_store(arg), None
    except WriteError as exc:
        return None, str(exc)
