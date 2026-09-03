---
type: Executable Contract
status: draft
generated: { by: "process:codex", at: "2026-09-03T06:15:42Z" }
owner: "human:hwain"
sources:
  - resource: ../golden/crap/formula-v1.json
    title: CRAP 수식과 표준 소수 golden vector
---

# CRAP 수치 계약

한마디로, 모든 SENTINEL 구현은 부동소수점 오차 없이 같은 CRAP 값과 같은 통과 여부를 만들어야 합니다.

## 입력

|이름|뜻|허용값|
|---|---|---|
|CC|Cyclomatic Complexity, 실행 경로의 복잡도|bool이 아닌 1 이상의 정수|
|C|covered unit, 테스트가 실행한 측정 단위 수|bool이 아닌 0 이상의 정수|
|T|total unit, 전체 측정 단위 수|bool이 아닌 1 이상의 정수이며 C 이상|

입력 하나라도 범위를 벗어나면 계산을 계속하지 않고 validation error를 반환합니다.

## 계산 순서

1. denominator를 T의 세제곱으로 계산합니다.
2. numerator를 CC의 제곱 곱하기 `(T-C)`의 세제곱에 CC 곱하기 denominator를 더해 계산합니다.
3. numerator와 denominator의 최대공약수로 나눠 기약분수를 만듭니다.
4. 원래 numerator가 `8 × denominator` 이하일 때만 통과합니다. 표시용 소수는 판정에 사용하지 않습니다.

예를 들어 CC가 4이고 C가 3, T가 4이면 계산 전 분수는 272/64이고 기약분수는 17/4입니다. 표준 소수는 4.25이며 8 이하이므로 통과합니다.

## 표준 소수

표준 소수는 음수가 아닌 기약분수를 소수점 아래 최대 12자리로 표시합니다. 13번째 자리에서 정확히 절반이면 마지막 남는 숫자가 짝수가 되도록 반올림하는 round-half-to-even 규칙을 사용합니다. 마지막의 불필요한 0과 불필요한 소수점은 제거합니다.

|정확한 분수|표준 소수|
|---:|---:|
|17/4|4.25|
|1/3|0.333333333333|
|246913578025/2000000000000|0.123456789012|
|246913578027/2000000000000|0.123456789014|
|1999999999999/2000000000000|1|

언어별 구현은 binary float, epsilon, locale formatter를 계산이나 gate에 사용하면 안 됩니다. 언어별 동일성 검증 자료는 [formula-v1.json](../golden/crap/formula-v1.json)입니다.
