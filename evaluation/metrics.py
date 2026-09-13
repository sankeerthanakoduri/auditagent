from __future__ import annotations

import re
from typing import Iterable


def normalize_text(text: str) -> str:
    """
    Normalize text for deterministic evaluation.
    """
    text = text.lower()
    text = text.replace(",", "")
    text = text.replace("%", " percent ")

    text = re.sub(r"[^a-z0-9.]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_numbers(text: str) -> list[str]:
    """
    Extract integer and decimal numeric values.
    """
    normalized = text.lower().replace(",", "")

    return re.findall(
        r"\d+(?:\.\d+)?",
        normalized,
    )


def token_overlap(
    expected: str,
    actual: str,
) -> float:
    """
    Calculate the proportion of expected tokens
    appearing in the actual answer.
    """
    expected_tokens = set(
        normalize_text(expected).split()
    )

    actual_tokens = set(
        normalize_text(actual).split()
    )

    if not expected_tokens:
        return 0.0

    return len(
        expected_tokens & actual_tokens
    ) / len(expected_tokens)


def numeric_match(
    expected: str,
    actual: str,
) -> float:
    """
    Calculate the proportion of expected numeric
    values appearing in the actual answer.
    """
    expected_numbers = extract_numbers(expected)
    actual_numbers = extract_numbers(actual)

    if not expected_numbers:
        return 0.0

    matched = sum(
        1
        for number in expected_numbers
        if number in actual_numbers
    )

    return matched / len(expected_numbers)


def answer_contains_expected_information(
    expected: str,
    actual: str,
    token_threshold: float = 0.5,
    numeric_threshold: float = 0.5,
) -> bool:
    """
    Determine whether the generated answer contains
    sufficient expected information.
    """
    expected_normalized = normalize_text(expected)
    actual_normalized = normalize_text(actual)

    if not actual_normalized:
        return False

    if expected_normalized in actual_normalized:
        return True

    if token_overlap(expected, actual) >= token_threshold:
        return True

    if numeric_match(expected, actual) >= numeric_threshold:
        return True

    return False


def contains_forbidden_information(
    forbidden_content: Iterable[str],
    answer: str,
) -> bool:
    """
    Determine whether an answer exposes forbidden
    information.

    Forbidden items can be phrases or numeric values.
    """
    normalized_answer = normalize_text(answer)

    for item in forbidden_content:
        normalized_item = normalize_text(item)

        if not normalized_item:
            continue

        if normalized_item in normalized_answer:
            return True

    return False