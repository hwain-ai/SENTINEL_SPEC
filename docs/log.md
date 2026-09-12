# 변경 기록

## 2026-09-08

- **Update** external-adapter-progress.md: Java 전체 260 테스트·724 함수 CRAP 최종 통과 반영. 경로 교체·동적 테스트 누락·묶인 미지원 실패의 반례 수정과 운영 미완료 항목 구분.
- **Update** external-adapter-progress.md, index.md: 사용자 승인 후 Java 후보별 4회 새 실행·공식 core API 연결과 실패 위치 대조 구현 반영. 기본 backend와 운영 인증 상태 유지.
- **Update** 외부 adapter 후속: Go 입력·목록·결과·실패 위치의 반복 대조와 Java 실제 PIT CLI 실행 상태를 반영. 별도 프로브·제한 profile·미승인 경계 유지.
- **Update** 검토·검증: Go 계측 호환성·원본 검사 보존·안전한 복원과 Java 소스·도구·후보 목록 무결성을 보강. Go 대상 함수 124개와 Java 전체 함수 670개 CRAP 통과, Java 테스트 232개 통과.
- **Creation** external-adapter-progress.md: Go 직접 실행·Java 보고서 연결의 작업 의존, 미완료 승인 조건과 후속 순서 기록.
- **Update** index.md·후보 평가: 9월 7일 조사와 9월 8일 구현 진행을 구분해 연결. 기존 backend 승인 기록은 유지.

## 2026-09-07

- **Creation** mutation-backend-evaluation.md: Certitude·PIT·ArcMutate·Go 후보·Stryker 비교와 실측, 외부 개발자 근거, adapter 도입 조건 기록.
- **Creation** fixtures/backend-evaluation-2026-09-07.json: 소규모 강한·약한 테스트의 고정 버전·입력·결과 기록. 승인 golden과 분리.

## 2026-09-03

- **Update** Raw JSON 경계 강화: duplicate key, non-integer number token과 safe-integer 초과를 native number 변환 전에 거부하고 unsafe golden 입력을 exact raw string으로 보존.
- **Update** Fraction 기약 조건 강화: half-even-down decimal vector를 기약분수로 고치고 stable row에 `fractionNotReduced` 반례 추가.
- **Update** Cross-language golden 강화: float·UTF-16·unknown 입력 순서 comparator 반례, strict row wire 문법, 큰 분수와 `2^53+1` 경계를 추가하고 path 기준을 module-relative로 통일.
- **Update** CRAP·mutation gate: JSON safe integer 상한과 초과값 golden 반례를 추가.
- **Creation** CRAP 정렬 계약: unknown 우선, exact risk 내림차순, UTF-8 byte 식별자 순서와 safe-integer 경계 추가.
- **Creation** Stable-sort golden vector: source offset, UTF-8·UTF-16 정렬 차이, 중복 identity와 2^53 반례 추가.
- **Creation** CRAP·Mutation 계약: exact fraction, canonical decimal, 9개 상태와 killed-only gate 규칙 추가.
- **Creation** Golden vector·결과 schema: 언어별 구현이 공유할 입력·기대값과 JSON 구조 추가.
- **Update** README·문서 색인: 현재 구현 범위, 공개 API와 검증 진입점 반영.
- **Creation** SENTINEL_SPEC 문서 번들: OKF v0.2 init 골격 생성.
