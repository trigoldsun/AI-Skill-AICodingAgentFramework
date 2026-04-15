"""Utils module - utility functions."""
import os
import sys

def ensure_dir(path: str) -> None:
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)

def get_version() -> str:
    """Get framework version."""
    return "1.1.0"
