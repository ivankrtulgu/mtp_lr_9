#!/usr/bin/env python3
"""
Benchmark script comparing three approaches for prime counting:
1. Pure Python
2. Python + Rust (PyO3)
3. Python + Go (HTTP service)

Task: Count primes in range [2, n] using trial division up to sqrt(N)
"""

import math
import time
from pathlib import Path

import requests

# Try to import Rust module (will fail if not built)
try:
    import rust_lib
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    print("Warning: rust_lib module not available. Build it with: cd rust_lib && maturin develop")


def is_prime_python(n: int) -> bool:
    """Check if a number is prime using trial division up to sqrt(n)."""
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
    """Count prime numbers in range [2, n] using pure Python."""
    count = 0
    for num in range(2, n + 1):
        if is_prime_python(num):
            count += 1
    return count


def count_primes_rust(n: int) -> int:
    """Count prime numbers in range [2, n] using Rust via PyO3."""
    if not RUST_AVAILABLE:
        raise RuntimeError("Rust module not available")
    return rust_lib.count_primes(n)


def count_primes_go(n: int, port: int = 8080) -> int:
    """Count prime numbers in range [2, n] using Go HTTP service."""
    url = f"http://localhost:{port}/count"
    params = {"n": str(n)}
    
    try:
        response = requests.get(url, params=params, timeout=300)
        response.raise_for_status()
        data = response.json()
        return data["count"]
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise RuntimeError(
                "404 Not Found - Wrong endpoint. Make sure Go service is rebuilt and running.\n"
                "  cd go_service && go build && ./go_service"
            )
        raise RuntimeError(f"Go service HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Go service request failed: {e}")


def run_benchmark(func, n: int, iterations: int = 5) -> tuple[float, int]:
    """
    Run benchmark for a given function.
    
    Args:
        func: Function to benchmark
        n: Upper bound for prime counting
        iterations: Number of iterations to run
    
    Returns:
        tuple: (average_time_ms, result)
    """
    times = []
    result = None
    
    for i in range(iterations):
        start = time.perf_counter()
        result = func(n)
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        times.append(elapsed_ms)
        print(f"  Iteration {i + 1}/{iterations}: {elapsed_ms:.2f} ms")
    
    avg_time = sum(times) / len(times)
    return avg_time, result


def wait_for_go_service(port: int = 8080, timeout: float = 10.0) -> bool:
    """Wait for Go service to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=1)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.1)
    return False


def main():
    print("=" * 70)
    print("BENCHMARK: Prime Counting (trial division up to sqrt(N))")
    print("=" * 70)
    print()
    
    # Test parameters
    n = 1_000_000  # Upper bound for prime counting
    iterations = 5
    
    print(f"Range: [2, {n:,}]")
    print(f"Iterations per method: {iterations}")
    print()
    
    # Expected result: π(1,000,000) = 78,498 primes
    # This is a well-known mathematical constant
    expected_result = 78498
    print(f"Expected result (π({n:,})): {expected_result:,} primes")
    print()
    
    results = {}
    
    # Benchmark 1: Pure Python
    print("-" * 70)
    print("1. Pure Python")
    print("-" * 70)
    try:
        avg_time, result = run_benchmark(count_primes_python, n, iterations)
        results["Pure Python"] = (avg_time, result)
        print(f"Average time: {avg_time:.2f} ms")
        print(f"Result: {result:,} primes")
        assert result == expected_result, f"Result mismatch! Got {result}, expected {expected_result}"
        print("✓ Result verified")
    except Exception as e:
        print(f"Error: {e}")
        results["Pure Python"] = (None, None)
    print()
    
    # Benchmark 2: Rust (PyO3)
    print("-" * 70)
    print("2. Python + Rust (PyO3)")
    print("-" * 70)
    if RUST_AVAILABLE:
        try:
            avg_time, result = run_benchmark(count_primes_rust, n, iterations)
            results["Rust (PyO3)"] = (avg_time, result)
            print(f"Average time: {avg_time:.2f} ms")
            print(f"Result: {result:,} primes")
            assert result == expected_result, f"Result mismatch! Got {result}, expected {expected_result}"
            print("✓ Result verified")
        except Exception as e:
            print(f"Error: {e}")
            results["Rust (PyO3)"] = (None, None)
    else:
        print("Skipped: Rust module not available")
        print("To build: cd rust_lib && maturin develop")
        results["Rust (PyO3)"] = (None, None)
    print()
    
    # Benchmark 3: Go HTTP Service
    print("-" * 70)
    print("3. Python + Go (HTTP Service)")
    print("-" * 70)
    print("NOTE: Go service must be running manually on port 8080")
    print()
    
    go_port = 8080
    
    # Check if Go service is available
    if wait_for_go_service(go_port, timeout=2.0):
        print(f"Go service detected on port {go_port}")
        try:
            avg_time, result = run_benchmark(
                lambda n: count_primes_go(n, go_port), 
                n, 
                iterations
            )
            results["Go (HTTP)"] = (avg_time, result)
            print(f"Average time: {avg_time:.2f} ms")
            print(f"Result: {result:,} primes")
            assert result == expected_result, f"Result mismatch! Got {result}, expected {expected_result}"
            print("✓ Result verified")
        except Exception as e:
            print(f"Error: {e}")
            results["Go (HTTP)"] = (None, None)
    else:
        print(f"Skipped: Go service not running on port {go_port}")
        print("To start: cd go_service && go run main.go")
        results["Go (HTTP)"] = (None, None)
    print()
    
    # Print summary table
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    # Calculate speedup relative to pure Python
    python_time = results.get("Pure Python", (None, None))[0]
    
    print(f"{'Approach':<25} {'Time (ms)':<15} {'Speedup':<15} {'Status'}")
    print("-" * 70)
    
    for name, (avg_time, result) in results.items():
        if avg_time is not None:
            if python_time and avg_time > 0:
                speedup = f"{python_time / avg_time:.2f}x"
            else:
                speedup = "N/A"
            status = "✓" if result == expected_result else "✗"
            print(f"{name:<25} {avg_time:<15.2f} {speedup:<15} {status}")
        else:
            print(f"{name:<25} {'N/A':<15} {'N/A':<15} Skipped")
    
    print()
    print("=" * 70)
    print("Benchmark completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
