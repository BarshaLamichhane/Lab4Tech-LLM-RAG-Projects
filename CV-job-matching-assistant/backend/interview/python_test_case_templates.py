from __future__ import annotations

import json
import re
from typing import Any


MAX_TEST_CASES = 10

PYTHON_TEST_CASE_TEMPLATES = [
    {
        "patterns": [r"\beven numbers?\b", r"\bfilter\b.+\beven\b"],
        "test_cases": [
            {"args": [[1, 2, 3, 4, 5, 6]], "expected_output": [2, 4, 6]},
            {"args": [[1, 3, 5]], "expected_output": []},
            {"args": [[]], "expected_output": []},
        ],
    },
    {
        "patterns": [r"\bpalindrome\b"],
        "test_cases": [
            {"args": ["racecar"], "expected_output": True},
            {"args": ["python"], "expected_output": False},
            {"args": [""], "expected_output": True},
        ],
    },
    {
        "patterns": [r"\bfactorial\b"],
        "test_cases": [
            {"args": [0], "expected_output": 1},
            {"args": [1], "expected_output": 1},
            {"args": [5], "expected_output": 120},
        ],
    },
    {
        "patterns": [r"\bfibonacci\b"],
        "test_cases": [
            {"args": [0], "expected_output": 0},
            {"args": [1], "expected_output": 1},
            {"args": [7], "expected_output": 13},
        ],
    },
    {
        "patterns": [r"\breverse\b.+\bstring\b", r"\bstring\b.+\breverse\b"],
        "test_cases": [
            {"args": ["hello"], "expected_output": "olleh"},
            {"args": [""], "expected_output": ""},
            {"args": ["a"], "expected_output": "a"},
        ],
    },
    {
        "patterns": [r"\bprime number\b", r"\bis prime\b"],
        "test_cases": [
            {"args": [2], "expected_output": True},
            {"args": [7], "expected_output": True},
            {"args": [8], "expected_output": False},
        ],
    },
    {
        "patterns": [r"\bsum\b.+\blist\b", r"\blist\b.+\bsum\b"],
        "test_cases": [
            {"args": [[1, 2, 3]], "expected_output": 6},
            {"args": [[-2, 2]], "expected_output": 0},
            {"args": [[]], "expected_output": 0},
        ],
    },
]


def python_test_cases_for_question(skill: str, question: str) -> list[dict[str, Any]]:
    if skill.casefold().strip() != "python":
        return []

    normalized_question = " ".join(question.casefold().split())
    for template in PYTHON_TEST_CASE_TEMPLATES:
        if any(re.search(pattern, normalized_question) for pattern in template["patterns"]):
            return validate_python_test_cases(template["test_cases"])
    return []


def validate_python_test_cases(test_cases: object) -> list[dict[str, Any]]:
    if not isinstance(test_cases, list):
        return []

    valid: list[dict[str, Any]] = []
    for test_case in test_cases[:MAX_TEST_CASES]:
        if not isinstance(test_case, dict) or "expected_output" not in test_case:
            continue
        if "args" in test_case:
            if not isinstance(test_case["args"], list):
                continue
            candidate = {
                "args": test_case["args"],
                "expected_output": test_case["expected_output"],
            }
        elif "input" in test_case:
            candidate = {
                "input": str(test_case["input"]),
                "expected_output": test_case["expected_output"],
            }
        else:
            continue
        try:
            json.dumps(candidate)
        except (TypeError, ValueError):
            continue
        valid.append(candidate)
    return valid
