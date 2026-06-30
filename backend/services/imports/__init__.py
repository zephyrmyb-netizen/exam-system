"""Compatibility package for the AI import service split.

The active implementation lives in ``backend.imports``.  This package keeps
the planned ``backend.services.imports`` import path available for future
maintenance without changing existing runtime behavior.
"""

from ...imports import *  # noqa: F403

