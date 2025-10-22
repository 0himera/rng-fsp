from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, Sequence


@dataclass(slots=True)
class TestOutcome:
    name: str
    passed: bool
    metric: float
    threshold: float
    details: dict[str, float]


def _mean(bits: Sequence[int]) -> float:
    return sum(bits) / len(bits)


def _variance(bits: Sequence[int], mean: float) -> float:
    return sum((b - mean) ** 2 for b in bits) / len(bits)


def frequency_test(bits: Sequence[int]) -> TestOutcome:
    """Monobit frequency test."""
    ones = sum(bits)
    zeros = len(bits) - ones
    balance = (ones - zeros) / len(bits)
    metric = abs(balance)
    threshold = 0.01
    passed = metric < threshold
    return TestOutcome(
        name="frequency",
        passed=passed,
        metric=metric,
        threshold=threshold,
        details={"ones": ones, "zeros": zeros},
    )


def runs_test(bits: Sequence[int]) -> TestOutcome:
    """Runs test following NIST SP 800-22 approximation."""
    n = len(bits)
    pi = _mean(bits)
    if pi in (0.0, 1.0):
        return TestOutcome(
            name="runs",
            passed=False,
            metric=float("inf"),
            threshold=0.0,
            details={"runs": 1, "pi": pi},
        )

    runs = 1 + sum(1 for a, b in zip(bits, bits[1:]) if a != b)
    expected_runs = 2 * n * pi * (1 - pi)
    denominator = 2 * sqrt(2 * n) * pi * (1 - pi)
    z_score = 0.0 if denominator == 0 else abs(runs - expected_runs) / denominator
    threshold = 1.96
    passed = z_score < threshold
    return TestOutcome(
        name="runs",
        passed=passed,
        metric=z_score,
        threshold=threshold,
        details={"runs": runs, "expected_runs": expected_runs, "pi": pi},
    )


def chi_square_test(bits: Sequence[int], block_size: int = 32) -> TestOutcome:
    """Chi-square test on fixed-size blocks."""
    if len(bits) < block_size:
        raise ValueError("sequence too short for chi-square test")
    blocks = [bits[i : i + block_size] for i in range(0, len(bits), block_size)]
    blocks = [b for b in blocks if len(b) == block_size]
    ones_counts = [sum(block) for block in blocks]
    mean = sum(ones_counts) / len(ones_counts)
    expected = block_size / 2
    chi_square = sum((count - expected) ** 2 / expected for count in ones_counts)
    threshold = len(blocks)
    passed = chi_square < threshold
    return TestOutcome(
        name="chi_square",
        passed=passed,
        metric=chi_square,
        threshold=threshold,
        details={"blocks": len(blocks), "mean_ones": mean},
    )


AVAILABLE_TESTS = {
    "frequency": frequency_test,
    "runs": runs_test,
    "chi_square": chi_square_test,
}


def run_selected_tests(bits: Iterable[int], tests: Iterable[str] | None = None) -> list[TestOutcome]:
    bit_list = list(bits)
    if not bit_list:
        raise ValueError("No bits provided for analysis")
    selected = tests or AVAILABLE_TESTS.keys()
    outcomes: list[TestOutcome] = []
    for name in selected:
        if name not in AVAILABLE_TESTS:
            raise ValueError(f"unknown test: {name}")
        test_fn = AVAILABLE_TESTS[name]
        outcome = test_fn(bit_list)
        outcomes.append(outcome)
    return outcomes
