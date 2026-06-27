"""Compatibility import for the Phase 2 api package.

The stable public router still lives in backend.routers.practice.
"""

from ..routers.practice import router

__all__ = ["router"]
