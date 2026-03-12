use pyo3::prelude::*;

fn fibonacci_impl(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }

    let mut a: u64 = 0;
    let mut b: u64 = 1;

    for _ in 2..=n {
        let temp = a + b;
        a = b;
        b = temp;
    }

    b
}

#[no_mangle]
pub extern "C" fn fibonacci(n: u64) -> u64 {
    fibonacci_impl(n)
}

#[pymodule]
fn rust_benchmark(_py: Python, m: &PyModule) -> PyResult<()> {
    #[pyfn(m)]
    #[pyo3(name = "fibonacci")]
    fn fibonacci_py(n: u64) -> u64 {
        fibonacci_impl(n)
    }
    Ok(())
}
