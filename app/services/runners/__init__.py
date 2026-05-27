"""
언어 문자열 → runner.run 함수 매핑.

main 쪽에서 사용하는 Language enum 값("Python", "Java", "C++")을 그대로 키로 받는다.
"""

from . import python_runner, java_runner, cpp_runner
from .base import VerifyResult  # re-export


RUNNERS = {
    "Python": python_runner.run,
    "Java": java_runner.run,
    "C++": cpp_runner.run,
}


__all__ = ["RUNNERS", "VerifyResult"]