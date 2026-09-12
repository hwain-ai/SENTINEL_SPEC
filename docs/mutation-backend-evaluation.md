---
type: Research Note
status: draft
generated: { by: process:codex, at: 2026-09-07T12:50:00Z }
sources:
  - resource: https://testing.googleblog.com/2021/04/mutation-testing.html
    title: Google 개발자의 mutation testing 운영 경험
  - resource: https://pitest.org/
    title: PIT 공식 문서
  - resource: https://www.synopsys.com/verification/simulation/testbench-quality-assurance.html
    title: Synopsys 검증 도구 지원 언어
  - resource: https://github.com/avito-tech/go-mutesting
    title: Avito go-mutesting
  - resource: https://github.com/go-gremlins/gremlins
    title: Gremlins
  - resource: https://stryker-mutator.io/
    title: Stryker Mutator
stale_after: 2026-10-07
---

# 외부 mutation 도구 후보 평가

외부 도구를 설치하고 SENTINEL은 연결과 판정을 맡는 방향을 추천한다. Java는 PIT, JS/TS는 기존 StrykerJS, Go는 go-mutesting과 Gremlins를 연결 시험할 가치가 있다. 이 문서는 **추천과 실측 기록**이며, 기존 승인 backend를 교체했다는 뜻이 아니다.

Mutation testing은 코드를 일부러 바꾸고 기존 테스트가 그 오류를 잡는지 확인하는 검사다. 여기서 backend는 코드를 바꾸고 테스트를 실행하는 외부 도구, adapter는 그 도구와 SENTINEL을 연결하는 코드다. 버전 고정은 같은 도구로 결과를 재현하기 위한 것이며, 외부 도구 활용과 반대되는 개념이 아니다.

## 선택 가능한 유지보수 방식

| 접근 | 장점 | 부담과 실패 시 복구 |
|---|---|---|
| 외부 릴리스 설치 + 작은 adapter | 변경 규칙은 원 개발자가 관리한다. SENTINEL은 실행·결과 계약만 유지한다 | 새 버전마다 보고서와 실패 분류를 재검증한다. 이전 버전 잠금으로 돌아갈 수 있다 |
| upstream 소스를 저장소에 복사 | 실행 경계를 세밀하게 제어할 수 있다 | 6개월 뒤 원본 개선을 수동 병합해야 한다. 자체 수정이 쌓일수록 되돌리기 어렵다 |
| 상용 확장 선택 | 지원 계약과 추가 기능을 구매할 수 있다 | 비용·라이선스·오프라인 동작을 별도 확인해야 한다. 이번 작업에서 구매하지 않았다 |

추천은 첫 번째다. 단, SENTINEL의 엄격한 결과 계약을 만족하는지 확인하기 전 기존 backend를 제거하지 않는다.

## 언어별 판단

| 언어 | 후보와 확인 사실 | 추천·제한 |
|---|---|---|
| Java | PIT는 Java/JVM용이며 Maven 연결을 제공한다. ArcMutate는 PIT의 상용 확장이다 | PIT를 우선 연결 시험한다. 상용 지원·변경 코드 분석 요구가 생기면 ArcMutate를 별도로 평가한다 |
| Java 후보로 제시된 Certitude | Synopsys 자료는 하드웨어 testbench, VHDL·Verilog·SystemVerilog·SystemC·C/C++를 다룬다 | Java 지원 근거를 확인하지 못했다. 다른 동명 제품이라면 정확한 제품 URL이 필요하다 |
| Go: avito-tech/go-mutesting | 외부 실행 명령 연결과 JSON 출력이 있다. 고정 commit을 현재 설치된 Go에서 실행했다 | SENTINEL의 테스트 실패 증거 수집과 연결하기 좋은 후보다. 보고서 점수는 그대로 사용할 수 없다 |
| Go: Gremlins | 설치 가능한 실행 파일과 상태별 JSON 보고서가 있다. 공식 문서는 작은 Go module 사용과 0.x 호환성 주의를 명시한다 | 독립 실행 편의가 좋은 대안이다. 대규모 저장소 시간과 보고서 완전성은 별도 시험한다 |
| JS/TS | 현재 SENTINEL_TS는 StrykerJS 10.0.0과 Vitest runner 10.0.0을 사용한다 | 새 자체 엔진을 만들지 않고 기존 Stryker 연결을 유지·보강한다 |
| .NET | Stryker.NET은 StrykerJS와 별도 도구이며 C# 프로젝트에 연결한다 | 기존 5개 언어의 구현에 포함되지 않는다. 후보 조사만 했고 .NET 실행기는 추가하지 않았다 |
| Python·Clojure | Python은 이미 mutmut를 사용한다. Clojure의 대체 도구는 이번 실행 비교 대상이 아니다 | Python은 유지한다. Clojure의 현행 backend와 남은 검증을 다른 언어의 선정으로 해결됐다고 보지 않는다 |

