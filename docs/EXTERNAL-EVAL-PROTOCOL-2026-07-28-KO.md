# WIGTN Codex 외부 평가 프로토콜 v1

상태: 2026-07-28 실행 전 고정
대상: `wigtn-plugins-with-codex`의 선택적 구현·검증 하네스
주요 모델: `gpt-5.6-sol`, reasoning effort `high`

## 1. 왜 이 평가를 하는가

초기 내부 평가는 플러그인의 계약 파일, 트리거, 검증 스크립트가 의도대로 동작하는지는 보여줬다. 그러나 그것만으로 “플러그인이 강한 기본 모델의 코드 품질을 높인다”고 말할 수는 없다. 플러그인이 만든 규칙을 같은 플러그인이 만든 검사기로 확인하면 순환 검증이 되기 때문이다.

이번 평가는 다음 반증 가능 질문에 답한다.

- **RQ1 — 비간섭성:** 플러그인이 이미 강한 모델의 외부 과제 성공률을 떨어뜨리지 않는가?
- **RQ2 — 품질 향상:** 동일 모델·동일 과제에서 플러그인이 독립 실행 oracle의 통과율을 높이는가?
- **RQ3 — 검증 정직성:** 외부 테스트를 볼 수 없는 조건에서 완료·검증 주장의 강도가 실제 결과와 일치하는가?
- **RQ4 — 비용:** 성공 여부가 같을 때 플러그인의 시간·출력 토큰·도구 호출 증가는 얼마인가?

핵심 추정량은 같은 과제·모델·실행 예산에서 `plugin - bare`의 paired outcome 차이다. 모델 간 절대 성능 비교가 아니다.

## 2. 과제 포함 기준

과제는 실행 전에 아래 기준으로 감사한다.

1. 공개 문제문과 평가 대상 커밋이 고정되어 있다.
2. 원본 커밋에서 최소 하나의 핵심 검사가 실패한다.
3. 공식 또는 제3자 reference patch가 모든 핵심 검사를 통과한다.
4. 핵심 검사가 문제문에 명시된 observable outcome을 검사한다.
5. 구현이 만든 자체 테스트만으로 합격할 수 없다.
6. 필수 의존성이 고정된 격리 환경에서 재현된다.
7. 평가 중 네트워크가 필요하지 않다.
8. 테스트 수정, oracle 파일 탐색, reference patch 접근이 차단된다.

다음 중 하나라도 해당하면 confirmatory 결과에서 제외한다.

- 문제에 없는 함수명·인자명·파일 경로를 테스트가 강제한다.
- 원본이 이미 전부 통과해 ceiling effect가 있다.
- reference patch도 실패한다.
- 환경 누락 때문에 구현과 무관하게 실패하거나 연쇄 skip된다.
- 정규식·문자열 존재 확인이 실제 동작을 잘못 판정한다.
- 실행 후 결과를 보고 포함 여부를 바꿔야 한다.

## 3. oracle 신뢰도 등급

| 등급 | 조건 | 사용 |
|---|---|---|
| A | 독립 fail-to-pass + pass-to-pass, clean base 실패, gold 통과, 격리 Docker | 주효과·홀드아웃 |
| B | 명시 계약에 대한 독립 실행 테스트, 일부 정적 검사 포함 | 보조 결과 |
| C | 정적/문자열 검사 중심 또는 일부 계약 불일치 | 진단 전용 |
| D | 환경 파손, 원본 전부 통과, 명백한 prompt-test mismatch | 제외 |

SWE-bench Verified 과제는 개별 과제마다 clean-base/gold 재현을 다시 확인한 뒤 A로 인정한다. “Verified”라는 이름만으로 자동 인정하지 않는다.

## 4. 실험군

| arm | 입력 |
|---|---|
| Bare | 문제문 + 동일한 실행 제약 |
| Plugin | 문제문 + 동결된 WIGTN `verified-delivery` 명시 호출 |

