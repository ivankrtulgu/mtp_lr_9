use pyo3::prelude::*;

/// Check if a number is prime
fn is_prime_impl(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    if n == 2 {
        return true;
    }
    if n % 2 == 0 {
        return false;
    }
    let mut i = 3;
    while i * i <= n {
        if n % i == 0 {
            return false;
        }
        i += 2;
    }
    true
}

/// Check if a number is prime.
/// Returns True if the number is prime, False otherwise.
#[pyfunction]
fn is_prime(n: u64) -> bool {
    is_prime_impl(n)
}

/// A Python module implemented in Rust.
#[pymodule]
fn task_hard3(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(is_prime, m)?)?;
    Ok(())
}