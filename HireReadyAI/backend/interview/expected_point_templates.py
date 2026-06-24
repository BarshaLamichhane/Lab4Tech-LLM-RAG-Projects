from __future__ import annotations

import re


PYTHON_TOPIC_TEMPLATES = [
    {
        "topic": "generators",
        "patterns": [r"\bgenerators?\b", r"\byield\b", r"\biterators?\b"],
        "expected_points": [
            "Uses yield or the iterator protocol to produce Python values lazily",
            "Explains that lazy iteration avoids holding the complete result in memory",
            "Handles iteration termination correctly",
            "Discusses when a Python generator is preferable to a fully materialized collection",
        ],
        "scoring_rubric": [
            "Correctly explains Python generator or iterator behavior",
            "Demonstrates valid lazy iteration",
            "Explains memory and execution trade-offs accurately",
            "Addresses relevant edge cases or limitations",
        ],
    },
    {
        "topic": "context_managers",
        "patterns": [r"\bcontext managers?\b", r"\b__enter__\b", r"\b__exit__\b", r"\bwith statement\b"],
        "expected_points": [
            "Implements or explains Python __enter__ and __exit__ methods correctly",
            "Returns the managed resource from __enter__ when appropriate",
            "Releases or cleans up the resource reliably in __exit__",
            "Explains how exceptions are handled by a context manager",
        ],
        "scoring_rubric": [
            "Uses the Python context-manager protocol correctly",
            "Performs reliable resource cleanup",
            "Handles exception behavior accurately",
            "Provides a clear and relevant example",
        ],
    },
    {
        "topic": "decorators",
        "patterns": [r"\bdecorators?\b", r"\bfunctools\.wraps\b"],
        "expected_points": [
            "Explains that a Python decorator receives and wraps a callable",
            "Returns a callable with the intended additional behavior",
            "Preserves wrapped-function metadata when appropriate",
            "Explains practical decorator trade-offs or use cases",
        ],
        "scoring_rubric": [
            "Implements or explains the Python decorator pattern correctly",
            "Preserves function behavior and metadata appropriately",
            "Uses closures and arguments correctly",
            "Provides a relevant use case",
        ],
    },
    {
        "topic": "list_comprehensions",
        "patterns": [r"\blist comprehensions?\b"],
        "expected_points": [
            "Uses valid Python list-comprehension syntax",
            "Applies the requested transformation or filtering condition correctly",
            "Explains readability and memory trade-offs compared with alternatives",
        ],
        "scoring_rubric": [
            "Produces the correct Python result",
            "Uses clear and valid comprehension syntax",
            "Explains when a comprehension is or is not appropriate",
        ],
    },
    {
        "topic": "exception_handling",
        "patterns": [r"\bexception handling\b", r"\btry\b.+\bexcept\b", r"\braise\b"],
        "expected_points": [
            "Catches specific Python exceptions instead of using an unnecessarily broad handler",
            "Preserves useful error context or raises an appropriate exception",
            "Uses finally or cleanup behavior when required",
            "Avoids silently hiding failures",
        ],
        "scoring_rubric": [
            "Uses specific and appropriate Python exception handling",
            "Preserves clear failure behavior",
            "Handles cleanup correctly",
            "Explains relevant trade-offs",
        ],
    },
    {
        "topic": "asyncio",
        "patterns": [r"\basyncio\b", r"\basync\b", r"\bawait\b", r"\bcoroutines?\b"],
        "expected_points": [
            "Explains Python async and await behavior correctly",
            "Uses concurrency for suitable I/O-bound work",
            "Avoids blocking the event loop",
            "Explains task lifecycle, error handling, or cancellation where relevant",
        ],
        "scoring_rubric": [
            "Uses Python asynchronous constructs correctly",
            "Distinguishes concurrency from parallel execution",
            "Avoids blocking operations in the event loop",
            "Addresses errors or cancellation appropriately",
        ],
    },
    {
        "topic": "object_oriented_programming",
        "patterns": [r"\bclasses?\b", r"\binheritance\b", r"\bpolymorphism\b", r"\bencapsulation\b"],
        "expected_points": [
            "Explains the relevant Python object-oriented concept accurately",
            "Uses classes, instances, or inheritance correctly for the question",
            "Describes an appropriate design trade-off",
            "Provides a clear Python example",
        ],
        "scoring_rubric": [
            "Demonstrates correct Python object-oriented behavior",
            "Chooses an appropriate design",
            "Explains trade-offs clearly",
            "Uses a relevant example",
        ],
    },
    {
        "topic": "functions_and_arguments",
        "patterns": [r"\bfunctions?\b", r"\bargs\b", r"\bkwargs\b", r"\bparameters?\b"],
        "expected_points": [
            "Defines or explains the Python function behavior correctly",
            "Handles arguments and return values accurately",
            "Addresses relevant validation or edge cases",
            "Explains readability or API-design considerations",
        ],
        "scoring_rubric": [
            "Produces correct Python function behavior",
            "Uses arguments and return values correctly",
            "Handles relevant edge cases",
            "Communicates the design clearly",
        ],
    },
    {
        "topic": "testing",
        "patterns": [r"\bunit tests?\b", r"\bpytest\b", r"\bmocking\b", r"\btest cases?\b"],
        "expected_points": [
            "Identifies the behavior that the Python test must verify",
            "Covers normal behavior and relevant edge cases",
            "Uses isolation or mocking only where appropriate",
            "Explains how the test detects regressions",
        ],
        "scoring_rubric": [
            "Defines meaningful Python test cases",
            "Covers relevant edge cases",
            "Uses isolation appropriately",
            "Explains expected outcomes clearly",
        ],
    },
    {
        "topic": "data_structures",
        "patterns": [r"\blists?\b", r"\bdictionaries\b", r"\bdicts?\b", r"\bsets?\b", r"\btuples?\b"],
        "expected_points": [
            "Chooses an appropriate Python data structure",
            "Explains the relevant lookup, insertion, or iteration behavior",
            "Addresses time and memory trade-offs",
            "Handles duplicates, ordering, or mutability where relevant",
        ],
        "scoring_rubric": [
            "Selects the correct Python data structure",
            "Explains behavior and complexity accurately",
            "Addresses relevant edge cases",
            "Provides a clear example",
        ],
    },
]


def python_expected_point_template(skill: str, question: str) -> dict[str, object] | None:
    """Return reviewed criteria for a recognized Python topic."""
    if skill.casefold().strip() != "python":
        return None

    normalized_question = " ".join(question.casefold().split())
    for template in PYTHON_TOPIC_TEMPLATES:
        if any(re.search(pattern, normalized_question) for pattern in template["patterns"]):
            return {
                "topic": template["topic"],
                "expected_points": list(template["expected_points"]),
                "scoring_rubric": list(template["scoring_rubric"]),
            }
    return None
