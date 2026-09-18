# SENTINEL_SPEC

SENTINEL 언어 검사기가 공유하는 CRAP 계산, mutation 판정, 결과 형식과 검증 예제입니다.

## 계약과 결과 읽기

| 문서 | 내용 |
|---|---|
| [CRAP 수치 계약](contracts/crap.md) | 정확한 분수 계산, 기준값, 소수 표시와 정렬 |
| [Mutation 판정 계약](contracts/mutation-gate.md) | 변이 상태, `killed / inScope` 비율과 통과 조건 |
| [선택 검사와 결과](contracts/agent-check.md) | 파일·함수·테스트 선택, 점수·위치, `pass`와 `certified` 해석 |
| [문서 목록](docs/index.md) | 계약·스키마·개발 안내 |

`schemas/`는 결과·증거·진단 JSON의 구조를 정의합니다. `golden/`은 언어별 구현에서 같은 결과가 나와야 하는 입력과 기대값입니다. 테스트 실행과 언어별 도구 설치는 [SENTINEL](https://github.com/hwain-ai/SENTINEL)이 담당합니다.

## Python 패키지와 검증

`sentinel-spec`은 Python 3.9 이상에서 동작하며 실행 시 표준 라이브러리만 사용합니다. 주요 공개 함수는 `calculate_crap`, `crap_gate_passes`, `render_canonical_decimal`, `evaluate_mutation`, `parse_crap_max`, `parse_mutation_min`입니다.

저장소 루트에서 공통 계약과 예제를 검사합니다.

```sh
# -B: 바이트코드 파일 생성 금지, discover: tests 폴더의 시험 탐색
python3 -B -m unittest discover -s tests -v
```
