---
type: Implementation Note
status: draft
generated: { by: process:codex, at: 2026-09-08T12:08:06Z }
sources:
  - resource: ../../SENTINEL_GO/docs/go-mutesting-adapter.md
    title: Go 직접 라이브러리 연결
  - resource: ../../SENTINEL_JAVA/docs/pit-report-adapter.md
    title: Java PIT 보고서 연결
  - resource: ../../SENTINEL_JAVA/docs/pit-execution-probe.md
    title: Java 고정 PIT 실제 실행과 지원 경계
---

# 외부 adapter 구현 진행

2026-09-07 후보 조사 이후 Go의 외부 라이브러리 직접 실행과 Java의 PIT 보고서 연결을 추가했다. 이어 9월 8일 후속 작업에서 Go 반복 검사의 소스·테스트·실패 위치 대조, Java의 실제 PIT 실행과 후보별 정상 대조·변이 재실행 증거를 구현했다. 다음 단계 개발에 대한 사용자 승인을 받아 진행했으며, 기존 backend 교체나 신규 도구의 운영 인증 승인은 하지 않았다.

| 작업 | 입력·의존 | 산출물 | 현재 상태 |
|---|---|---|---|
| G: Go 연결 | 고정 외부 함수, 기존 복사본·테스트 실행기 | 프로젝트·전체 후보 계획·실제 결과·실패 위치 지문, 원본 대조 2회와 후보별 재실행 2회 | 제한 profile의 실제 실행과 반복 대조 구현. 상태 문자열만 같은 다른 실패는 검출 성공에서 제외 |
| J: Java 연결 | PIT 1.30.0, JUnit 5, 7개 JAR 고정 목록 | 별도 PitProbeMain, 독립 dry-run·실제 PIT·XML 후보 대조와 후보별 4회 새 실행 | Java 17/Jupiter 일반 메서드 profile의 입력·결과·실패 위치 재현 증거 구현. 운영 인증은 미완료 |
| R: 교차 검토 | G와 J 구현 | 원래 검사 보존·복원 경로 보호·무결성·취소·크기 제한, 실제 검증과 문서 | 발견한 중요 문제를 재현 후 수정하고 새 테스트로 재검증. 기본값 전환과 분리 |

G와 J는 서로 다른 언어 저장소에서 독립 진행했고 R은 두 결과를 검토했다. Go는 추가 읽기 전용 검토자가 수정 후 회귀 테스트까지 실행했다. 세부 내용은 [Go 문서](https://github.com/hwain-hwang/SENTINEL_GO/blob/main/docs/go-mutesting-adapter.md), [Java 실행 문서](https://github.com/hwain-hwang/SENTINEL_JAVA/blob/main/docs/pit-execution-probe.md), [Java 보고서 계약](https://github.com/hwain-hwang/SENTINEL_JAVA/blob/main/docs/pit-report-adapter.md)에 둔다.

재실행 증거를 추가하기 전 단계의 검증은 Go 전체 패키지·연결 관련 race·module 무결성 검사 통과, 변경 대상 Go 함수 124개 CRAP 기준 초과·측정 불가 0개, Java 전체 232개 테스트 통과·함수 670개 CRAP 기준 초과·측정 불가 0개였다. 이번 단계는 Java 증거 수집에 한정하며 Go 구현·승인 상태는 바꾸지 않았다. 기존 Java 문서의 type 누락과 비표준 변경 이력 항목 수정도 이전 단계 이력이다. 문서 owner는 임의로 지정하지 않았다.

이번 단계의 최종 Java 검증은 2026-09-08 12:08 UTC scripts/self-crap.sh 종료 0, 전체 테스트 260개 통과·함수 724개 CRAP 기준 초과·측정 불가 0개다. 별도 읽기 전용 검토에서 지적한 이벤트 외부 쓰기와 건너뛴 동적 테스트 누락을 재현·수정했다. 이후 지원하지 않는 실패 종류가 assertAll 안에 감싸지는 반례도 고쳤으며, 테스트와 최종 품질 검사는 주 작업자가 실행했다. 새 람다 2개를 측정 가능한 이름 있는 연결로 바꿨고 검사 기준을 낮추지 않았다.

Go·Java·SPEC의 개념 문서 6개는 OKF 필수 속성, 색인 양방향 연결, 상대 링크·출처 파일 경로, 신선도, 변경 이력 검사를 통과했다. 각 문서의 담당자가 아직 지정되지 않은 권고는 남겨둔다. 자동으로 사람이나 팀을 소유자로 정하지 않았다.

작은 경계값 함수의 강한 테스트는 두 도구 모두 후보 3개를 검출했고 약한 테스트는 1개 검출·2개 생존이었다. 이는 각 3종 연산자 profile의 관측값이며 실제 프로젝트 전체나 두 도구의 모든 규칙이 동등하다는 증명이 아니다. 두 CLI 모두 certified=false와 종료 6을 유지한다. Java의 backendCounts는 PIT 원래 상태이며 SENTINEL의 엄격한 검출 증거로 승격하지 않는다.

고정 외부 함수를 호출하는 Go와 고정 외부 프로그램·공식 바이트코드 API를 함께 사용하는 Java는 버전 갱신의 연결 방식이 다르다. Go는 module·checksum·선택 함수 호환성을, Java는 JAR 목록·checksum·공식 API·CLI 옵션·XML 후보 대응을 갱신한다. 외부 변이 규칙 본문을 공통 계약인 SENTINEL_SPEC으로 옮기거나 복사하지 않는다.

## 다음 수와 실패 시 복구

1. Java 후보별 정상 대조·재실행은 구현했고, 상태 문자열이나 XML의 KILLED만으로 검출을 인정하지 않는다. 다음에는 지원 범위를 넓히기 전에 같은 줄의 서로 다른 단언, 그룹화된 finally 후보, 동적·반복 테스트의 증거 계약을 검증한다. 현 프로필은 묶인 후보와 동적 메서드 컨테이너를 거부한다. Go의 지문도 지원하지 않는 assertion·외부 상태·실행기 무결성까지 증명한다고 확대 해석하지 않는다.
2. 같은 실제 프로젝트에서 기존·신규 도구를 나란히 실행한다. 제한 규칙과 전체 규칙의 차이를 누락 또는 성능 우위로 오해하지 않는다.
3. 지원 범위·무결성·운영 격리·자원 예산·강제 종료 뒤 잔여 파일 회수를 검증해 별도 승인한다. 현재 프로세스 그룹 종료는 보안 격리가 아니다. 문제 발생 시 opt-in 연결을 중단하고 기존 기본값을 유지한다.
4. 기본값 전환 후에도 버전 변경을 adapter 호환성 시험과 잠금 갱신에 한정한다. 6개월 뒤 외부 규칙 변경 때문에 공통 결과 의미나 저장 이력을 바꿀 필요가 없게 유지한다.
5. 그다음 코딩 도우미 설치 plugin을 기존 CLI 위에 연결한다. .NET 실행기와 Clojure 대체 도구는 별도 평가 범위이며 이번 작업으로 해결됐다고 표시하지 않는다.

내부 adapter plugin은 외부 검사 도구와 결과를 연결하고, Codex/Claude 설치 plugin은 코딩 도우미가 CLI를 부르게 하는 배포·사용 계층이다. 이번 구현은 전자의 일부다. [두 plugin의 비교와 SPEC의 역할](mutation-backend-evaluation.md#plugin-두-종류와-spec의-역할)
