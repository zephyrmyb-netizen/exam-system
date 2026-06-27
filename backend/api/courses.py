"""Compatibility import for the Phase 2 api package.

The stable public router still lives in backend.routers.courses.
"""

from ..routers.courses import router

__all__ = ["router"]
