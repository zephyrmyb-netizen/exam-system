"""Structural checks for the AI import service package split."""

import importlib


def test_imports_package_exports_public_import_api():
    imports_pkg = importlib.import_module("backend.imports")
    file_parser = importlib.import_module("backend.imports.file_parser")
    ai_extractor = importlib.import_module("backend.imports.ai_extractor")
    ai_client_calls = importlib.import_module("backend.imports.ai_client_calls")
    import_validator = importlib.import_module("backend.imports.import_validator")
    import_orchestrator = importlib.import_module("backend.imports.import_orchestrator")

    assert imports_pkg.extract_text_and_warnings is file_parser.extract_text_and_warnings
    assert imports_pkg.extract_questions_from_ai_response is ai_extractor.extract_questions_from_ai_response
    assert imports_pkg.call_ai_parse is ai_client_calls.call_ai_parse
    assert imports_pkg.validate_question_item is import_validator.validate_question_item
    assert imports_pkg.preview_import_from_text is import_orchestrator.preview_import_from_text


def test_legacy_imports_service_is_package_orchestrator_alias():
    legacy = importlib.import_module("backend.services.imports_service")
    orchestrator = importlib.import_module("backend.imports.import_orchestrator")

    assert legacy is orchestrator
