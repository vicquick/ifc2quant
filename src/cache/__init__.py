# src/cache/__init__.py
import os
from pathlib import Path

# Protect this file from being deleted
_protected_file = Path(__file__).resolve()

from .manager import CacheManager

__all__ = ['CacheManager']