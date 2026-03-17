#!/usr/bin/env python3
"""
Simple tests for prime counting implementations.
"""

import math
import unittest

# Try to import Rust module
try:
    import rust_lib
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False

import requests


def is_prime_python(n: int) -> bool:
    """Reference implementation for testing."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    limit = int(math.sqrt(n))
    for i in range(3, limit + 1, 2):
        if n % i == 0:
            return False
    return True


def count_primes_python(n: int) -> int:
    """Reference implementation for testing."""
    count = 0
    for num in range(2, n + 1):
        if is_prime_python(num):
            count += 1
    return count


class TestPrimeCounting(unittest.TestCase):
    """Test cases for prime counting functions."""
    
    # Known values: π(x) = number of primes ≤ x
    KNOWN_VALUES = {
        10: 4,       # 2, 3, 5, 7
        100: 25,
        1000: 168,
        10000: 1229,
    }
    
    def test_python_small_ranges(self):
        """Test Pure Python implementation with small ranges."""
        for n, expected in self.KNOWN_VALUES.items():
            with self.subTest(n=n):
                result = count_primes_python(n)
                self.assertEqual(result, expected, f"Failed for n={n}")
    
    def test_python_edge_cases(self):
        """Test Pure Python with edge cases."""
        self.assertEqual(count_primes_python(0), 0)
        self.assertEqual(count_primes_python(1), 0)
        self.assertEqual(count_primes_python(2), 1)  # Only 2 is prime
        self.assertEqual(count_primes_python(3), 2)  # 2, 3
    
    @unittest.skipUnless(RUST_AVAILABLE, "Rust module not available")
    def test_rust_matches_python(self):
        """Test that Rust implementation matches Python."""
        test_values = [10, 100, 1000, 10000, 100000]
        for n in test_values:
            with self.subTest(n=n):
                python_result = count_primes_python(n)
                rust_result = rust_lib.count_primes(n)
                self.assertEqual(rust_result, python_result, 
                               f"Rust result mismatch for n={n}")
    
    @unittest.skipUnless(RUST_AVAILABLE, "Rust module not available")
    def test_rust_known_values(self):
        """Test Rust implementation with known values."""
        for n, expected in self.KNOWN_VALUES.items():
            with self.subTest(n=n):
                result = rust_lib.count_primes(n)
                self.assertEqual(result, expected, f"Rust failed for n={n}")
    
    def test_go_service_available(self):
        """Test if Go service is running."""
        try:
            response = requests.get("http://localhost:8080/health", timeout=2)
            go_available = response.status_code == 200
        except requests.exceptions.RequestException:
            go_available = False
        
        if not go_available:
            self.skipTest("Go service not running on port 8080")
    
    def test_go_matches_python(self):
        """Test that Go implementation matches Python."""
        try:
            response = requests.get("http://localhost:8080/health", timeout=2)
            if response.status_code != 200:
                self.skipTest("Go service not healthy")
        except requests.exceptions.RequestException:
            self.skipTest("Go service not running on port 8080")
        
        test_values = [10, 100, 1000]
        for n in test_values:
            with self.subTest(n=n):
                python_result = count_primes_python(n)
                response = requests.get(
                    f"http://localhost:8080/count",
                    params={"n": n},
                    timeout=30
                )
                go_result = response.json()["count"]
                self.assertEqual(go_result, python_result,
                               f"Go result mismatch for n={n}")
    
    def test_go_known_values(self):
        """Test Go implementation with known values."""
        try:
            requests.get("http://localhost:8080/health", timeout=2)
        except requests.exceptions.RequestException:
            self.skipTest("Go service not running on port 8080")
        
        for n, expected in self.KNOWN_VALUES.items():
            with self.subTest(n=n):
                response = requests.get(
                    f"http://localhost:8080/count",
                    params={"n": n},
                    timeout=30
                )
                result = response.json()["count"]
                self.assertEqual(result, expected, f"Go failed for n={n}")


class TestIsPrime(unittest.TestCase):
    """Test the is_prime helper function."""
    
    def test_small_primes(self):
        """Test known small primes."""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
        for p in primes:
            with self.subTest(prime=p):
                self.assertTrue(is_prime_python(p))
    
    def test_small_composites(self):
        """Test known composite numbers."""
        composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25]
        for c in composites:
            with self.subTest(composite=c):
                self.assertFalse(is_prime_python(c))
    
    def test_edge_cases(self):
        """Test edge cases."""
        self.assertFalse(is_prime_python(0))
        self.assertFalse(is_prime_python(1))
        self.assertTrue(is_prime_python(2))


if __name__ == "__main__":
    print("=" * 60)
    print("Running Prime Counting Tests")
    print("=" * 60)
    print()
    
    unittest.main(verbosity=2)
