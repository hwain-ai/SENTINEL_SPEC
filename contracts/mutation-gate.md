---
type: Executable Contract
status: draft
generated: { by: "process:codex", at: "2026-09-03T06:15:42Z" }
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

1. 9개 상태 count, inScope, unauthorizedExclusion이 bool이 아닌 0 이상의 정수인지 확인합니다.
2. 9개 상태 count의 합이 inScope와 정확히 같은지 확인합니다.
3. inScope가 0이면 통과시키지 않고 kill rate도 만들지 않습니다.
4. inScope가 1 이상이고 killed가 inScope와 같으며 나머지 8개 상태와 unauthorizedExclusion이 모두 0일 때만 통과합니다.
5. inScope가 1 이상이면 kill rate를 `killed / inScope` 기약분수로 계산합니다.

따라서 timeout-only, ignored-only, survived가 하나라도 있는 결과와 승인받지 않은 제외가 있는 결과는 모두 실패합니다. zero-mutant 결과를 100%로 꾸미지 않습니다.

언어별 동일성 검증 자료는 [mutation-v1.json](../golden/gate/mutation-v1.json)입니다.
