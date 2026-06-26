from unittest.mock import MagicMock, patch
from grader.sandbox import run_in_sandbox


def test_run_returns_stdout():
    mock_container = MagicMock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [b"hello\n", b""]

    with patch("grader.sandbox._client") as mock_client:
        mock_client.containers.run.return_value = mock_container
        result = run_in_sandbox(
            image="pautograder-python-sandbox",
            command=["python", "-c", "print('hello')"],
            files={"solution.py": b"print('hello')"},
            timeout=5,
        )

    assert result["stdout"] == "hello\n"
    assert result["exit_code"] == 0
    assert result["timed_out"] is False


def test_run_timeout():
    mock_container = MagicMock()
    mock_container.wait.side_effect = Exception("timeout")

    with patch("grader.sandbox._client") as mock_client:
        mock_client.containers.run.return_value = mock_container
        result = run_in_sandbox(
            image="pautograder-python-sandbox",
            command=["python", "infinite.py"],
            files={"infinite.py": b"while True: pass"},
            timeout=1,
        )

    assert result["timed_out"] is True
    assert result["exit_code"] == -1
