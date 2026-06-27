"""AI import package public API.

The orchestrator keeps compatibility with the previous service module while
smaller modules expose the main responsibility groups for new code.
"""

from .file_parser import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    SavedUpload,
    cleanup_temp_file,
    extract_text_and_warnings,
    extract_text_from_file,
    extract_text_or_raise,
    save_upload_to_temp,
    validate_upload,
)
from .ai_extractor import (
    build_ai_prompt,
    build_ai_repair_prompt,
    chunk_document_text,
    deduplicate_questions,
    extract_questions_from_ai_response,
    json_candidates_from_text,
    question_items_from_parsed_json,
)
from .ai_client_calls import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OpenAI,
    _build_import_client,
    call_ai_parse,
    call_ai_parse_chunk,
    safe_ai_error_detail,
)
from .import_validator import (
    ensure_questions_found,
    validate_imported_questions,
    validate_question_item,
)
from .import_orchestrator import (
    build_timing,
    elapsed_ms,
    persist_imported_questions,
    preview_import_from_text,
    resolve_target_course,
)

__all__ = [
    "ALLOWED_EXTENSIONS",
    "MAX_FILE_SIZE",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OpenAI",
    "SavedUpload",
    "_build_import_client",
    "build_ai_prompt",
    "build_ai_repair_prompt",
    "build_timing",
    "call_ai_parse",
    "call_ai_parse_chunk",
    "chunk_document_text",
    "cleanup_temp_file",
    "deduplicate_questions",
    "elapsed_ms",
    "ensure_questions_found",
    "extract_questions_from_ai_response",
    "extract_text_and_warnings",
    "extract_text_from_file",
    "extract_text_or_raise",
    "json_candidates_from_text",
    "persist_imported_questions",
    "preview_import_from_text",
    "question_items_from_parsed_json",
    "resolve_target_course",
    "safe_ai_error_detail",
    "save_upload_to_temp",
    "validate_imported_questions",
    "validate_question_item",
    "validate_upload",
]
