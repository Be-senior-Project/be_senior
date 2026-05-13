"""
Python 검증기.

조립 형태:
    {answer_code}

    {io_input}
    print(solution({param1}, {param2}, ...))
"""

import subprocess
import tempfile
from pathlib import Path

from .base import VerifyResult, ok_result, fail_result, extract_param_names

EXEC_TIMEOUT = 5  # seconds


def run(answer_code: str, io_input: str, expected_output: str, signature: str) -> VerifyResult:
    try:
        params = extract_param_names(signature)
    except ValueError as e:
        return fail_result("internal_error", f"Signature 파싱 실패: {e}")

    call_args = ", ".join(params)
    program = f"{answer_code}\n\n{io_input}\nprint(solution({call_args}))\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        script = Path(tmpdir) / "solution.py"
        script.write_text(program, encoding="utf-8")

        try:
            result = subprocess.run(
                ["python3", str(script)],
                capture_output=True,
                text=True,
                timeout=EXEC_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return fail_result("timeout", f"실행 시간 {EXEC_TIMEOUT}초 초과")

        if result.returncode != 0:
            return fail_result("runtime_error", result.stderr.strip() or "non-zero exit code")

        actual = result.stdout.strip()
        expected = expected_output.strip()
        if actual != expected:
            return fail_result(
                "output_mismatch",
                f"expected: {expected!r}, actual: {actual!r}",
            )

    return ok_result()
