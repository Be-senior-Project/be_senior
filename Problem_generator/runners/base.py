"""
검증기(runner) 공통 모듈.

- VerifyResult: 검증 결과 표준 포맷
- extract_param_names: Signature 문자열에서 파라미터 이름만 추출
"""

import re
from typing import TypedDict, Optional, Literal


VerifyReason = Literal[
    "compile_error",
    "runtime_error",
    "timeout",
    "output_mismatch",
    "internal_error",  # 우리 쪽 파싱/조립 실패 등
]


class VerifyResult(TypedDict):
    ok: bool
    reason: Optional[VerifyReason]
    detail: Optional[str]


def ok_result() -> VerifyResult:
    return {"ok": True, "reason": None, "detail": None}


def fail_result(reason: VerifyReason, detail: str) -> VerifyResult:
    return {"ok": False, "reason": reason, "detail": detail}


# Signature 예:
#   "def solution(n, arr):"
#   "public int solution(int n, int[] arr)"
#   "int solution(int n, vector<int>& arr)"
#
# 우리는 호출용 변수명 순서만 필요하므로 괄호 안의 마지막 단어들만 뽑는다.
_PAREN_RE = re.compile(r"\(([^)]*)\)")
_LAST_WORD_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*$")


def extract_param_names(signature: str) -> list[str]:
    """
    Signature 문자열에서 파라미터 이름만 순서대로 추출한다.
    파라미터가 없으면 빈 리스트를 반환한다.
    파싱 실패 시 ValueError를 던진다.
    """
    m = _PAREN_RE.search(signature)
    if not m:
        raise ValueError(f"Signature에서 괄호를 찾지 못했습니다: {signature!r}")

    inner = m.group(1).strip()
    if not inner:
        return []

    # 단순 쉼표 분리. 제네릭(Java <K,V>, C++ <int, char>)이 들어오면 깨질 수 있으나
    # 코딩테스트 문제 시그니처 수준에서는 일반적이지 않아 일단 이대로.
    names: list[str] = []
    for part in inner.split(","):
        part = part.strip().rstrip(",").strip()
        if not part:
            continue
        m2 = _LAST_WORD_RE.search(part)
        if not m2:
            raise ValueError(f"Signature 파라미터 파싱 실패: {part!r}")
        names.append(m2.group(1))
    return names
