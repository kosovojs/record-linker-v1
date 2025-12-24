"""
Shared field validators for Pydantic schemas.

These validators handle SQLite JSON compatibility and other common patterns.
When running with PostgreSQL, JSONB fields return dicts directly.
With SQLite (used in tests), JSON fields may return strings that need parsing.
"""

from __future__ import annotations

import json
from typing import Any


def parse_json_field(v: Any) -> dict[str, Any]:
    """
    Parse a JSON field value, handling SQLite string storage.

    Returns empty dict if value is None.
    """
    if v is None:
        return {}
    if isinstance(v, str):
        return json.loads(v)
    return v


def parse_json_field_nullable(v: Any) -> dict[str, Any] | None:
    """
    Parse a nullable JSON field value, handling SQLite string storage.

    Returns None if value is None.
    """
    if v is None:
        return None
    if isinstance(v, str):
        return json.loads(v)
    return v


def parse_json_list_field(v: Any) -> list[Any]:
    """
    Parse a JSON list field value, handling SQLite string storage.

    Returns empty list if value is None.
    """
    if v is None:
        return []
    if isinstance(v, str):
        return json.loads(v)
    return v


def parse_enum_field(v: Any, enum_class: type) -> Any:
    """
    Parse an enum field value from string if needed.
    """
    if isinstance(v, str):
        return enum_class(v)
    return v
