import json
import subprocess
from typing import Any


def call_go(data: dict[str, Any], go_executable: str = "./main.exe") -> dict[str, Any]:
    """
    Send JSON data to Go program via stdin and read result from stdout.

    Args:
        data: Dictionary to send as JSON to the Go program.
        go_executable: Path to the compiled Go executable.

    Returns:
        Dictionary parsed from Go program's JSON output.
    """
    process = subprocess.Popen(
        [go_executable],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    json_input = json.dumps(data)
    stdout_bytes, stderr_bytes = process.communicate(input=json_input.encode("utf-8"))

    if process.returncode != 0:
        raise RuntimeError(f"Go program failed: {stderr_bytes.decode('utf-8')}")

    return json.loads(stdout_bytes.decode("utf-8"))


if __name__ == "__main__":
    result = call_go({"val": 10})
    print(f"Result: {result}")
