---
type: Implementation Note
status: draft
generated: { by: process:codex, at: 2026-09-08T12:08:06Z }
sources:
  - resource: ../../SENTINEL_JAVA/docs/pit-report-adapter.md
    title: Java PIT 보고서 연결
  - resource: ../../SENTINEL_JAVA/docs/pit-execution-probe.md
    title: Java 고정 PIT 실제 실행과 지원 경계
---

# 외부 adapter 구현 진행

2026-09-07 후보 조사 이후 Java의 PIT 보고서 연결을 추가했다. 이어 9월 8일 후속 작업에서 실제 PIT 실행과 후보별 정상 대조·변이 재실행 증거를 구현했다. 다음 단계 개발에 대한 사용자 승인을 받아 진행했으며, 기존 backend 교체나 신규 도구의 운영 인증 승인은 하지 않았다.

| 작업 | 입력·의존 | 산출물 | 현재 상태 |
|---|---|---|---|
| J: Java 연결 | PIT 1.30.0, JUnit 5, 7개 JAR 고정 목록 | 별도 PitProbeMain, 독립 dry-run·실제 PIT·XML 후보 대조와 후보별 4회 새 실행 | Java 17/Jupiter 일반 메서드 profile의 입력·결과·실패 위치 재현 증거 구현. 운영 인증은 미완료 |
| R: 교차 검토 | Java 구현 | 원래 검사 보존·복원 경로 보호·무결성·취소·크기 제한, 실제 검증과 문서 | 발견한 중요 문제를 재현 후 수정하고 새 테스트로 재검증. 기본값 전환과 분리 |

구현과 별도 검토 결과는 [Java 실행 문서](https://github.com/hwain-ai/SENTINEL_JAVA/blob/main/docs/pit-execution-probe.md)와 [Java 보고서 계약](https://github.com/hwain-ai/SENTINEL_JAVA/blob/main/docs/pit-report-adapter.md)에 둔다.

기존 Java 문서의 type 누락과 비표준 변경 이력 항목 수정도 이전 단계 이력이다. 문서 owner는 임의로 지정하지 않았다.

이번 단계의 최종 Java 검증은 2026-09-08 12:08 UTC scripts/self-crap.sh 종료 0, 전체 테스트 260개 통과·함수 724개 CRAP 기준 초과·측정 불가 0개다. 별도 읽기 전용 검토에서 지적한 이벤트 외부 쓰기와 건너뛴 동적 테스트 누락을 재현·수정했다. 이후 지원하지 않는 실패 종류가 assertAll 안에 감싸지는 반례도 고쳤으며, 테스트와 최종 품질 검사는 주 작업자가 실행했다. 새 람다 2개를 측정 가능한 이름 있는 연결로 바꿨고 검사 기준을 낮추지 않았다.

당시 개념 문서는 OKF 필수 속성, 색인 양방향 연결, 상대 링크·출처 파일 경로, 신선도, 변경 이력 검사를 통과했다. 각 문서의 담당자가 아직 지정되지 않은 권고는 남겨둔다. 자동으로 사람이나 팀을 소유자로 정하지 않았다.

작은 경계값 함수의 강한 테스트는 Java PIT 후보 3개를 검출했고 약한 테스트는 1개 검출·2개 생존이었다. 이는 3종 연산자 profile의 관측값이며 실제 프로젝트 전체나 모든 규칙의 검증 결과가 아니다. 프로브 CLI는 certified=false와 종료 6을 유지한다. Java의 backendCounts는 PIT 원래 상태이며 SENTINEL의 엄격한 검출 증거로 승격하지 않는다.

Java는 고정 외부 프로그램·공식 바이트코드 API를 함께 사용하므로 버전 변경 때 JAR 목록·checksum·공식 API·CLI 옵션·XML 후보 대응을 갱신한다. 외부 변이 규칙 본문을 공통 계약인 SENTINEL_SPEC으로 옮기거나 복사하지 않는다.

## 다음 수와 실패 시 복구

1. Java 후보별 정상 대조·재실행은 구현했고, 상태 문자열이나 XML의 KILLED만으로 검출을 인정하지 않는다. 다음에는 지원 범위를 넓히기 전에 같은 줄의 서로 다른 단언, 그룹화된 finally 후보, 동적·반복 테스트의 증거 계약을 검증한다. 현 프로필은 묶인 후보와 동적 메서드 컨테이너를 거부한다.
2. 같은 실제 프로젝트에서 기존·신규 도구를 나란히 실행한다. 제한 규칙과 전체 규칙의 차이를 누락 또는 성능 우위로 오해하지 않는다.
3. 지원 범위·무결성·운영 격리·자원 예산·강제 종료 뒤 잔여 파일 회수를 검증해 별도 승인한다. 현재 프로세스 그룹 종료는 보안 격리가 아니다. 문제 발생 시 opt-in 연결을 중단하고 기존 기본값을 유지한다.
4. 기본값 전환 후에도 버전 변경을 adapter 호환성 시험과 잠금 갱신에 한정한다. 6개월 뒤 외부 규칙 변경 때문에 공통 결과 의미나 저장 이력을 바꿀 필요가 없게 유지한다.
5. 그다음 코딩 도우미 설치 plugin을 기존 CLI 위에 연결한다.

내부 adapter plugin은 외부 검사 도구와 결과를 연결하고, Codex/Claude 설치 plugin은 코딩 도우미가 CLI를 부르게 하는 배포·사용 계층이다. 이번 구현은 전자의 일부다. [두 plugin의 비교와 SPEC의 역할](mutation-backend-evaluation.md#plugin-두-종류와-spec의-역할)
