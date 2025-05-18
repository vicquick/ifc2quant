# ifc_processing/__init__.py
"""
Package initialization for ifc_processing.
Only exposes the main aggregate function.
"""
from .transform import aggregate

__all__ = [
    'aggregate',
]
