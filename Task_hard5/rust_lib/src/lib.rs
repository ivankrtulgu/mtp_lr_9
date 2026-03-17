use pyo3::prelude::*;

/// Check if a number is prime using trial division up to sqrt(n)
fn is_prime(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    if n == 2 {
        return true;
    }
    if n % 2 == 0 {
        return false;
    }
    
    let limit = (n as f64).sqrt() as u64;
    for i in (3..=limit).step_by(2) {
        if n % i == 0 {
            return false;
        }
    }
    true
}

/// Count prime numbers in range [2, n] using trial division
/// 
/// # Arguments
/// * `n` - Upper bound of the range (inclusive)
/// 
/// # Returns
/// Count of prime numbers in the range
#[pyfunction]
fn count_primes(n: u64) -> PyResult<u64> {
    let mut count: u64 = 0;
    for num in 2..=n {
        if is_prime(num) {
            count += 1;
        }
    }
    Ok(count)
}

/// Python module for high-performance prime counting
#[pymodule]
fn rust_lib(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(count_primes, m)?)?;
    Ok(())
}
