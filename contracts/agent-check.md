# 에이전트가 선택하는 검사와 측정 결과

## 입력

`sentinel check --file src/pricing.py --function calculate_discount --tests tests/test_pricing.py`

- `--file`은 측정할 기능 파일이며 반복할 수 있다. 프로젝트 루트 기준 경로를 사용한다.
- `--function`은 파일 하나 안의 함수 이름 또는 정확한 callable ID다. `()`를 붙이지 않는다. 이름이 없거나 모호하면 실패한다.
- `--tests`는 실행할 테스트 파일이며 반복할 수 있다. 생략하면 설정된 테스트 묶음을 사용한다. 기능 파일과 테스트 파일의 역할은 서로 다르다.
- `--all`/기본 호출은 설정된 기능 코드 전체, `--changed`는 Git 변경 목록과 기능 코드 목록의 교집합이다. `--file`과 동시에 사용하지 않는다.
- 파일 선택은 Git 변경 여부와 무관하다. 테스트만 수정한 경우에도 같은 기능 파일·함수를 재검사할 수 있다.
- 지원하지 않는 선택은 오류다. 전체 파일을 실행한 뒤 함수만 검사했다고 주장하지 않는다.
- Java 변이 백엔드는 행 단위 선택을 사용한다. 선택한 메서드와 다른 메서드가 같은 행에 겹치면 함수 선택을 거부한다. 이 경우 파일 전체를 선택한다.
- 프로젝트의 나머지 코드·설정·의존성은 실행에 필요하므로 보존한다. 측정 대상 선택과 테스트 실행 범위는 별도로 기록한다.

## 실행과 호환성

Python·TypeScript·Java의 기본 검사에는 자동 실행 시간 제한을 적용하지 않는다. 프로세스 회수 대기, 네트워크 요청·파일 잠금 등 검사가 아닌 작업의 대기 시간은 별개다.

tool-protocol-v1의 선택적 request field `selection`은 `files`, `functions`, `tests` 문자열 배열을 가진다. 이를 받은 어댑터는 response에 동일한 `selection`을 돌려줘야 한다. 미지원 구버전 어댑터가 선택을 무시하면 실행 결과를 거부한다.

선택적 response field `details`는 언어별 측정 결과다. 통합 실행기는 변이 개수와 ID·상태 목록 및 통과 판정의 일치 여부를 확인하고 `sentinel-diagnostics-v1`로 변환한다. 기존 공통 gate/evidence의 수식과 기준값은 바꾸지 않는다.

## 반환하는 사실

- `scope`: 실제 기능 파일, 선택 함수, 실행에 사용한 테스트 범위. 테스트 생략 시 Python은 설정된 테스트 루트, TypeScript는 수집된 테스트 파일, Java는 `testSelection: maven`으로 기본 Maven 테스트 탐색을 표시한다. 개별 실행 테스트 ID 전체를 제공한다는 의미는 아니다.
- `crap.limit`, `maxScore`, `pass`: 적용한 기준, 함수별 CRAP 최댓값, 판정.
- `crap.functions`: 파일·함수·식별자·위치와 CRAP, 복잡도, 커버리지 측정값. 언어별 coverageBasis를 보존한다.
- `crap.files`: 파일 안 함수 개수, 함수 CRAP 최댓값, 미측정 개수. 평균이나 별도의 100점 총점으로 바꾸지 않는다.
- `mutation.minimum`, `score`, `inScope`, `counts`, `pass`: 기준과 killed/inScope 백분율, 판정에 포함한 변이 개수, 상태별 개수, 판정. `inScope`는 테스트 파일이나 테스트 함수 개수가 아니다. `killed`는 테스트가 오류를 탐지한 변이 개수다.
- `mutation.mutants`: 변이 ID·파일·위치·실행 상태. 도구가 제공하는 경우 함수·연산자·원래 코드·변경 코드도 포함한다. 원인을 추측하지 않는다.
- `mutation.files`, `mutation.functions`: 같은 위치로 묶은 탐지 개수/전체 개수와 비율. 함수를 식별할 수 없는 변이는 파일 집계에 남긴다.
- 변이가 없는 세부 그룹은 `score: null`, `pass: null`, `reason: zeroMutants`다. 전체 변이가 0개면 전체 gate는 실패하며 100%로 표시하지 않는다.

수치는 기존 정확한 분수 계산으로 판정하고 표시값은 문자열로 제공한다. `noChanges`는 미검사다. 특정 파일·함수·테스트, 변경분 또는 일부 모듈의 통과는 `certified: false`이며 전체 인증으로 보고하지 않는다.

SENTINEL은 측정 사실을 반환한다. 테스트 설계, 요구사항과의 일치 여부, 수정 방향은 이를 호출한 에이전트가 판단한다.

## inScope와 통과 표시 읽기

예를 들어 `killed: 2`, `inScope: 2`, `score: "100"`이면 판정 대상 변이 두 개를 테스트가 모두 탐지했다는 뜻이다. 점수는 `killed / inScope × 100`이며, 변이가 없으면 100%로 계산하지 않는다.

`pass`는 놓인 위치에 따라 판단 범위가 다르다.

| 위치 | 판단 대상 |
|---|---|
| `details.mutation.functions[].pass` | 해당 함수의 mutation 점수가 기준을 충족했는가 |
| `details.mutation.files[].pass` | 해당 파일의 mutation 점수가 기준을 충족했는가 |
| `details.mutation.pass` | 검사 범위 전체의 mutation 결과가 기준을 충족했는가 |
| `details.crap.pass` | 검사 범위의 함수별 CRAP 결과가 기준을 충족했는가 |
| 명령 결과 최상위 `pass` | 명령의 최종 `exitCode`가 0인가 |

최상위 `pass`는 검사기가 정상 작동했는지를 나타내는 별도 진단 값이 아니다. 품질 미달, 잘못된 입력, 실행 오류, 취소와 미승인 실행은 모두 명령 실패가 될 수 있다. 에이전트는 `results[].status`와 제공된 `diagnostic`을 함께 읽는다.

- `qualityFailed`: 점수나 필수 측정 조건이 품질 기준을 충족하지 못했다. 이 상태만으로 검사기 고장을 뜻하지는 않는다.
- `noChanges`: 검사할 기능 코드 변경이 없어 실행을 건너뛰었다. 종료 0과 `pass: true`여도 테스트를 실행해 통과한 결과는 아니다.
- `backendError` 등 실행 실패 상태: 검사 실행이나 결과 수집에 문제가 있다. 정상적으로 얻은 점수와 제공되지 않은 측정값을 구분한다.

`certified`는 전체 설정 범위를 승인된 도구로 모두 검사해 통과했는지를 별도로 표시한다. 파일·함수·테스트 선택, 변경분 검사, 일부 모듈 검사와 `noChanges`는 전체 인증이 아니다. `--experimental` 실행은 세부 점수가 통과해도 최상위 종료 6, `pass: false`, `certified: false`를 반환한다.

최상위 판정 구현은 [SENTINEL cli.py](https://github.com/hwain-ai/SENTINEL/blob/main/src/sentinel/cli.py), 통합 출력 예시는 [결과 해석](https://github.com/hwain-ai/SENTINEL/blob/main/docs/results.md)에 있다.
