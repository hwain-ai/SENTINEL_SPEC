# SENTINEL_SPEC

## 역할

SENTINEL_SPEC의 단일 책임은 언어별 SENTINEL 구현이 공유할 결과 형식, 품질 정책, 적합성 예제를 정의하는 것입니다.

현재 버전은 CRAP exact fraction 계산, 표준 소수 표시, mutation 9개 상태 검증과 killed-only gate를 실행 가능한 Python reference implementation으로 제공합니다.

## 현재 제공 범위

* [CRAP 수치 계약](contracts/crap.md): CRAP 8 이하 판정과 최대 12자리 round-half-to-even 표시
* [Mutation gate 계약](contracts/mutation-gate.md): 모든 in-scope mutant가 killed된 경우만 통과
* [결과 JSON Schema](schemas/result.schema.json): 언어별 결과의 공통 구조와 안전한 정수 범위
* `golden/`: 다른 언어가 같은 결과를 내는지 확인하는 공통 입력과 기대값

CLI, history, mutation backend 실행, 언어별 toolchain 설치는 이 단계의 범위가 아닙니다.

## Python package

package 이름은 sentinel-spec이고 Python 3.9 이상에서 설치할 수 있습니다. 실행 코드는 Python standard library만 사용하며 runtime dependency는 없습니다. 공개 함수는 `calculate_crap`, `crap_gate_passes`, `render_canonical_decimal`, `evaluate_mutation`입니다.

repository의 계약 검증은 다음 명령으로 실행합니다: `/usr/bin/python3 -m unittest discover -s tests -v`.

현재는 로컬 구현 단계이며 GitHub private remote는 아직 없습니다.

## 설계 근거

원본 작업공간 설계 문서: `docs/design-docs/2026-08-native-quality-tools.md`
