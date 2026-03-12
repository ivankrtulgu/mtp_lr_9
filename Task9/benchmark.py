import timeit
from pathlib import Path

from python_impl import fibonacci_python, fibonacci_python_recursive
from rust_wrapper import fibonacci_rust, get_rust_lib_path


ITERATIONS = 100
FIB_N = 30


def run_benchmark():
    print("=" * 70)
    print("RUST vs PYTHON PERFORMANCE BENCHMARK")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  - Fibonacci n: {FIB_N}")
    print(f"  - Iterations: {ITERATIONS}")
    print(f"  - Rust library: {get_rust_lib_path().name}")
    print()

    result_rust = fibonacci_rust(FIB_N)
    result_python = fibonacci_python(FIB_N)

    print(f"Fibonacci({FIB_N}) = {result_rust}")
    print(f"Results match: {result_rust == result_python}")
    print()

    rust_time = timeit.timeit(
        lambda: fibonacci_rust(FIB_N),
        number=ITERATIONS
    )

    python_iter_time = timeit.timeit(
        lambda: fibonacci_python(FIB_N),
        number=ITERATIONS
    )

    recursive_iterations = 10
    python_rec_time = timeit.timeit(
        lambda: fibonacci_python_recursive(FIB_N),
        number=recursive_iterations
    )
    python_rec_time_normalized = python_rec_time * (ITERATIONS / recursive_iterations)

    print("-" * 70)
    print(f"{'Implementation':<35} {'Time (ms)':<15} {'Time/iter (µs)':<15}")
    print("-" * 70)

    rust_ms = rust_time * 1000
    rust_per_iter = (rust_time / ITERATIONS) * 1_000_000
    print(f"{'Rust (cdylib via ctypes)':<35} {rust_ms:<15.3f} {rust_per_iter:<15.3f}")

    python_iter_ms = python_iter_time * 1000
    python_iter_per_iter = (python_iter_time / ITERATIONS) * 1_000_000
    print(f"{'Python (iterative)':<35} {python_iter_ms:<15.3f} {python_iter_per_iter:<15.3f}")

    python_rec_ms = python_rec_time_normalized * 1000
    python_rec_per_iter = (python_rec_time_normalized / ITERATIONS) * 1_000_000
    print(f"{'Python (recursive) normalized':<35} {python_rec_ms:<15.3f} {python_rec_per_iter:<15.3f}")

    print("-" * 70)

    rust_speedup_vs_iter = python_iter_time / rust_time
    rust_speedup_vs_rec = python_rec_time_normalized / rust_time

    print()
    print("SPEEDUP COMPARISON:")
    print(f"  Rust vs Python iterative:  {rust_speedup_vs_iter:.2f}x faster")
    print(f"  Rust vs Python recursive:  {rust_speedup_vs_rec:.2f}x faster")
    print()

    return {
        'rust_time_ms': rust_ms,
        'python_iter_time_ms': python_iter_ms,
        'python_rec_time_ms': python_rec_ms,
        'rust_speedup_iter': rust_speedup_vs_iter,
        'rust_speedup_rec': rust_speedup_vs_rec,
        'results_match': result_rust == result_python
    }


if __name__ == "__main__":
    run_benchmark()
