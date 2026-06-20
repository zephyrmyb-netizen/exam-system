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

    # Try JSON array: ["A","B"]
    if cleaned.startswith('[') or cleaned.startswith('['):
        try:
            import json
            parsed = json.loads(cleaned)
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
    - fill_blank / short_answer: stripped as-is
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
