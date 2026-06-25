"""Answer normalization utilities."""

import re
from typing import Any

VALID_QUESTION_TYPES = frozenset({
    "single_choice",
    "multiple_choice",
    "true_false",
    "fill_blank",
    "short_answer",
})

TRUE_VALUES = frozenset({
    "正确", "对", "true", "t", "yes", "y", "✔", "1",
    "a", "a.", "a)",  # 个别用户把 true/false 当 A/B
})
FALSE_VALUES = frozenset({
    "错误", "错", "false", "f", "no", "n", "✘", "0",
    "b", "b.", "b)",
})


def _strip_prefix(text: str) -> str:
    """Remove common Chinese/English prefixes like '选项A', '选A', '答案A'."""
    return re.sub(
        r'^\s*(?:选\s*项|选|答案|答|选择|option\s*|choice\s*)[：:\.\s]*',
        '',
        text,
        flags=re.IGNORECASE,
    ).strip()


def _extract_single_choice(text: str) -> str:
    """Normalize single-choice answer: A, A., 选项A, 选A → A."""
    cleaned = _strip_prefix(text).strip().upper()
    # If it's just a single letter A-D (possibly with trailing punctuation)
    m = re.match(r'^([A-D])[\.\)\s]*$', cleaned)
    if m:
        return m.group(1)
    # Fallback: take the first letter
    if cleaned and cleaned[0] in 'ABCD':
        return cleaned[0]
    return cleaned


def _normalize_true_false(text: str) -> str:
    """Normalize true/false answer to 'True' or 'False'."""
    cleaned = _strip_prefix(text).strip().lower()
    # Remove punctuation and extra spaces
    cleaned = cleaned.strip('.。，,！!？?')
    if cleaned in TRUE_VALUES:
        return "True"
    if cleaned in FALSE_VALUES:
        return "False"
    # If it's literally the Chinese characters
    if '正确' in cleaned or '对' in cleaned:
        return "True"
    if '错误' in cleaned or '错' in cleaned:
        return "False"
    # Keep original if unrecognised
    return text.strip()


def _normalize_multiple_choice(text: str) -> str:
    """
    Normalize multiple-choice answer.
    Accepts: "A,B", "AB", '["A","B"]', "A, B", "A、B" → "A,B"
    """
    cleaned = _strip_prefix(text).strip()

    # Try JSON array: ["A","B"] (also tolerate fullwidth ［ ］ from AI output)
    if cleaned.startswith('[') or cleaned.startswith('［'):
        json_candidate = cleaned
        if json_candidate.startswith('［'):
            json_candidate = '[' + json_candidate[1:].replace('］', ']', 1)
        try:
            import json
            parsed = json.loads(json_candidate)
            if isinstance(parsed, list):
                letters = sorted(
                    _extract_single_choice(item) for item in parsed
                    if isinstance(item, str) and item.strip()
                )
                return ",".join(letters)
        except (json.JSONDecodeError, TypeError):
            pass

    # Split by common separators: comma, 、,  /, space
    parts = re.split(r'[,，、/;\s]+', cleaned)
    letters = []
    for p in parts:
        p = p.strip().upper()
        if not p:
            continue
        # Extract the letter from something like "A." or "选项A"
        m = re.match(r'^([A-Z])[\.\)\s]*$', p)
        if m:
            letters.append(m.group(1))
        elif len(p) == 1 and 'A' <= p <= 'Z':
            letters.append(p)

    # If no separator matched but string is like "AB", split into individual letters
    if not letters:
        upper = cleaned.upper()
        letters = [ch for ch in upper if 'A' <= ch <= 'Z']

    return ",".join(sorted(set(letters))) if letters else text.strip()


