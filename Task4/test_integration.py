import pytest
import bridge


@pytest.fixture(scope="module")
def go_executable() -> str:
    return "./main.exe"


def test_double_value(go_executable: str) -> None:
    """Test that Go program doubles the input value."""
    input_data = {"val": 10}
    expected = {"result": 20}

    result = bridge.call_go(input_data, go_executable)

    assert result == expected


def test_zero_value(go_executable: str) -> None:
    """Test with zero input."""
    input_data = {"val": 0}
    expected = {"result": 0}

    result = bridge.call_go(input_data, go_executable)

    assert result == expected


def test_negative_value(go_executable: str) -> None:
    """Test with negative input."""
    input_data = {"val": -5}
    expected = {"result": -10}

    result = bridge.call_go(input_data, go_executable)

    assert result == expected


def test_large_value(go_executable: str) -> None:
    """Test with a large input value."""
    input_data = {"val": 1000000}
    expected = {"result": 2000000}

    result = bridge.call_go(input_data, go_executable)

    assert result == expected
