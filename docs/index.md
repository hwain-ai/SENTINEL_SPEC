# 문서 안내

각 문서의 내용과 함께 확인할 코드·설정 경로입니다.

`docs/manifest.json`을 수정한 뒤 `python scripts/docs_lint.py --write-index`로 이 목록을 갱신합니다.
코드 변경에 필요한 문서는 `python scripts/docs_lint.py --base HEAD`로 확인합니다.
Python 명령은 환경에 맞게 Windows에서 `py -3`, Linux에서 `python3`로 바꿀 수 있습니다.
검사는 관련 문서의 실제 변경 여부를 확인하며, 설명이 정확한지는 사람이 검토해야 합니다.

| 문서 | 내용 | 관련 코드·설정 |
| --- | --- | --- |
| [README.md](../README.md) | 공통 계산 계약, 스키마, 테스트 실행 방법 | `golden/**`, `pyproject.toml`, `schemas/**`, `src/**`, `toolchain.lock.json` |
| [contracts/agent-check.md](../contracts/agent-check.md) | 파일·함수·테스트 선택과 진단 결과의 필드 의미 | `golden/**`, `pyproject.toml`, `schemas/**`, `schemas/diagnostics.schema.json`, `src/**`, `toolchain.lock.json` |
| [contracts/crap.md](../contracts/crap.md) | 함수별 CRAP 계산과 커버리지·행 정렬 계약 | `golden/**`, `golden/crap/**`, `pyproject.toml`, `schemas/**`, `src/**`, `src/sentinel_spec/crap*.py`, `toolchain.lock.json` |
| [contracts/mutation-gate.md](../contracts/mutation-gate.md) | 변이 상태, 분모와 탐지율의 통과 기준 | `golden/**`, `golden/mutation/**`, `pyproject.toml`, `schemas/**`, `src/**`, `src/sentinel_spec/mutation.py`, `toolchain.lock.json` |
| [docs/contributing.md](contributing.md) | 문서 색인·소스 연결표 관리, diff 검사와 push 훅 사용 | `.githooks/**`, `.github/workflows/**`, `docs/manifest.json`, `scripts/docs_lint.py`, `scripts/verify_repository.sh`, `tests/test_docs_lint.py` |
