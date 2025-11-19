"""
Sample algorithm to be optimized by the optimize-evaluate workflow.

This is intentionally inefficient to demonstrate the optimization loop.
"""


def find_duplicates(numbers: list[int]) -> list[int]:
    """
    Find all duplicate numbers in a list.

    This implementation is intentionally inefficient (O(n²)).
    The optimizer should improve it to O(n) using a set.

    Args:
        numbers: List of integers

    Returns:
        List of duplicate numbers (without duplicates in result)

    Examples:
        >>> find_duplicates([1, 2, 3, 2, 4, 3])
        [2, 3]
        >>> find_duplicates([1, 2, 3, 4, 5])
        []
        >>> find_duplicates([1, 1, 1, 1])
        [1]
    """
    duplicates = []

    # Inefficient: O(n²) nested loops
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] == numbers[j]:
                # Inefficient: checking if already in duplicates list
                if numbers[i] not in duplicates:
                    duplicates.append(numbers[i])

    return duplicates


def fibonacci(n: int) -> int:
    """
    Calculate nth Fibonacci number.

    This implementation is intentionally inefficient (exponential time).
    The optimizer should improve it using memoization or dynamic programming.

    Args:
        n: Position in Fibonacci sequence (0-indexed)

    Returns:
        nth Fibonacci number

    Examples:
        >>> fibonacci(0)
        0
        >>> fibonacci(1)
        1
        >>> fibonacci(10)
        55
    """
    # Inefficient: exponential time complexity
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def is_prime(n: int) -> bool:
    """
    Check if a number is prime.

    This implementation is inefficient (checks all numbers).
    The optimizer should improve it to only check up to sqrt(n).

    Args:
        n: Number to check

    Returns:
        True if prime, False otherwise

    Examples:
        >>> is_prime(2)
        True
        >>> is_prime(17)
        True
        >>> is_prime(4)
        False
    """
    if n < 2:
        return False

    # Inefficient: checking all numbers from 2 to n-1
    for i in range(2, n):
        if n % i == 0:
            return False

    return True
