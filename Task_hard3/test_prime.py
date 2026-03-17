import task_hard3


def test_is_prime_13():
    """Test that 13 is prime"""
    assert task_hard3.is_prime(13) is True


def test_is_prime_15():
    """Test that 15 is not prime"""
    assert task_hard3.is_prime(15) is False


if __name__ == "__main__":
    test_is_prime_13()
    test_is_prime_15()
    print("All tests passed!")
