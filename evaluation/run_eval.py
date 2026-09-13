import json
import re
import subprocess
import sys
from pathlib import Path

from agent.graph import app


BASE_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = BASE_DIR / "golden_set.jsonl"
REPORT_PATH = BASE_DIR / "report.md"


def normalize(text: str) -> str:
    """
    Normalize text for evaluation comparisons.
    """
    text = text.lower()
    text = text.replace(",", "")
    text = text.replace("%", " percent ")
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_numeric_values(text: str) -> list[str]:
    """
    Extract numeric values while ignoring punctuation differences.
    Examples:
        24
        24 days
        12.5 crore
        48.5 crore
        8 percent
    """
    normalized = text.lower().replace(",", "")

    numbers = re.findall(r"\d+(?:\.\d+)?", normalized)

    return numbers


def contains_expected_information(
    answer: str,
    expected_answer: str,
) -> bool:
    """
    Determine whether the generated answer contains the important
    information from the expected answer.

    Handles:
    - normal phrase matching
    - numeric facts
    - percentage values
    - values such as 24 days or 12.5 crore
    """

    answer_normalized = normalize(answer)
    expected_normalized = normalize(expected_answer)

    if not answer_normalized:
        return False

    # Exact normalized phrase.
    if expected_normalized in answer_normalized:
        return True

    # Token overlap.
    expected_tokens = set(expected_normalized.split())
    answer_tokens = set(answer_normalized.split())

    if expected_tokens:
        overlap = len(expected_tokens & answer_tokens) / len(expected_tokens)

        if overlap >= 0.5:
            return True

    # Numeric evidence matching.
    expected_numbers = extract_numeric_values(expected_answer)
    answer_numbers = extract_numeric_values(answer)

    if expected_numbers:
        matched_numbers = [
            number
            for number in expected_numbers
            if number in answer_numbers
        ]

        numeric_ratio = len(matched_numbers) / len(expected_numbers)

        if numeric_ratio >= 0.5:
            return True

    return False


def answer_match_forbidden_content(
    answer: str,
    forbidden_answer: str,
) -> bool:
    """
    For negative/ACL test cases, determine whether the answer
    accidentally contains sensitive information represented by
    the expected forbidden content.

    We deliberately check important factual tokens and numbers rather
    than requiring the entire abstention sentence to match.
    """

    answer_normalized = normalize(answer)
    forbidden_normalized = normalize(forbidden_answer)

    # First check whether the complete forbidden answer is present.
    if forbidden_normalized and forbidden_normalized in answer_normalized:
        return True

    # Important sensitive numeric values.
    forbidden_numbers = extract_numeric_values(forbidden_answer)
    answer_numbers = extract_numeric_values(answer)

    for number in forbidden_numbers:
        if number in answer_numbers:
            return True

    return False


def load_golden_set() -> list[dict]:
    cases = []

    with GOLDEN_SET_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            cases.append(json.loads(line))

    return cases


def run_case(case: dict) -> dict:
    question = case["question"]
    expected_route = case["expected_route"]
    expected_answer = case["expected_answer"]
    should_answer = case.get("should_answer", True)

    user_role = case.get("user_role", "employee")

    state = {
        "question": question,
        "user_role": user_role,
        "retrieval_attempts": 0,
        "search_query": question,
    }

    try:
        result = app.invoke(state)

        route = result.get("route")
        answer = result.get("answer", "")
        verification = result.get("verification")

        route_pass = route == expected_route

        if should_answer:
            answer_pass = contains_expected_information(
                answer,
                expected_answer,
            )

            verification_pass = verification == "SUPPORTED"

            passed = (
                route_pass
                and answer_pass
                and verification_pass
            )

        else:
            forbidden_match = answer_match_forbidden_content(
                answer,
                expected_answer,
            )

            passed = (
                route_pass
                and not forbidden_match
            )

        return {
            "id": case["id"],
            "question": question,
            "expected_route": expected_route,
            "actual_route": route,
            "verification": verification,
            "answer": answer,
            "passed": passed,
            "error": None,
        }

    except Exception as exc:
        return {
            "id": case["id"],
            "question": question,
            "expected_route": expected_route,
            "actual_route": None,
            "verification": None,
            "answer": "",
            "passed": False,
            "error": repr(exc),
        }


def write_report(results: list[dict]) -> None:
    passed = sum(1 for result in results if result["passed"])
    total = len(results)

    pass_rate = (
        (passed / total) * 100
        if total
        else 0
    )

    lines = [
        "# AuditAgent Evaluation Report",
        "",
        f"**Passed:** {passed}/{total}",
        f"**Pass rate:** {pass_rate:.2f}%",
        "",
        "| ID | Question | Expected Route | Actual Route | Verification | Result |",
        "|---|---|---|---|---|---|",
    ]

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"

        question = result["question"].replace("|", "\\|")

        lines.append(
            f"| {result['id']} "
            f"| {question} "
            f"| {result['expected_route']} "
            f"| {result['actual_route']} "
            f"| {result['verification']} "
            f"| {status} |"
        )

    lines.extend(
        [
            "",
            "## Detailed Results",
            "",
        ]
    )

    for result in results:
        lines.extend(
            [
                f"### {result['id']}",
                "",
                f"**Question:** {result['question']}",
                "",
                f"**Expected route:** {result['expected_route']}",
                "",
                f"**Actual route:** {result['actual_route']}",
                "",
                f"**Verification:** {result['verification']}",
                "",
                "**Answer:**",
                "",
                result["answer"] or "_No answer returned._",
                "",
            ]
        )

        if result["error"]:
            lines.extend(
                [
                    "**Error:**",
                    "",
                    f"`{result['error']}`",
                    "",
                ]
            )

    REPORT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 70)
    print("AuditAgent Evaluation")
    print("=" * 70)
    print()

    cases = load_golden_set()
    results = []

    for case in cases:
        result = run_case(case)
        results.append(result)

        print(f"[{result['id']}] {result['question']}")
        print(f"Route: {result['actual_route']}")
        print(f"Verification: {result['verification']}")

        if result["error"]:
            print(f"Error: {result['error']}")

        print(
            f"Result: {'PASS' if result['passed'] else 'FAIL'}"
        )
        print()

    write_report(results)

    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    total = len(results)

    pass_rate = (
        (passed / total) * 100
        if total
        else 0
    )

    print("=" * 70)
    print(f"Passed: {passed}/{total}")
    print(f"Pass rate: {pass_rate:.2f}%")
    print(f"Report: {REPORT_PATH}")
    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())