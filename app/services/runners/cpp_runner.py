"""
C++ 검증기.

조립 형태:
    #include <bits/stdc++.h>
    using namespace std;

    {answer_code}   // solution 함수 정의

    int main() {
        {io_input}
        cout << solution({param1}, {param2}, ...) << endl;
        return 0;
    }

가정:
- answer_code 는 함수 한 덩어리 (예: "int solution(int n, vector<int>& arr) { ... }")
- IO 입력은 변수 선언문이며 main 안에 그대로 삽입된다.
- 출력은 endl 한 번 (Python/Java print 와 동일하게 끝에 줄바꿈).

주의:
- 반환 타입이 vector<...> 등인 경우 단순 cout 으로는 못 찍는다.
  현 프롬프트 기준 코딩테스트 수준에서는 int/long/string/bool/double 정도가 일반적이라
  일단 단순 cout 으로 진행. 추후 필요 시 출력 헬퍼를 두면 됨.
"""

import subprocess
import tempfile
from pathlib import Path

from .base import VerifyResult, ok_result, fail_result, extract_param_names

COMPILE_TIMEOUT = 5
EXEC_TIMEOUT = 5

_TEMPLATE = """\
#include <bits/stdc++.h>
using namespace std;

{answer_code}

int main() {{
    {io_input}
    cout << solution({call_args}) << endl;
    return 0;
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
        answer_code=answer_code,
        io_input=_indent(io_input, 4).lstrip(),
        call_args=call_args,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "solution.cpp"
        bin_path = tmp / "solution"
        src.write_text(program, encoding="utf-8")

        # 컴파일
        try:
            compile_proc = subprocess.run(
                ["g++", "-std=c++17", "-O2", "-o", str(bin_path), str(src)],
                capture_output=True,
                text=True,
                timeout=COMPILE_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return fail_result("compile_error", f"컴파일 시간 {COMPILE_TIMEOUT}초 초과")

        if compile_proc.returncode != 0:
            return fail_result("compile_error", compile_proc.stderr.strip() or "g++ failed")

        # 실행
        try:
            run_proc = subprocess.run(
                [str(bin_path)],
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
