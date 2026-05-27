다음 조건에 맞는 코딩 테스트 문제를 생성해 주세요:

Category: {category}
Subcategory: {subcategory}
Difficulty Level: {difficulty}
Language: {language}
Style: {style}

## 참고 예시 (Reference Examples)

아래는 시드 DB에서 벡터 유사도 검색으로 가져온 기존 문제들입니다. 요청된 문제와 동일한 Category / Subcategory / Language를 공유합니다.

{examples}

위 예시는 다음을 **참고**하는 용도로만 사용하세요:
- 해당 난이도에서 일반적인 `Constraints` 규모
- `Description`의 톤과 분량
- 요청 언어에서의 `Signature`와 `IO Example` 구성 방식

예시를 그대로 베끼지 마세요. **같은 주제 안에서 다른 각도/시나리오/변형**을 가진 **새로운 문제**를 생성하세요. 예시와 동일한 Title, 시나리오, 풀이 접근법은 피하세요.

---

Subcategory가 "None"이 아닌 경우, 해당 Category 안에서 주어진 Subcategory에 특화된 문제를 출제하세요.

시스템 프롬프트에 정의된 엄격한 JSON 형식에 따라 문제 **1개**를 생성하세요. 특히 다음을 반드시 지키세요:
- `Signature`는 요청된 LANGUAGE 문법으로 작성되어야 하며, 함수명은 `solution`이어야 합니다.
- `IO Example.input`은 요청된 LANGUAGE의 변수 선언 문법을 사용해야 하며, 변수명은 `Signature`의 파라미터명과 **이름·순서가 정확히 일치**해야 합니다.
- `solution()`은 **어떤 출력도 수행하지 말고**, 반드시 단일 값을 return만 해야 합니다.
- `Code Skeleton`과 `Answer`는 시스템 프롬프트의 Type별 규칙을 따라야 합니다.

JSON만 출력하세요. JSON 외부에 어떠한 설명, 안내문, 마크다운 코드 펜스도 포함하지 마세요.
