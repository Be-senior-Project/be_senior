"""
Java 검증기.

조립 형태:
    import java.util.*;

    public class Main {
        {answer_code}   // public/static 등의 수식어가 붙은 solution 메서드

        public static void main(String[] args) {
            {io_input}
            System.out.println(new Main().solution({param1}, {param2}, ...));
        }
    }

가정:
- answer_code 는 메서드 정의 한 덩어리 (예: "public int solution(int n, int[] arr) { ... }")
- 우리는 그 메서드를 인스턴스 메서드로 보고 new Main().solution(...) 으로 호출한다.
- IO 입력은 변수 선언문이며 main 안에 그대로 삽입된다.
"""

import subprocess
import tempfile
from pathlib import Path

from .base import VerifyResult, ok_result, fail_result, extract_param_names

COMPILE_TIMEOUT = 5
EXEC_TIMEOUT = 5

_TEMPLATE = """\
import java.util.*;

public class Main {{
    {answer_code}

    public static void main(String[] args) {{
        {io_input}
        System.out.println(new Main().solution({call_args}));
    }}
}}
"""


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.splitlines())


def run(answer_code: str, io_input: str, expected_output: str, signature: str) -> VerifyResult:
    try:
        params = extract_param_names(signature)
    except ValueError as e:
        return fail_result("internal_error", f"Signature 파싱 실패: {e}")

    call_args = ", ".join(params)

    program = _TEMPLATE.format(
        answer_code=_indent(answer_code, 4).lstrip(),
        io_input=_indent(io_input, 8).lstrip(),
        call_args=call_args,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "Main.java"
        src.write_text(program, encoding="utf-8")

        # 컴파일
        try:
            compile_proc = subprocess.run(
                ["javac", str(src)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=COMPILE_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return fail_result("compile_error", f"컴파일 시간 {COMPILE_TIMEOUT}초 초과")

        if compile_proc.returncode != 0:
            return fail_result("compile_error", compile_proc.stderr.strip() or "javac failed")

        # 실행
        try:
            run_proc = subprocess.run(
                ["java", "-cp", str(tmp), "Main"],
                capture_output=True,
                text=True,
                timeout=EXEC_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return fail_result("timeout", f"실행 시간 {EXEC_TIMEOUT}초 초과")

        if run_proc.returncode != 0:
            return fail_result("runtime_error", run_proc.stderr.strip() or "non-zero exit code")

        actual = run_proc.stdout.strip()
        expected = expected_output.strip()
        if actual != expected:
            return fail_result(
                "output_mismatch",
                f"expected: {expected!r}, actual: {actual!r}",
            )

    return ok_result()
