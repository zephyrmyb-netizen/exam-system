"""Compatibility alias for the AI import package orchestrator.

Older tests and callers patch ``backend.services.imports_service`` directly.
Alias this module object to the orchestrator so monkeypatches still affect the
runtime code path instead of only changing a thin wrapper namespace.
"""

import sys

from ..imports import import_orchestrator as _orchestrator

sys.modules[__name__] = _orchestrator
