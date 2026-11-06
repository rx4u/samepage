"""Generate and load the store schema (ADR-0003).

`python3 -m sp schema` reads the logical DDL and lookup list in
docs/architecture/data-architecture.md and writes schema/fields.json and
schema/lookups.json. Those two files are what `sp check` and the skill use.
File key naming follows data-architecture.md agent call B18.
"""
import json
import os
import re

from . import SCHEMA_VERSION

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH_DOC = os.path.join(ROOT, "docs", "architecture", "data-architecture.md")
SCHEMA_DIR = os.path.join(ROOT, "schema")

# Physical layout of a GitHub store (data-architecture.md). `None` = not a store file.
LAYOUT = {
    "store_meta": {"path": "store.md", "entity": "store"},
    "profile": {"path": "profile.md", "entity": "profile"},
    "profile_link": {"path": "profile/links/{id8}.md", "entity": "profile_links"},
    "preference": {"path": "rules/{id8}.md", "entity": "rules"},
    "tag": {"path": "tags/{slug}.md", "entity": "tags"},
    "project": {"path": "projects/{slug}.md", "entity": "projects"},
    "ship_event": {"path": "events/{yyyy}/{date}-{project}-{id8}.md", "entity": "ship_events"},
    "decision": {"path": "decisions/{project}/{date}-{id8}.md", "entity": "decisions"},
    "design_asset": {"path": "design/{project}/{id8}.md", "entity": "design_assets"},
    "handoff": {"path": "handoffs/{id8}.md", "entity": "handoffs"},
}

# Columns that are implied and never written to a file (B18).
OMITTED = {("store_meta", "id"), ("profile", "id"), ("profile_link", "profile_id")}

# Entity foreign keys and how they are written (B18).
ENTITY_REFS = {
    "project_id": {"key": "project", "ref": "project", "by": "slug"},
    "superseded_by_id": {"key": "superseded_by", "ref": "decision", "by": "id"},
}

TYPE_MAP = {
    "uuid": "uuid", "text": "text", "smallint": "integer", "integer": "integer",
    "numeric": "number", "boolean": "boolean", "date": "date", "timestamptz": "datetime",
}


def _sql_block(markdown):
    match = re.search(r"```sql\n(.*?)```", markdown, re.S)
    if not match:
        raise ValueError("no ```sql block in data-architecture.md")
    return match.group(1)


def _parse_tables(sql):
    sql = re.sub(r"--[^\n]*", "", sql)
    tables = {}
    for match in re.finditer(r"CREATE TABLE (\w+)\s*\((.*?)\);", sql, re.S):
        name, body = match.group(1), match.group(2)
        columns = []
        for raw in body.split("\n"):
            line = raw.strip().rstrip(",")
            if not line or line.upper().startswith(("PRIMARY KEY", "UNIQUE", "CHECK", "FOREIGN KEY")):
                continue
            parts = line.split()
            col, sqltype = parts[0], parts[1].lower()
            upper = line.upper()
            column = {
                "column": col,
                "sqltype": sqltype,
                "required": "NOT NULL" in upper or "PRIMARY KEY" in upper,
                "unique": " UNIQUE" in upper or "PRIMARY KEY" in upper,
            }
            ref = re.search(r"REFERENCES (\w+)\(", line)
            if ref:
                column["references"] = ref.group(1)
            default = re.search(r"DEFAULT (\S+)", line)
            if default:
                column["default"] = default.group(1)
                column["required"] = False
            maxlen = re.search(r"char_length\(\w+\)\s*<=\s*(\d+)", line)
            if maxlen:
                column["max_length"] = int(maxlen.group(1))
            pattern = re.search(r"~\s*'([^']+)'", line)
            if pattern:
                column["pattern"] = pattern.group(1)
            if re.search(r"CHECK \(id = 1\)", line):
                column["singleton"] = True
            columns.append(column)
        tables[name] = columns
    return tables


def _parse_lookups(markdown):
    section = markdown.split("## Lookup tables", 1)[1].split("\n## ", 1)[0]
    lookups = {}
    for match in re.finditer(r"^\| (\w+) \| Fixed list: ([^|]+)\|", section, re.M):
        lookups[match.group(1)] = [v.strip() for v in match.group(2).split(",")]
    return lookups


def build(markdown):
    tables = _parse_tables(_sql_block(markdown))
    lookups = _parse_lookups(markdown)
    missing = [t for t in lookups if t not in tables]
    if missing:
        raise ValueError("lookups without a table: %s" % ", ".join(missing))
    entities = {}
    for table, layout in LAYOUT.items():
        keys = []
        for col in tables[table]:
            name = col["column"]
            if (table, name) in OMITTED:
                continue
            field = {"column": name, "type": TYPE_MAP[col["sqltype"]], "required": col["required"]}
            for extra in ("max_length", "pattern", "unique"):
                if col.get(extra):
                    field[extra] = col[extra]
            target = col.get("references")
            if target in lookups:
                field["key"] = name[:-3] if name.endswith("_id") else name
                field["type"] = "lookup"
                field["lookup"] = target
            elif name in ENTITY_REFS:
                info = ENTITY_REFS[name]
                field.update({"key": info["key"], "type": "ref", "ref": info["ref"], "ref_by": info["by"]})
            else:
                field["key"] = name
            if name == "body":
                field["in_body"] = True
            keys.append(field)
        if table == "project":
            keys.append({"column": "project_tag.tag_id", "key": "tags", "type": "list", "required": False,
                         "item_pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"})
        entities[table] = {"path": layout["path"], "entity": layout["entity"], "keys": keys}
    fields = {"schema_version": SCHEMA_VERSION, "source": "docs/architecture/data-architecture.md",
              "tables": entities}
    return fields, {"schema_version": SCHEMA_VERSION, "lookups": lookups}


def _dump(obj):
    return json.dumps(obj, indent=2, sort_keys=False) + "\n"


def generate(write=True):
    with open(ARCH_DOC, encoding="utf-8") as handle:
        fields, lookups = build(handle.read())
    outputs = {os.path.join(SCHEMA_DIR, "fields.json"): _dump(fields),
               os.path.join(SCHEMA_DIR, "lookups.json"): _dump(lookups)}
    if write:
        os.makedirs(SCHEMA_DIR, exist_ok=True)
        for path, text in outputs.items():
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
    return outputs


def load(schema_dir=SCHEMA_DIR):
    with open(os.path.join(schema_dir, "fields.json"), encoding="utf-8") as handle:
        fields = json.load(handle)
    with open(os.path.join(schema_dir, "lookups.json"), encoding="utf-8") as handle:
        lookups = json.load(handle)["lookups"]
    return fields, lookups
