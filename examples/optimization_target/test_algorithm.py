"""
Test suite for algorithm.py

These tests verify correctness during optimization.
The optimizer must keep all tests passing.
"""

import pytest
import time
from algorithm import find_duplicates, fibonacci, is_prime


class TestFindDuplicates:
    """Test cases for find_duplicates function."""

    def test_basic_duplicates(self):
        """Should find duplicates in basic list."""
        assert set(find_duplicates([1, 2, 3, 2, 4, 3])) == {2, 3}

    def test_no_duplicates(self):
        """Should return empty list when no duplicates."""
        assert find_duplicates([1, 2, 3, 4, 5]) == []

    def test_all_duplicates(self):
        """Should handle list with all same numbers."""
        assert find_duplicates([1, 1, 1, 1]) == [1]

    def test_empty_list(self):
        """Should handle empty list."""
        assert find_duplicates([]) == []

    def test_single_element(self):
        """Should handle single element list."""
        assert find_duplicates([5]) == []

    def test_performance(self):
        """Performance baseline for find_duplicates."""
        # Test with 1000 numbers
        numbers = list(range(500)) * 2  # 500 duplicates
        start = time.time()
        result = find_duplicates(numbers)
        duration = time.time() - start

        # Should complete in reasonable time (< 1 second even for inefficient version)
        assert duration < 1.0
        assert len(result) == 500  # All numbers are duplicated


class TestFibonacci:
    """Test cases for fibonacci function."""

    def test_base_cases(self):
        """Should handle base cases correctly."""
        assert fibonacci(0) == 0
        assert fibonacci(1) == 1

    def test_small_numbers(self):
        """Should calculate small Fibonacci numbers correctly."""
        assert fibonacci(2) == 1
        assert fibonacci(3) == 2
        assert fibonacci(4) == 3
        assert fibonacci(5) == 5
        assert fibonacci(10) == 55

    def test_sequence(self):
        """Should produce correct sequence."""
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        actual = [fibonacci(i) for i in range(10)]
        assert actual == expected

    def test_performance(self):
        """Performance baseline for fibonacci."""
        # Test with n=20 (should be fast with optimization)
        start = time.time()
        result = fibonacci(20)
        duration = time.time() - start

        # Unoptimized: ~0.01s, Optimized: <0.001s
        # For testing, we allow up to 0.1s even for inefficient version
        assert duration < 0.1
        assert result == 6765  # 20th Fibonacci number


class TestIsPrime:
    """Test cases for is_prime function."""

    def test_small_primes(self):
        """Should identify small prime numbers."""
        assert is_prime(2) is True
        assert is_prime(3) is True
        assert is_prime(5) is True
        assert is_prime(7) is True
        assert is_prime(11) is True

    def test_small_composites(self):
        """Should identify small composite numbers."""
        assert is_prime(4) is False
        assert is_prime(6) is False
        assert is_prime(8) is False
        assert is_prime(9) is False
        assert is_prime(10) is False

    def test_edge_cases(self):
        """Should handle edge cases correctly."""
        assert is_prime(0) is False
        assert is_prime(1) is False
        assert is_prime(-5) is False

    def test_larger_primes(self):
        """Should identify larger prime numbers."""
        assert is_prime(17) is True
        assert is_prime(19) is True
        assert is_prime(97) is True

    def test_larger_composites(self):
        """Should identify larger composite numbers."""
        assert is_prime(100) is False
        assert is_prime(99) is False

    def test_performance(self):
        """Performance baseline for is_prime."""
        # Test with moderately large prime
        start = time.time()
        result = is_prime(9973)  # Prime number
        duration = time.time() - start

        # Unoptimized: ~0.01s, Optimized: <0.001s
        # For testing, we allow up to 0.1s
        assert duration < 0.1
        assert result is True


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
