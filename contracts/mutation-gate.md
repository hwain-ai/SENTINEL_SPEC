---
type: Executable Contract
status: draft
generated: { by: "process:codex", at: "2026-09-03T09:45:52Z" }
owner: "human:hwain"
sources:
  - resource: ../golden/gate/mutation-v1.json
    title: Mutation killed-only gate golden vector
---

# Mutation killed-only gate 계약

한마디로, 검사 범위에 mutant가 하나 이상 있고 모든 mutant가 테스트에 의해 killed된 경우만 통과합니다.

Mutant는 mutation 도구가 결함을 흉내 내기 위해 원본 코드를 한 군데 바꾼 실행 후보입니다. killed는 기존 테스트가 그 변경을 감지해 실패했다는 뜻입니다.

## 허용 상태

상태 이름은 다음 9개만 허용합니다.

|상태|뜻|
|---|---|
|killed|테스트가 mutant를 감지함|
|survived|테스트가 mutant를 감지하지 못함|
|uncovered|mutant 위치를 테스트가 실행하지 않음|
|timedOut|제한 시간 안에 결과가 나오지 않음|
|compileError|mutant 실행 전 compile에 실패함|
|runtimeError|테스트 판정과 구분되는 실행 오류가 발생함|
|pending|판정이 끝나지 않음|
|ignored|검사에서 제외됨|
|toolError|mutation 도구 자체가 실패함|

각 상태는 정확히 한 번 있어야 합니다. JSON을 읽는 구현은 같은 이름이 두 번 있는 object도 mapping으로 바꾸기 전에 거부해야 합니다. 빠진 상태나 알 수 없는 상태가 있으면 validation error입니다.

## 판정 순서

1. 9개 상태 count, inScope, unauthorizedExclusion이 bool이 아닌 0 이상 9,007,199,254,740,991 이하의 정수인지 확인합니다. 이 범위는 JSON을 사용하는 세 언어가 같은 정수를 손실 없이 읽기 위한 공통 한계입니다.
2. 9개 상태 count의 합이 inScope와 정확히 같은지 확인합니다.
3. inScope가 0이면 통과시키지 않고 kill rate도 만들지 않습니다.
4. inScope가 1 이상이고 unauthorizedExclusion이 0이며 `killed × 100 × minimum.denominator ≥ minimum.numerator × inScope`일 때만 통과합니다. minimum은 검사 요청이 넘기는 최소 kill 비율(퍼센트)이며 기본값은 100입니다.
5. inScope가 1 이상이면 kill rate를 `killed / inScope` 기약분수로 계산합니다.

기본값 100에서는 killed가 inScope와 같아야 하므로 나머지 8개 상태는 모두 0이어야 합니다. 따라서 timeout-only, ignored-only, survived가 하나라도 있는 결과와 승인받지 않은 제외가 있는 결과는 모두 실패합니다. zero-mutant 결과를 100%로 꾸미지 않습니다.

## 최소 kill 비율 형식

최소 kill 비율은 CRAP 상한과 같은 문자열 형식입니다. 정수 또는 소수점 아래 최대 두 자리의 십진 문자열이며 정규식 `^(0|[1-9][0-9]*)(\.[0-9]{1,2})?$`에 맞아야 하고, 형식 위반은 `mutationMinInvalid`, 100 초과는 `mutationMinOutOfRange`입니다. 문자열은 정확한 분수로 읽습니다. 비율을 100보다 낮추면 killed 외의 상태가 비율만큼 남아도 통과하지만, inScope 0과 승인받지 않은 제외는 어떤 비율에서도 실패합니다. timedOut·toolError 같은 상태도 kill 비율을 낮추는 방향으로만 계산하며 별도로 면제하지 않습니다.

언어별 동일성 검증 자료는 [threshold-v1.json](../golden/gate/threshold-v1.json)입니다.

언어별 동일성 검증 자료는 [mutation-v1.json](../golden/gate/mutation-v1.json)입니다. 이 자료는 `2^53-1` all-killed와 one-survived 정상 입력, 각 count field의 `2^53`과 `2^53+1` 오류를 따로 고정합니다.

Golden의 unsafe 입력은 `rawJsonInvalidCases[].rawInput`에 JSON 원문 string으로 보존합니다. 각
runtime은 이 원문을 UTF-8 byte로 만든 뒤 duplicate key, fraction·exponent·negative-zero number
token과 safe-integer 초과를 native JSON number 변환 전에 검사합니다. Unsafe token은
`jsonIntegerOutOfRange`로 중단하며 일반 JavaScript `JSON.parse`를 먼저 호출하지 않습니다. 이
순서를 지켜야 `2^53`과 `2^53+1`이 서로 다른 반례로 남습니다.
