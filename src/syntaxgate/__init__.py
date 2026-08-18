"""Public API for SyntaxGate."""

from .core import (
    SyntaxIssue,
    SyntaxResult,
    check_content,
    check_file,
    check_paths,
    introduced_regression,
)

__all__ = [
    "SyntaxIssue",
    "SyntaxResult",
    "check_content",
    "check_file",
    "check_paths",
    "introduced_regression",
]

__version__ = "0.1.0"
