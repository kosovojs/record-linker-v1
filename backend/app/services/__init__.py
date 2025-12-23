"""
Services package - business logic layer.

Re-exports all service classes for convenient importing.
"""

from app.services.base import BaseService

__all__ = [
    "BaseService",
]
