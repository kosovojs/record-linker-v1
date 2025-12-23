"""
Domain exceptions for the service layer.

These exceptions are raised by services and caught by API routes
to convert into appropriate HTTP responses.
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base exception for service layer errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(ServiceError):
    """Entity not found."""

    def __init__(self, entity: str, identifier: str | None = None):
        self.entity = entity
        self.identifier = identifier
        message = f"{entity} not found"
        if identifier:
            message = f"{entity} with identifier '{identifier}' not found"
        super().__init__(message)


class ConflictError(ServiceError):
    """Entity already exists or conflict occurred."""

    def __init__(self, entity: str, field: str, value: str):
        self.entity = entity
        self.field = field
        self.value = value
        message = f"{entity} with {field} '{value}' already exists"
        super().__init__(message)


class ValidationError(ServiceError):
    """Validation error in service layer."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


class InvalidStateTransitionError(ServiceError):
    """Invalid status/state transition."""

    def __init__(self, entity: str, current_state: str, target_state: str):
        self.entity = entity
        self.current_state = current_state
        self.target_state = target_state
        message = f"Cannot transition {entity} from '{current_state}' to '{target_state}'"
        super().__init__(message)
