"""
검증기 진입점.

흐름:
    1. JSON에서 필요한 필드 추출 (Type, Signature, IO Example, Code Skeleton, Answer)
    2. Type별로 "완성 코드(answer_code)" 만들기
        - Implementation: Answer 그대로
        - Debugging:      Answer 그대로 (이미 수정된 완성 코드)
        - Fill-in-the-blank: Code Skeleton의 {{BLANK_N}} 자리를 Answer 리스트로 치환
    3. 언어에 맞는 runner 호출
    4. {ok, reason, detail} 반환
"""

import re
from typing import Optional

from runners import RUNNERS, VerifyResult
from runners.base import fail_result


_BLANK_RE = re.compile(r"\{\{BLANK_(\d+)\}\}")


def _compose_answer_code(problem_type: str, code_skeleton: Optional[str], answer) -> tuple[Optional[str], Optional[str]]:
    """
    (answer_code, error_message) 를 반환한다.
    실패 시 answer_code = None, error_message에 사유를 담는다.
    """
    if problem_type in ("Implementation", "Debugging"):
        if not isinstance(answer, str):
            return None, f"{problem_type} Type의 Answer는 문자열이어야 합니다. 받은 타입: {type(answer).__name__}"
        return answer, None

    if problem_type == "Fill-in-the-blank":
        if not isinstance(answer, list) or not all(isinstance(a, str) for a in answer):
            return None, "Fill-in-the-blank Type의 Answer는 문자열 리스트여야 합니다."
        if not isinstance(code_skeleton, str) or not code_skeleton:
            return None, "Fill-in-the-blank Type은 Code Skeleton이 필요합니다."

        placeholders = _BLANK_RE.findall(code_skeleton)
        if len(placeholders) != len(answer):
            return None, (
                f"빈칸 개수 불일치: Code Skeleton에 {{BLANK_N}} {len(placeholders)}개, "
                f"Answer 리스트 {len(answer)}개"
            )

        composed = code_skeleton
        for idx, replacement in enumerate(answer, start=1):
            composed = composed.replace(f"{{{{BLANK_{idx}}}}}", replacement)
        return composed, None

    return None, f"알 수 없는 Type: {problem_type!r}"


def verify_problem(problem: dict, language: str) -> VerifyResult:
    """
    problem: generate_problem()이 반환한 JSON dict
    language: "Python" | "Java" | "C++"  (enums.Language.value 와 일치)
    """
    runner = RUNNERS.get(language)
    if runner is None:
        return fail_result("internal_error", f"지원하지 않는 언어: {language!r}")

    try:
        prob = problem["Problem"]
        problem_type = prob["Type"]
        signature = prob["Signature"]
        io_example = prob["IO Example"]
        io_input = io_example["input"]
        expected_output = io_example["output"]
        code_skeleton = prob.get("Code Skeleton")
        answer = prob["Answer"]
    except KeyError as e:
        return fail_result("internal_error", f"JSON 구조 누락: {e}")

    answer_code, err = _compose_answer_code(problem_type, code_skeleton, answer)
    if answer_code is None:
        return fail_result("internal_error", err or "answer_code 조립 실패")

    return runner(
        answer_code=answer_code,
        io_input=io_input,
        expected_output=expected_output,
        signature=signature,
    )