PIT·Stryker·go-mutesting·Gremlins는 로컬에서 실행하는 오픈소스 도구다. 이를 사용하는 것과 유료 SaaS에 소스를 전송하는 것은 다르다. 지원 범위의 근거는 [PIT](https://pitest.org/), [ArcMutate](https://www.arcmutate.com/), [Synopsys](https://www.synopsys.com/verification/simulation/testbench-quality-assurance.html), [Stryker.NET](https://stryker-mutator.io/docs/stryker-net/getting-started/), [Gremlins](https://github.com/go-gremlins/gremlins), [Avito](https://github.com/avito-tech/go-mutesting)다.

## 다른 개발자의 경험을 어떻게 반영했는가

1. Google의 Goran Petrovic은 변경 코드에 대한 빠르고 유용한 피드백을 강조하고 전체 mutation 점수 자체를 목표로 삼는 것을 경계한다. 해당 글은 특정 제품의 추천이 아니다. SENTINEL에서는 빠른 변경 코드 검사와 전체 범위의 엄격한 인증 결과를 구분하는 근거로 삼는다. [Google Testing Blog, 2021-04-12](https://testing.googleblog.com/2021/04/mutation-testing.html)
2. Google 연구진의 대규모 운영 논문도 코드 변경 중심 실행과 불필요한 변이 줄이기를 다룬다. 이것을 모든 실리콘밸리 개발자의 합의나 현재 제품별 시장 점유율로 확대하지 않는다. [Practical Mutation Testing at Scale, 2021](https://arxiv.org/abs/2102.11378)
3. Gremlins 유지보수자는 큰 module의 실행 시간이 길어질 수 있고, 0.x의 minor 업데이트에 호환성을 보장하지 않는다고 직접 적었다. 따라서 편한 설치만으로 채택하지 않고 실제 프로젝트 시간 예산을 시험해야 한다. [공식 README](https://github.com/go-gremlins/gremlins)
4. go-mutesting의 Go 1.26 실패 제보는 참고했지만, 제보에 나타난 오래된 의존성과 현재 commit을 구분했다. 이번 고정 commit은 Go 1.27.1의 작은 예제에서 실행됐다. 과거 이슈만으로 현재 후보를 배제하지 않는다. [개발자 제보 #44](https://github.com/avito-tech/go-mutesting/issues/44)

공개된 개발자 글·논문·이슈를 조사한 것이며, 개발자에게 직접 연락하거나 의견을 받은 것은 아니다.

## 실제 실행 비교

2026-09-07 Linux amd64에서 숫자가 0보다 큰지 판정하는 작은 함수를 검사했다. 강한 테스트는 입력 1·0·-1을 확인하고, 약한 테스트는 입력 1만 확인했다. 두 테스트 모두 원래 코드에서는 통과한다. 데이터는 [실행 기록](fixtures/backend-evaluation-2026-09-07.json)에 남겼다.

| 도구 | 고정 실행 대상 | 강한 테스트 | 약한 테스트 | 약한 테스트의 종료 코드 |
|---|---|---|---|---|
| PIT | 1.30.0, JUnit5 plugin 1.2.3 | 3개 생성, 3개 검출 | 3개 중 1개 검출, 2개 생존 | 1, 기준 100 미달 |
| Avito go-mutesting | 48d0401f00fbfb9502adc2c5138497ad8ccfafb9 | 3개 생성, 3개 검출 | 3개 중 1개 검출, 2개 생존 | 0, JSON 출력 설정 |
| Gremlins | 0.6.0 Linux amd64 | 2개 생성, 2개 검출 | 2개 중 1개 검출, 1개 생존 | 0, efficacy·coverage 기준을 각각 100으로 전달한 실행 |

Go는 1.27.1, Java는 Temurin 17.0.20.1+1·Maven 3.9.16·JUnit 5.10.2를 사용했다. Gremlins archive SHA-256은 b02a42e47935f891c9a411d68c07e211c7082609e79c2435b67c85ee9658c538이며 공식 checksum과 대조했다.

변이 개수가 다른 것은 변경 규칙이 다르기 때문이다. 작은 예제의 숫자로 검출 능력·속도·대규모 안정성 순위를 매길 수 없다. 도구 종료 코드는 관찰값 그대로 기록했으며, 0을 SENTINEL 검사 통과로 해석하거나 운영 인증 결과로 발행하지 않았다.

중요한 경계는 다음과 같다.

- go-mutesting의 MSI 계산에는 killed뿐 아니라 error와 skipped도 분자에 포함된다. 100% 점수를 killed-only로 바꾸면 안 된다. JSON에는 원본·변경 소스와 실행 출력도 포함되므로 공개 결과로 그대로 전달하면 안 된다. [고정 소스](https://github.com/avito-tech/go-mutesting/blob/48d0401f00fbfb9502adc2c5138497ad8ccfafb9/internal/models/report.go)
- Gremlins 0.6.0 보고서의 mutants_total 집계는 모든 상태의 합이 아니다. files의 개별 변이를 다시 검증해야 한다. 위 종료 코드 관찰의 근본 원인까지 규명한 것은 아니다. [고정 보고서 구현](https://github.com/go-gremlins/gremlins/blob/v0.6.0/internal/report/report.go)
- PIT의 KILLED 결과와 killingTest 이름만으로 SENTINEL의 assertion 증거가 충족되지는 않는다. 원본 대조 실행, 실패 종류 확인, 동일 변이 재실행과 후보 전체 목록 검증이 추가로 필요하다.

## plugin 두 종류와 SPEC의 역할

| 구분 | ② SENTINEL 내부 adapter plugin | ③ Codex/Claude 설치 plugin |
|---|---|---|
| 연결 대상 | SENTINEL과 PIT·Stryker·Go 도구 | 코딩 도우미와 SENTINEL CLI |
| 하는 일 | 검사 범위 전달, 실행, 도구별 결과와 실패 종류 검증 | 설치 안내, 명령 호출, 결과 설명 |
| 도구를 바꿀 때 | 해당 언어 adapter와 버전 잠금을 바꾼다 | CLI 계약이 같으면 변경을 줄일 수 있다 |
| 제공하지 않는 것 | 코딩 도우미의 설치·명령 UI | mutation 생성과 결과의 진위 검증 |

둘은 경쟁 대안이 아니다. 먼저 ②의 실행 경계를 안정화하면 나중에 ③이 CLI를 호출할 수 있다. 초기부터 임의 코드를 자동 탐색해 실행하는 plugin 장치를 추가할 필요는 없다. 승인된 adapter만 연결하면 실행 가능 코드의 범위를 제한할 수 있다.

SENTINEL_SPEC은 외부 도구가 아니라 언어별 결과가 지켜야 할 공통 규칙과 시험 입력이다. 도구 이름은 각 adapter가 알고, 공통 판정은 정규화한 상태와 증거만 알아야 한다. 현재 SPEC에는 Python 참조 코드도 있으므로 "JSON만 있는 저장소"라고 부르는 것도 정확하지 않다. 외부 도구를 사용해도 [killed-only 계약](../contracts/mutation-gate.md)은 필요하다.

## 이번 개선과 다음 도입 순서

이번 제품 변경은 SENTINEL_TS의 실제 Stryker 설치 진단과 실행 전 확인이다. 기존 doctor가 설치 상태와 관계없이 고정 버전과 ready를 출력하던 문제를 회귀 테스트로 재현하고 수정했다. 설치 파일을 읽어 버전·식별자·CLI 파일 지문을 확인하고, 누락·불일치는 unavailable과 종료 코드 5로 알린다. 기존 전체 설치 지문 검증기를 대체하지 않는다. [구현 설명](../../SENTINEL_TS/docs/stryker-runtime.md)

앞으로의 순서는 추천이며, 현재 backend 승인 기록을 덮어쓰지 않는다.

1. Java PIT와 Go 후보의 독립 adapter를 만들고 버전·무결성·라이선스를 잠근다. 원본 backend는 그대로 둔다.
2. 후보 누락, 0개 변이, 생존, timeout, compile/runtime error, 비정상 중단, 실패 종류 증거, 소스 복원 시험을 통과시킨다. 미충족이면 기존 backend로 돌아가며 성공으로 표시하지 않는다.
3. 같은 실제 프로젝트에서 기존·신규 결과를 나란히 실행해 범위 차이·검출 차이·시간을 비교한다. 숫자가 달라질 때는 규칙 차이와 누락을 구분한다.
4. 검증된 도구만 기본값으로 전환한다. 6개월 뒤에도 도구 버전 변경은 adapter의 호환성 시험으로 제한하고, SPEC이나 저장 결과 의미는 유지한다.
5. CLI 배포가 안정된 뒤 Codex/Claude plugin과 .NET 실행기를 별도 범위로 검토한다. 변경 코드 전용 결과를 전체 검사 통과 증거로 재사용하지 않는다.

외부 릴리스·지원 상태가 변할 수 있어 이 조사는 한 달 뒤 재확인한다. 대규모 성능, 상용 라이선스 조건, 새로운 Go adapter, PIT assertion 증거 연결과 .NET 지원은 아직 검증·구현하지 않았다.

위 구현 상태는 2026-09-07 조사 시점의 기록이다. 이후 2026-09-08에 추가한 Go 제한 profile 직접 실행과 Java PIT 보고서 연결은 [후속 구현 진행](external-adapter-progress.md)에 별도로 기록한다. 신규 backend의 기본값 전환·운영 인증을 뜻하지 않는다.