def normalize_answer(answer: str, q_type: str) -> str:
    """
    Normalize an answer string based on question type.

    - single_choice:  A/a/选项A → "A"
    - true_false:     正确/对/true/T → "True", 错误/错/false/F → "False"
    - multiple_choice: A,B / AB / ["A","B"] → sorted "A,B"
    - fill_blank / short_answer: stripped as-is (normalization done at compare time)
    """
    if not answer:
        return answer

    answer = answer.strip()

    if q_type == "single_choice":
        normalized = _extract_single_choice(answer)
        # Ensure it's a single uppercase letter
        if len(normalized) == 1 and normalized.isalpha():
            return normalized.upper()
        return normalized

    if q_type == "true_false":
        return _normalize_true_false(answer)

    if q_type == "multiple_choice":
        return _normalize_multiple_choice(answer)

    # fill_blank, short_answer — just strip whitespace
    return answer


# ── Grading helpers ──────────────────────────────────────────────────────

def _normalize_text_for_compare(text: str) -> str:
    """Normalize text for fill_blank / short_answer comparison.

    - Strip leading/trailing whitespace
    - Replace fullwidth punctuation with halfwidth equivalents
    - Collapse multiple whitespace to single space
    - Lowercase for case-insensitive comparison
    """
    if not text:
        return ""

    text = text.strip()

    # Fullwidth → halfwidth mappings
    replacements = {
        "，": ",", "。": ".", "！": "!", "？": "?",
        "；": ";", "：": ":", "（": "(", "）": ")",
        "【": "[", "】": "]", "《": "<", "》": ">",
        "“": '"', "”": '"', "‘": "'", "’": "'",
        "　": " ",  # fullwidth space
        "＠": "@", "＃": "#", "＄": "$", "％": "%",
        "＆": "&", "＊": "*", "＋": "+", "－": "-",
        "／": "/", "＝": "=", "＜": "<", "＞": ">",
    }
    for full, half in replacements.items():
        text = text.replace(full, half)

    # Collapse multiple whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Case-insensitive
    text = text.lower()

    return text


def check_fill_blank_answer(correct_answer: str, user_answer: str) -> bool:
    """Check a fill_blank answer, supporting multiple acceptable answers with ||.

    Example correct answers:
      "TCP"                   → single answer, exact match after normalization
      "TCP||传输控制协议"      → either "TCP" or "传输控制协议" is correct

    Comparison ignores:
    - Leading/trailing whitespace
    - Fullwidth/halfwidth punctuation
    - Case (English)
    - Multiple consecutive spaces
    """
    if not correct_answer:
        return not user_answer.strip()

    user_norm = _normalize_text_for_compare(user_answer)
    if not user_norm:
        return False

    # Split by || for multiple acceptable answers
    acceptable = correct_answer.split("||")
    for ans in acceptable:
        ans_norm = _normalize_text_for_compare(ans)
        if user_norm == ans_norm:
            return True

    return False


def check_short_answer_answer(correct_answer: str, user_answer: str) -> bool:
    """Check a short_answer answer with keyword and alternative support.

    Rules:
    1. If correct_answer contains `||`: any one of the alternatives must match
       (same as fill_blank || logic).
    2. If correct_answer contains `&&`: ALL keywords must appear in user_answer
       (order-insensitive).
    3. If none of the above: keep original strict normalization match.

    Comparison ignores leading/trailing whitespace, fullwidth/halfwidth,
    case, and collapsed spaces (same as fill_blank).
    """
    if not correct_answer:
        return not user_answer.strip()

    user_norm = _normalize_text_for_compare(user_answer)
    if not user_norm:
        return False

    # Rule 1: || alternatives
    if "||" in correct_answer:
        acceptable = correct_answer.split("||")
        for ans in acceptable:
            ans_norm = _normalize_text_for_compare(ans)
            if user_norm == ans_norm:
                return True
        return False

    # Rule 2: && all keywords required
    if "&&" in correct_answer:
        keywords = correct_answer.split("&&")
        for kw in keywords:
            kw_norm = _normalize_text_for_compare(kw)
            if not kw_norm:
                continue
            if kw_norm not in user_norm:
                return False
        return True

    # Rule 3: strict match (legacy behavior)
    correct_norm = _normalize_text_for_compare(correct_answer)
    return user_norm == correct_norm
