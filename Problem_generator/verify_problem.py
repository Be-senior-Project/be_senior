import subprocess
import ast
import json


def _parse_input(input_val: str) -> tuple[list, dict]:
    """
    GPT가 생성한 input 문자열을 args, kwargs로 파싱
    예) "arr = [1, 2, 3]"       → ([], {"arr": [1, 2, 3]})
        "[1, 2, 3]"             → ([1, 2, 3], {})  → args로 전달
        "5"                     → (5, {})           → args로 전달
        "arr = [1, 2], n = 3"  → ([], {"arr": [1, 2], "n": 3})
    """
    input_val = input_val.strip()
    kwargs = {}
    args = None

    # "key = value" 패턴이 있으면 kwargs로 파싱
    if "=" in input_val:
        try:
            for part in input_val.split(","):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    kwargs[k.strip()] = ast.literal_eval(v.strip())
                else:
                    # 혼합 케이스는 일단 통째로 파싱 시도
                    args = ast.literal_eval(input_val)
                    kwargs = {}
                    break
        except Exception:
            args = input_val  # 파싱 실패 시 raw string으로
    else:
        try:
            args = ast.literal_eval(input_val)
        except Exception:
            args = input_val

    return args, kwargs


def verify_problem(problem: dict) -> bool:
    try:
        prob = problem["Problem"]
        answer_code = prob["Answer"]
        io_example = prob["IO Example"]
        input_val = io_example["input"]
        expected_output = io_example["output"]
    except KeyError as e:
        print(f"JSON 구조 오류: {e}")
        return False

    args, kwargs = _parse_input(input_val)

    # solution() 호출 코드 생성
    if kwargs:
        kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
        call_str = f"solution({kwargs_str})"
    elif isinstance(args, (list, tuple)):
        call_str = f"solution({repr(args)})"
    else:
        call_str = f"solution({repr(args)})"

    run_code = f"""
{answer_code}

result = {call_str}
print(result)
"""

    try:
        result = subprocess.run(
            ["python", "-c", run_code],
            capture_output=True,
            text=True,
            timeout=5
        )
    except subprocess.TimeoutExpired:
        print("검증 실패: 실행 시간 초과 (무한루프 의심)")
        return False

    if result.returncode != 0:
        print(f"검증 실패: 코드 실행 오류\n{result.stderr}")
        return False

    actual_output = result.stdout.strip()

    if actual_output != expected_output.strip():
        print(f"검증 실패: 출력 불일치\n  예상: {expected_output}\n  실제: {actual_output}")
        return False

    return True