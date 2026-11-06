"""samepage: one shared working context for every AI tool you work in."""

PRODUCT_NAME = "samepage"
SCHEMA_VERSION = "1.1"
MAX_ROWS_PER_READ = 50
DEFAULT_PAGE_SIZE = 20

# Default role (surface) per tool, used when a writer gets a tool and no surface (ADR-0017).
TOOL_ROLES = {
    "claude_code": "code", "codex": "code", "cursor": "code", "copilot": "code",
    "gemini_cli": "code", "windsurf": "code",
    "claude_ai": "chat", "claude_desktop": "chat",
    "cowork": "cowork", "claude_design": "design",
    "other": None,
}


def version_tuple(text):
    """'1.1' -> (1, 1). Anything unreadable sorts as (0, 0)."""
    try:
        major, minor = (text or "").strip().split(".")[:2]
        return int(major), int(minor)
    except ValueError:
        return 0, 0