두 arm 모두 다음을 동일하게 유지한다.

- 모델, reasoning effort, Codex CLI 버전
- 기준 커밋과 Docker 이미지
- wall-clock 상한
- sandbox와 네트워크 정책
- 사용자 규칙 무시 옵션
- 외부 테스트 비공개

플러그인 arm만 동결 스냅샷을 workspace의 숨김 평가 디렉터리에서 읽는다. 스냅샷은 실행 중 수정할 수 없고 결과 patch에서 제외한다.

## 5. 반복과 순서

- 과제당 arm별 최소 2회 independent trial
- trial은 매번 clean workspace에서 시작
- 첫 반복은 Bare → Plugin, 두 번째 반복은 Plugin → Bare로 순서를 교차
- 동일 trial seed를 강제할 수 없으므로 exact paired blocking은 `task × repetition`으로 정의
- 개발 중 본 과제와 최종 holdout 과제를 분리

`n < 20 paired tasks`에서는 p-value로 일반화를 주장하지 않는다. 성공률, paired delta, 비용 중앙값, trial 간 일관성, 실패 유형을 보고한다. 충분한 표본이 쌓이면 task-level paired bootstrap 95% CI와 McNemar exact test를 추가한다.

## 6. 측정값

### 1차

- official resolved: fail-to-pass 전부 통과 + pass-to-pass 회귀 없음
- audited requirement pass rate
- 검증 주장 calibration: 주장한 상태와 외부 결과의 일치 여부

### 2차

- wall-clock seconds
- output tokens
- tool/command calls
- changed production lines
- 새 테스트 수
- 불필요한 파일 변경
- 오류 분류: 구현, 회귀, 계약 오해, 환경, oracle 결함

### 해석 우선순위

1. 외부 functional outcome
2. 회귀 여부
3. 검증 주장 calibration
4. 비용
5. 스타일·코드 모양

경로가 아니라 결과를 채점한다. 더 많은 문서·테스트·명령을 만들었다는 사실 자체에는 가점을 주지 않는다.

## 7. 사전 의사결정 규칙

| 관찰 | 제품 결정 |
|---|---|
| 성공률 동일, 비용 +25% 이하, calibration 개선 | 선택적 유지 |
| 성공률 동일, 비용 +25% 초과, calibration 개선 없음 | 기본 구현 경로에서 제거 |
| 성공률 하락 또는 회귀 증가 | 해당 단계 비활성화 후 원인 수정 |
| 성공률 상승이 20개 이상 holdout에서도 일관 | 제한적 quality-lift 주장 허용 |
| 소표본에서만 상승 | “유망 신호”로만 표기 |

현재 데이터로 허용되는 최상위 표현은 “외부 과제에서 비간섭성 또는 검증 calibration을 관찰했다”이다. “일반적으로 코드 품질을 높인다”는 표현은 20개 이상 독립 과제, 복수 저장소·과제 유형, task-level CI가 확보되기 전 금지한다.

## 8. 신뢰성 위협

- 모델 비결정성: 반복과 순서 교차로 완화
- 과제 오염 가능성: 최신 private benchmark가 아니므로 절대 성능이 아니라 paired harness effect만 해석
- 단일 모델: GPT-5.5 보조 복제 전에는 모델 일반화 금지
- 평가자 편향: 2인 독립 oracle 감사 전에는 “저자 감사”로 표기
- 소표본: 유의성·일반 품질 향상 주장 금지
- ARM 호스트에서 x86 Docker 에뮬레이션: 성공 판정에는 영향이 작지만 wall-clock의 외부 일반화는 제한

## 9. 출처

- Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- SWE-bench, [Evaluation harness](https://www.swebench.com/SWE-bench/reference/harness/)
- OpenAI, [Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
- Claw-SWE-Bench, [paper](https://arxiv.org/abs/2606.12344)
