---
okf_version: "0.2"
---

# SENTINEL_SPEC 문서

SENTINEL_SPEC의 사용법과 변경 이유를 찾는 문서 시작점입니다.

## 실행 가능한 계약

* [CRAP 수치 계약](../contracts/crap.md) - exact fraction 계산, CRAP 상한(기본 8) gate와 표준 소수 규칙
* [Mutation gate](../contracts/mutation-gate.md) - 9개 상태 합계와 최소 kill 비율(기본 100%) 판정 규칙
* [CRAP golden vector](../golden/crap/formula-v1.json) - 언어별 CRAP 구현이 재현할 입력과 기대값
* [CRAP 정렬 golden vector](../golden/crap/stable-sort-v1.json) - 위험도·UTF-8 byte·source byte 위치의 공통 정렬 규칙
* [Mutation golden vector](../golden/gate/mutation-v1.json) - 언어별 mutation gate가 재현할 입력과 기대값
* [기준값 golden vector](../golden/gate/threshold-v1.json) - CRAP 상한·최소 kill 비율의 문자열 형식, 기본값과 상한별 통과·실패 사례

## 도구 선택 근거

* [외부 mutation 도구 후보 평가](mutation-backend-evaluation.md) - 개발자 공개 경험, PIT 실제 실행, Stryker 유지와 plugin 경계
* [외부 adapter 구현 진행](external-adapter-progress.md) - Java 후보별 정상 대조와 변이 재실행, 남은 운영 조건

## 운영 기록

* [변경 기록](log.md) - 문서 번들의 생성과 변경 내역
