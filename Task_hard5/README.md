# Performance Benchmark: Prime Counting

Сравнение производительности трех подходов для подсчета простых чисел:
1. **Pure Python** — нативный Python с циклами
2. **Python + Rust (PyO3)** — Rust библиотека через PyO3
3. **Python + Go (HTTP)** — Go микросервис через HTTP запросы

## Задача

Подсчитать количество простых чисел в диапазоне от 2 до N (по умолчанию 1,000,000) используя алгоритм перебора с проверкой делителей до √N.

**Входные данные:** Одно число — верхняя граница диапазона (N).

## Project Structure

```
Task_hard5/
├── benchmark.py          # Main benchmark script
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── rust_lib/
│   ├── Cargo.toml        # Rust project configuration
│   └── src/
│       └── lib.rs        # Rust implementation (count_primes)
└── go_service/
    ├── go.mod            # Go module file
    └── main.go           # Go HTTP service implementation
```

## Prerequisites

- **Python 3.11+**
- **Rust** (для PyO3 модуля)
- **Go 1.21+** (для HTTP сервиса)
- **maturin** (для сборки Rust-Python модуля)

## Installation & Build

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Build Rust module

```bash
cd rust_lib

# Install maturin if not already installed
pip install maturin

# Build and install the Rust module in development mode
maturin develop
```

### 3. Build Go service

```bash
cd go_service
go build -o go_service main.go
```

На Windows исполняемый файл будет `go_service.exe`.

## Running the Benchmark

### Step 1: Start Go service (in a separate terminal)

```bash
cd go_service
./go_service
# or on Windows:
go_service.exe
```

Сервер запустится на порту 8080. Эндпоинт: `GET /count?n=1000000`

### Step 2: Run benchmark (in another terminal)

```bash
python benchmark.py
```

Скрипт:
1. Замеряет время выполнения каждого метода (5 итераций)
2. Проверяет идентичность результатов всех трех методов
3. Выводит итоговую таблицу со Speedup относительно Python

## Expected Output

```
======================================================================
BENCHMARK: Prime Counting (trial division up to sqrt(N))
======================================================================

Range: [2, 1,000,000]
Iterations per method: 5

Expected result (π(1,000,000)): 78,498 primes

----------------------------------------------------------------------
1. Pure Python
----------------------------------------------------------------------
  Iteration 1/5: 45678.90 ms
  Iteration 2/5: 45234.56 ms
  Iteration 3/5: 45890.12 ms
  Iteration 4/5: 45123.45 ms
  Iteration 5/5: 45567.89 ms
Average time: 45499.18 ms
Result: 78,498 primes
✓ Result verified

----------------------------------------------------------------------
2. Python + Rust (PyO3)
----------------------------------------------------------------------
  Iteration 1/5: 1234.56 ms
  Iteration 2/5: 1245.67 ms
  Iteration 3/5: 1223.45 ms
  Iteration 4/5: 1256.78 ms
  Iteration 5/5: 1234.56 ms
Average time: 1239.00 ms
Result: 78,498 primes
✓ Result verified

----------------------------------------------------------------------
3. Python + Go (HTTP Service)
----------------------------------------------------------------------
Go service detected on port 8080
  Iteration 1/5: 2345.67 ms
  Iteration 2/5: 2456.78 ms
  Iteration 3/5: 2234.56 ms
  Iteration 4/5: 2567.89 ms
  Iteration 5/5: 2345.67 ms
Average time: 2390.11 ms
Result: 78,498 primes
✓ Result verified

======================================================================
SUMMARY
======================================================================

Approach                  Time (ms)       Speedup         Status
----------------------------------------------------------------------
Pure Python               45499.18        1.00x           ✓
Rust (PyO3)               1239.00         36.72x          ✓
Go (HTTP)                 2390.11         19.04x          ✓

======================================================================
Benchmark completed!
======================================================================
```

## API Reference

### Go HTTP Service

- **Health check:** `GET http://localhost:8080/health`
- **Count primes:** `GET http://localhost:8080/count?n=1000000`

Response format:
```json
{"count": 78498}
```

### Rust Module

```python
import rust_lib
result = rust_lib.count_primes(1000000)
```

## Notes

- **Rust (PyO3)** обычно самый быстрый благодаря отсутствию накладных расходов FFI
- **Go (HTTP)** включает сетевые накладные расходы, но всё равно быстрее Python
- **Pure Python** самый медленный, но не требует дополнительных зависимостей
- Все три метода дают идентичные результаты (проверяется через assert)
- Go сервис запускается вручную в отдельном терминале

## Troubleshooting

### Rust module not found
```bash
cd rust_lib
maturin develop --release
```

### Go service fails to start
- Убедитесь, что порт 8080 не занят
- Проверьте установку Go: `go version`

### Go service not detected
- Запустите Go сервис перед запуском benchmark.py:
  ```bash
  cd go_service
  go run main.go
  ```
