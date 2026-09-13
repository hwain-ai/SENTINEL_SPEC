---
type: Executable Contract
status: draft
generated: { by: "process:codex", at: "2026-09-03T09:45:52Z" }
owner: "human:hwain"
sources:
  - resource: ../golden/crap/formula-v1.json
    title: CRAP 수식과 표준 소수 golden vector
  - resource: ../golden/crap/stable-sort-v1.json
    title: CRAP 결과의 안정적인 정렬 golden vector
---

# CRAP 수치 계약

한마디로, 모든 SENTINEL 구현은 부동소수점 오차 없이 같은 CRAP 값과 같은 통과 여부를 만들어야 합니다.

## 입력

|이름|뜻|허용값|
|---|---|---|
|CC|Cyclomatic Complexity, 실행 경로의 복잡도|bool이 아닌 1 이상 9,007,199,254,740,991 이하의 정수|
|C|covered unit, 테스트가 실행한 측정 단위 수|bool이 아닌 0 이상 9,007,199,254,740,991 이하의 정수|
|T|total unit, 전체 측정 단위 수|bool이 아닌 1 이상 9,007,199,254,740,991 이하의 정수이며 C 이상|

입력 하나라도 범위를 벗어나면 계산을 계속하지 않고 validation error를 반환합니다. 이 상한은 JSON을 사용하는 다섯 언어가 같은 정수를 손실 없이 읽기 위한 공통 한계입니다.

## 계산 순서

1. denominator를 T의 세제곱으로 계산합니다.
2. numerator를 CC의 제곱 곱하기 `(T-C)`의 세제곱에 CC 곱하기 denominator를 더해 계산합니다.
3. numerator와 denominator의 최대공약수로 나눠 기약분수를 만듭니다.
4. 원래 numerator가 `limit × denominator` 이하일 때만 통과합니다. limit는 검사 요청이 넘기는 CRAP 상한이며 기본값은 8입니다. 표시용 소수는 판정에 사용하지 않습니다.

예를 들어 CC가 4이고 C가 3, T가 4이면 계산 전 분수는 272/64이고 기약분수는 17/4입니다. 표준 소수는 4.25이며 기본 상한 8 이하이므로 통과합니다. 같은 값은 상한 4.25에서는 통과하고 4.24에서는 실패합니다.

## 상한 기준값 형식

CRAP 상한과 mutation 최소 kill 비율은 같은 문자열 형식을 씁니다. 정수 또는 소수점 아래 최대 두 자리의 십진 문자열이며 정규식 `^(0|[1-9][0-9]*)(\.[0-9]{1,2})?$`에 맞아야 합니다. 앞자리 0, 부호, 공백, 지수 표기, 세 자리 이상의 소수는 `crapMaxInvalid`로 거부합니다. 문자열은 binary float 없이 정확한 분수로 읽습니다. 예를 들어 "8.5"는 17/2입니다. CRAP 상한은 0보다 커야 하며 0은 `crapMaxOutOfRange`입니다. 판정은 `numerator × limit.denominator ≤ limit.numerator × denominator`의 정수 비교입니다.

언어별 동일성 검증 자료는 [threshold-v1.json](../golden/gate/threshold-v1.json)입니다. 기본값, 정규식, 상한별 통과·실패 사례와 거부해야 하는 문자열을 함께 고정합니다.

## 표준 소수

표준 소수는 음수가 아닌 기약분수를 소수점 아래 최대 12자리로 표시합니다. 13번째 자리에서 정확히 절반이면 마지막 남는 숫자가 짝수가 되도록 반올림하는 round-half-to-even 규칙을 사용합니다. 마지막의 불필요한 0과 불필요한 소수점은 제거합니다.

|정확한 분수|표준 소수|
|---:|---:|
|17/4|4.25|
|1/3|0.333333333333|
|9876543121/80000000000|0.123456789012|
|246913578027/2000000000000|0.123456789014|
|1999999999999/2000000000000|1|

언어별 구현은 binary float, epsilon, locale formatter를 계산이나 gate에 사용하면 안 됩니다. 언어별 동일성 검증 자료는 [formula-v1.json](../golden/crap/formula-v1.json)입니다. 이 자료는 `2^53-1` 정상 입력, `2^53`과 `2^53+1` 오류, safe-integer 입력에서 생기는 큰 CRAP 분수와 80자리/48자리 표시용 분수를 함께 고정합니다.

## Raw JSON 읽기 경계

JSON 입력은 UTF-8 원본 byte에서 먼저 검증합니다. Object pair를 mapping으로 합치기 전에 같은
key가 두 번 나오면 `jsonDuplicateKey`로 거부합니다. JSON number token은 runtime 숫자로 바꾸기
전에 검사하며, 정수 token만 허용합니다. Fraction, exponent와 negative zero는
`jsonIntegerLexemeInvalid`, 절댓값이 9,007,199,254,740,991을 넘으면
`jsonIntegerOutOfRange`입니다. 각 nonnegative field의 음수와 0 허용 여부는 이 손실 없는 읽기 뒤
field 계약으로 검사합니다.

Golden의 `rawJsonInvalidCases[].rawInput`과 `rawDocument`는 실패해야 하는 JSON 원문을 string으로
보존합니다. Consumer는 이 string을 다시 UTF-8 byte로 만든 뒤 위 검증을 적용합니다. 특히
`2^53`과 `2^53+1`을 일반 JavaScript `JSON.parse`로 먼저 읽으면 두 값이 같아지므로, lossless
scanner 또는 동등한 raw-token validator보다 `JSON.parse`를 먼저 호출하면 안 됩니다.

## 결과 정렬 순서

같은 프로젝트를 반복 검사했을 때 보고서 행 순서도 항상 같아야 합니다. 각 언어 도구는 다음 순서를 그대로 사용합니다.

1. Coverage를 알 수 없는 callable을 먼저 놓습니다.
2. Coverage를 아는 callable은 반올림하지 않은 CRAP 기약분수를 교차 곱셈해 큰 값부터 놓습니다.
3. 값이 같으면 module-relative POSIX path의 UTF-8 byte, 0부터 시작하는 source byte 위치, callable ID의 UTF-8 byte 순서로 비교합니다.
4. 세 식별값이 모두 같은 두 행은 임의로 순번을 붙이지 않고 `identityAmbiguous` 오류로 거절합니다.

`sourceStartByte`는 JSON에서 정확히 공유할 수 있는 0부터 9,007,199,254,740,991까지만 허용합니다. CRAP의 numerator와 denominator는 이 상한을 적용하지 않고 arbitrary-precision integer로 비교합니다. 공통 반례는 [stable-sort-v1.json](../golden/crap/stable-sort-v1.json)에 있습니다.

Golden JSON의 known row는 identity 세 field와 numerator, denominator만 가져야 하고 unknown row는 identity 세 field와 `unknownReason`만 가져야 합니다. 두 형태를 섞거나 다른 field를 더하면 `rowShapeInvalid`입니다. Numerator는 `^(0|[1-9][0-9]*)$`, denominator는 `^[1-9][0-9]*$`에 맞는 JSON string이어야 하며, plus, 공백, underscore와 leading zero는 허용하지 않습니다.

Known fraction은 최대공약수가 1인 기약분수여야 합니다. `2/2`처럼 줄일 수 있는 값은
`fractionNotReduced`이며, 언어의 fraction class가 자동으로 줄이기 전에 원래 두 decimal string을
검사해야 합니다.
