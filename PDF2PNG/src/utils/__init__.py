"""Utility modules for file operations, error handling, and configuration."""

from .error_handling import (
    UserFriendlyError,
    PDFConversionError,
    FileSystemError,
    ValidationError,
    ErrorSeverity
)
from .path_utils import PathManager

__all__ = [
    "UserFriendlyError",
    "PDFConversionError",
    "FileSystemError",
    "ValidationError",
    "ErrorSeverity",
    "PathManager"
]