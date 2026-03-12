import ctypes
import sys
from pathlib import Path


def get_rust_lib_path() -> Path:
    lib_dir = Path(__file__).parent / "rust_lib" / "target" / "release"

    if sys.platform == "win32":
        lib_path = lib_dir / "rust_benchmark.dll"
    elif sys.platform == "darwin":
        lib_path = lib_dir / "librust_benchmark.dylib"
    else:
        lib_path = lib_dir / "librust_benchmark.so"

    return lib_path


class RustLib:

    def __init__(self):
        self.lib_path = get_rust_lib_path()
        self._lib = None
        self._load_library()

    def _load_library(self):
        if not self.lib_path.exists():
            raise FileNotFoundError(
                f"Rust library not found at {self.lib_path}. "
                "Please build it first with: cargo build --release"
            )

        self._lib = ctypes.CDLL(str(self.lib_path))

        self._lib.fibonacci.argtypes = [ctypes.c_uint64]
        self._lib.fibonacci.restype = ctypes.c_uint64

    def fibonacci(self, n: int) -> int:
        if n < 0:
            raise ValueError("n must be non-negative")
        return self._lib.fibonacci(ctypes.c_uint64(n))


_rust_lib = None


def get_rust_lib() -> RustLib:
    global _rust_lib
    if _rust_lib is None:
        _rust_lib = RustLib()
    return _rust_lib


def fibonacci_rust(n: int) -> int:
    return get_rust_lib().fibonacci(n)
