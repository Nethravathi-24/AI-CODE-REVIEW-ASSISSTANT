"""Clean Python module with zero static analysis violations."""

from typing import List


def calculate_average(numbers: List[float]) -> float:
    """Calculates arithmetic mean of a list of numbers."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def read_data_safely(filepath: str) -> str:
    """Reads file content safely using context manager."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
