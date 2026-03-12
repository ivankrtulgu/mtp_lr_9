import pytest
import timeit
from python_impl import fibonacci_python, fibonacci_python_recursive
from rust_wrapper import fibonacci_rust, RustLib


class TestCorrectness:

    @pytest.mark.parametrize("n,expected", [
        (0, 0),
        (1, 1),
        (2, 1),
        (3, 2),
        (4, 3),
        (5, 5),
        (10, 55),
        (15, 610),
        (20, 6765),
        (25, 75025),
        (30, 832040),
    ])
    def test_fibonacci_values(self, n: int, expected: int):
        assert fibonacci_rust(n) == expected
        assert fibonacci_python(n) == expected

    def test_all_implementations_match(self):
        for n in [0, 1, 5, 10, 15, 20, 25, 30]:
            rust_result = fibonacci_rust(n)
            python_result = fibonacci_python(n)
            assert rust_result == python_result, f"Results differ for n={n}"

    def test_fibonacci_recursive_correctness(self):
        for n in range(0, 15):
            rust_result = fibonacci_rust(n)
            recursive_result = fibonacci_python_recursive(n)
            assert rust_result == recursive_result, f"Recursive results differ for n={n}"

    def test_negative_input_raises(self):
        with pytest.raises(ValueError):
            fibonacci_python(-1)
        with pytest.raises(ValueError):
            fibonacci_rust(-1)


class TestPerformance:

    @pytest.fixture
    def benchmark_config(self):
        return {
            'iterations': 100,
            'fib_n': 30
        }

    def test_rust_faster_than_python_iterative(self, benchmark_config):
        iterations = benchmark_config['iterations']
        fib_n = benchmark_config['fib_n']

        rust_time = timeit.timeit(
            lambda: fibonacci_rust(fib_n),
            number=iterations
        )

        python_time = timeit.timeit(
            lambda: fibonacci_python(fib_n),
            number=iterations
        )

        assert rust_time < python_time * 2, \
            f"Rust ({rust_time:.4f}s) is more than 2x slower than Python ({python_time:.4f}s)"

    def test_rust_faster_than_python_recursive(self, benchmark_config):
        fib_n = 20
        iterations = 10

        rust_time = timeit.timeit(
            lambda: fibonacci_rust(fib_n),
            number=iterations * 10
        )

        python_rec_time = timeit.timeit(
            lambda: fibonacci_python_recursive(fib_n),
            number=iterations
        )

        rust_time_normalized = rust_time / 10
        speedup = python_rec_time / rust_time_normalized

        assert speedup > 5, \
            f"Rust should be >5x faster than recursive Python, got {speedup:.2f}x"

    def test_rust_library_loads(self):
        rust_lib = RustLib()
        assert rust_lib._lib is not None

    def test_consistent_performance(self, benchmark_config):
        iterations = benchmark_config['iterations']
        fib_n = benchmark_config['fib_n']

        times = []
        for _ in range(3):
            rust_time = timeit.timeit(
                lambda: fibonacci_rust(fib_n),
                number=iterations
            )
            times.append(rust_time)

        min_time = min(times)
        max_time = max(times)
        variance = (max_time - min_time) / min_time

        assert variance < 0.5, \
            f"Performance variance too high: {variance:.2%}"


class TestBenchmarkIntegration:

    def test_benchmark_runs(self):
        from benchmark import run_benchmark
        results = run_benchmark()

        assert 'rust_time_ms' in results
        assert 'python_iter_time_ms' in results
        assert 'results_match' in results
        assert results['results_match'] is True

    def test_benchmark_shows_speedup(self):
        from benchmark import run_benchmark
        results = run_benchmark()

        assert results['rust_speedup_rec'] > 1, \
            "Rust should be faster than recursive Python"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
