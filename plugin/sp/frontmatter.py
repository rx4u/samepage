"""Flat frontmatter: parse and emit (ADR-0003).

A store file is `---`, one `key: value` per line, `---`, then a Markdown body
that is display-only and never parsed. Values are scalars, ISO dates or an
inline list `[a, b]`. No nesting, no multi-line values.
"""
import json
import re

KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class FrontmatterError(ValueError):
    """Raised when a file is not valid flat frontmatter. `field` may be None."""

    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field


def _parse_value(raw, key):
    value = raw.strip()
    if value == "":
        return None
    if value in ("|", ">", "|-", ">-", "|+", ">+"):
        raise FrontmatterError("multi-line values are not allowed", key)
    if value.startswith("{"):
        raise FrontmatterError("nested values are not allowed", key)
    if value.startswith("["):
        if not value.endswith("]"):
            raise FrontmatterError("inline list must end with ]", key)
        inner = value[1:-1].strip()
        if inner == "":
            return []
        items = [_parse_value(part, key) for part in inner.split(",")]
        if any(isinstance(i, list) for i in items):
            raise FrontmatterError("nested lists are not allowed", key)
        return items
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except ValueError:
            raise FrontmatterError("quoted value is not valid", key)
        if not isinstance(parsed, str):
            raise FrontmatterError("quoted value must be a string", key)
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise FrontmatterError("quoted value is not closed", key)
        return value[1:-1].replace("''", "'")
    return value


def parse(text):
    """Return (fields, body). Raises FrontmatterError."""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != "---":
        raise FrontmatterError("file must start with a --- line")
    fields = {}
    end = None
    for number, line in enumerate(lines[1:], start=2):
        line = line.rstrip("\r")
        if line == "---":
            end = number
            break
        if line.strip() == "":
            continue
        if line[0] in (" ", "\t") or line.lstrip().startswith("- "):
            raise FrontmatterError("nested values are not allowed (line %d)" % number)
        if ":" not in line:
            raise FrontmatterError("line %d is not key: value" % number)
        key, raw = line.split(":", 1)
        key = key.strip()
        if not KEY_RE.match(key):
            raise FrontmatterError("invalid key name %r (line %d)" % (key, number))
        if key in fields:
            raise FrontmatterError("duplicate key", key)
        fields[key] = _parse_value(raw, key)
    if end is None:
        raise FrontmatterError("frontmatter is not closed with a --- line")
    body = "\n".join(lines[end:])
    return fields, body


_NEEDS_QUOTES = re.compile(r"(^[\s\[\]{}\"'|>&*!%@`#-])|(:\s)|(\s#)|(\s$)|^(true|false|null|~|yes|no)$", re.I)


def _emit_scalar(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    text = str(value)
    if "\n" in text or "\r" in text:
        raise FrontmatterError("values cannot contain line breaks")
    if text == "" or _NEEDS_QUOTES.search(text):
        return json.dumps(text, ensure_ascii=False)
    return text


def emit(fields, body=""):
    """Render fields (an ordered dict) and a body as a store file."""
    out = ["---"]
    for key, value in fields.items():
        if not KEY_RE.match(key):
            raise FrontmatterError("invalid key name %r" % key)
        if isinstance(value, (list, tuple)):
            rendered = "[" + ", ".join(_emit_scalar(v) for v in value) + "]"
        else:
            rendered = _emit_scalar(value)
        out.append(("%s: %s" % (key, rendered)).rstrip())
    out.append("---")
    text = "\n".join(out) + "\n"
    if body:
        text += "\n" + body.lstrip("\n")
        if not text.endswith("\n"):
            text += "\n"
    return text
