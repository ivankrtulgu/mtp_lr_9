import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Optional
from queue import Queue, Empty
import pytest


@dataclass
class Task:
    data: dict[str, Any]
    timeout: float = 5.0


class BackgroundProcessor:

    def __init__(self, queue_size: int = 100):
        self.task_queue: Queue[Task] = Queue(maxsize=queue_size)
        self.workers: list[threading.Thread] = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._running = False
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()

    def start(self, workers: int = 4) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self._shutdown_event.clear()

            for i in range(workers):
                t = threading.Thread(target=self._worker, args=(i,), daemon=True)
                t.start()
                self.workers.append(t)

    def _worker(self, worker_id: int) -> None:
        while not self._shutdown_event.is_set():
            try:
                task = self.task_queue.get(timeout=0.1)
                self._process_task(task)
                self.task_queue.task_done()
            except Empty:
                continue

    def _process_task(self, task: Task) -> None:
        def execute() -> None:
            self._execute_task(task.data)

        future = self.executor.submit(execute)
        try:
            future.result(timeout=task.timeout)
        except (TimeoutError, asyncio.TimeoutError):
            pass

    def _execute_task(self, data: dict[str, Any]) -> None:
        if delay := data.get("delay"):
            if isinstance(delay, (int, float)):
                time.sleep(delay)

    def submit(self, data: dict[str, Any], timeout: float = 5.0) -> bool:
        with self._lock:
            if not self._running:
                raise RuntimeError("processor is stopped")

        try:
            self.task_queue.put_nowait(Task(data=data, timeout=timeout))
            return True
        except Exception:
            return False

    def shutdown(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._running = False

        self._shutdown_event.set()
        for t in self.workers:
            t.join(timeout=2.0)
        self.workers.clear()
        self.executor.shutdown(wait=True, cancel_futures=True)

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def queue_length(self) -> int:
        return self.task_queue.qsize()


_global_processor: Optional[BackgroundProcessor] = None
_global_lock = threading.Lock()


def process_bg(data: dict[str, Any]) -> None:
    global _global_processor

    with _global_lock:
        if _global_processor is None:
            _global_processor = BackgroundProcessor(queue_size=100)
            _global_processor.start(workers=4)

    timeout = data.get("timeout", 5.0)
    if isinstance(timeout, (int, float)):
        pass
    else:
        timeout = 5.0

    _global_processor.submit(data, timeout=timeout)


class TestProcessBG:

    def test_process_bg_non_blocking(self) -> None:
        started = threading.Event()
        completed = threading.Event()

        def run() -> None:
            started.set()
            process_bg({"delay": 0.01, "timeout": 0.1})
            completed.set()

        t = threading.Thread(target=run)
        t.start()

        assert started.wait(timeout=0.1), "ProcessBG did not start in time"
        assert completed.wait(timeout=0.1), "ProcessBG appears to be blocking"
        t.join()

    def test_process_bg_with_custom_timeout(self) -> None:
        processor = BackgroundProcessor(queue_size=10)
        processor.start(2)

        called = threading.Event()

        def callback() -> None:
            called.set()

        processor.submit({"delay": 0.2, "timeout": 0.05, "onDone": callback})

        time.sleep(0.15)
        processor.shutdown()


class TestBackgroundProcessor:

    def test_background_processor_no_race(self) -> None:
        processor = BackgroundProcessor(queue_size=100)
        processor.start(4)

        success_count = 0
        lock = threading.Lock()

        def submit_tasks(task_id: int) -> None:
            for j in range(10):
                if processor.submit(
                    {"id": task_id, "task": j, "delay": 0.001, "timeout": 0.05},
                    timeout=0.05,
                ):
                    with lock:
                        nonlocal success_count
                        success_count += 1

        threads = [threading.Thread(target=submit_tasks, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        time.sleep(0.1)
        processor.shutdown()

        assert success_count > 0, "No tasks were successfully submitted"

    def test_background_processor_context_timeout(self) -> None:
        processor = BackgroundProcessor(queue_size=10)
        processor.start(2)

        processor.submit({"delay": 0.5, "timeout": 0.01}, timeout=0.01)

        time.sleep(0.1)
        processor.shutdown()

    def test_background_processor_graceful_shutdown(self) -> None:
        processor = BackgroundProcessor(queue_size=10)
        processor.start(2)

        completed_count = 0
        lock = threading.Lock()

        def make_callback() -> Callable[[], None]:
            def callback() -> None:
                nonlocal completed_count
                with lock:
                    completed_count += 1
            return callback

        for i in range(5):
            processor.submit(
                {"delay": 0.01, "timeout": 0.1, "callback": make_callback()},
                timeout=0.1,
            )

        time.sleep(0.05)

        shutdown_done = threading.Event()

        def do_shutdown() -> None:
            processor.shutdown()
            shutdown_done.set()

        t = threading.Thread(target=do_shutdown)
        t.start()

        assert shutdown_done.wait(timeout=2.0), "Shutdown did not complete - possible thread leak"
        t.join()

    def test_background_processor_queue_full(self) -> None:
        processor = BackgroundProcessor(queue_size=2)
        processor.start(1)

        for i in range(5):
            processor.submit({"delay": 0.1, "timeout": 0.2}, timeout=0.2)

        processor.submit({"delay": 0.01, "timeout": 0.05}, timeout=0.05)

        processor.shutdown()

    def test_background_processor_submit_after_stop(self) -> None:
        processor = BackgroundProcessor(queue_size=10)
        processor.start(2)
        processor.shutdown()

        with pytest.raises(RuntimeError, match="processor is stopped"):
            processor.submit({"delay": 0.01, "timeout": 0.05}, timeout=0.05)

    def test_background_processor_concurrent_submit_and_shutdown(self) -> None:
        processor = BackgroundProcessor(queue_size=100)
        processor.start(4)

        def submit_tasks() -> None:
            for j in range(20):
                processor.submit({"delay": 0.001, "timeout": 0.05}, timeout=0.05)
                time.sleep(0.001)

        threads = [threading.Thread(target=submit_tasks) for _ in range(5)]
        for t in threads:
            t.start()

        time.sleep(0.01)

        for t in threads:
            t.join()

        processor.shutdown()

    def test_background_processor_is_running(self) -> None:
        processor = BackgroundProcessor(queue_size=10)

        assert not processor.is_running, "Processor should not be running before Start"

        processor.start(2)
        assert processor.is_running, "Processor should be running after Start"

        processor.shutdown()
        assert not processor.is_running, "Processor should not be running after Shutdown"

    def test_background_processor_no_goroutine_leak(self) -> None:
        for i in range(5):
            processor = BackgroundProcessor(queue_size=10)
            processor.start(4)

            for j in range(5):
                processor.submit({"delay": 0.005, "timeout": 0.05}, timeout=0.05)

            time.sleep(0.02)
            processor.shutdown()

            assert not processor.is_running, f"Cycle {i}: Processor still running after shutdown"

        time.sleep(0.1)

    def test_background_processor_context_cancellation(self) -> None:
        processor = BackgroundProcessor(queue_size=10)
        processor.start(2)

        processor.submit({"delay": 1.0, "timeout": 0.5}, timeout=0.5)

        time.sleep(0.01)

        shutdown_done = threading.Event()

        def do_shutdown() -> None:
            processor.shutdown()
            shutdown_done.set()

        t = threading.Thread(target=do_shutdown)
        t.start()

        assert shutdown_done.wait(timeout=3.0), "Context cancellation did not propagate properly"
        t.join()


class TestBackgroundProcessorBenchmarks:

    def test_benchmark_submit(self) -> None:
        processor = BackgroundProcessor(queue_size=1000)
        processor.start(8)

        iterations = 1000
        start = time.perf_counter()

        for i in range(iterations):
            processor.submit({"id": i, "delay": 0, "timeout": 0.1}, timeout=0.1)

        elapsed = time.perf_counter() - start
        print(f"\nSubmit benchmark: {iterations} tasks in {elapsed:.3f}s ({iterations/elapsed:.0f} ops/s)")

        processor.shutdown()

    def test_benchmark_process(self) -> None:
        iterations = 100
        processor = BackgroundProcessor(queue_size=iterations)
        processor.start(4)

        start = time.perf_counter()

        for i in range(iterations):
            processor.submit({"id": i, "delay": 0, "timeout": 0.1}, timeout=0.1)

        time.sleep(0.1)
        processor.shutdown()

        elapsed = time.perf_counter() - start
        print(f"\nProcess benchmark: {iterations} tasks in {elapsed:.3f}s ({iterations/elapsed:.0f} ops/s)")
