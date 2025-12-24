"""
Shared validator mixins for Pydantic schemas.

Provides reusable JSON parsing validators for SQLite compatibility.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import field_validator


def create_json_field_validator(field_name: str, default_value: Any = None):
    """
    Factory function to create JSON field validators for SQLite compatibility.

    SQLite stores JSON as TEXT, so we need to parse it back to dict/list.

    Args:
        field_name: Name of the field to create validator for
        default_value: Default value if field is None (e.g., {} for dicts, [] for lists)
    """
    @field_validator(field_name, mode="before")
    @classmethod
    def parse_json(cls, v):
        if v is None:
            return default_value
        if isinstance(v, str):
            return json.loads(v)
        return v
    return parse_json


class SQLiteJSONMixin:
    """
    Mixin providing common JSON field validators for SQLite compatibility.

    Handles parsing of JSON fields that SQLite stores as TEXT strings.
    Subclasses should define which fields to validate.
    """

    @field_validator("extra_data", mode="before", check_fields=False)
    @classmethod
    def parse_extra_data(cls, v):
        """Parse extra_data field from SQLite TEXT to dict."""
        if v is None:
            return {}
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("tags", mode="before", check_fields=False)
    @classmethod
    def parse_tags(cls, v):
        """Parse tags field from SQLite TEXT to list."""
        if v is None:
            return []
        if isinstance(v, str):
            return json.loads(v)
        return v


class CandidateJSONMixin(SQLiteJSONMixin):
    """
    Mixin for MatchCandidate schemas with SQLite JSON compatibility.

    Handles all JSONB fields: score_breakdown, matched_properties, extra_data, tags
    """

    @field_validator("score_breakdown", "matched_properties", mode="before", check_fields=False)
    @classmethod
    def parse_nullable_json_fields(cls, v):
        """Parse nullable JSON fields from SQLite TEXT."""
        if v is None:
            return None
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("status", mode="before", check_fields=False)
    @classmethod
    def parse_status(cls, v):
        """Parse status enum from string."""
        from app.schemas.enums import CandidateStatus
        if isinstance(v, str):
            return CandidateStatus(v)
        return v

    @field_validator("source", mode="before", check_fields=False)
    @classmethod
    def parse_source(cls, v):
        """Parse source enum from string."""
        from app.schemas.enums import CandidateSource
        if isinstance(v, str):
            return CandidateSource(v)
        return v


class EntryJSONMixin:
    """
    Mixin for DatasetEntry schemas with SQLite JSON compatibility.

    Handles extra_data and raw_data fields.
    """

    @field_validator("extra_data", "raw_data", mode="before", check_fields=False)
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON fields from SQLite TEXT."""
        if v is None:
            return None
        if isinstance(v, str):
            return json.loads(v)
        return v
