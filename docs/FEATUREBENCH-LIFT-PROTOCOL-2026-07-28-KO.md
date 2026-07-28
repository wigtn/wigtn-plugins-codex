# WIGTN FeatureBench quality-lift 프로토콜 v1

상태: 모델 실행 전 동결
동결일: 2026-07-28
목적: 일반 bug fix가 아니라 feature-level 과제에서 WIGTN의 positive
quality lift 가능성을 탐색한다.

> 실행 후 결과와 protocol deviation은
> [FeatureBench quality-lift 파일럿 결과](FEATUREBENCH-LIFT-PILOT-2026-07-28-KO.md)에
> 분리해 기록했다. 이 사전 문서의 규칙은 결과에 맞춰 수정하지 않았다.

## 1. 연구 질문

기존 SWE-bench Verified 실험은 Python bug fix 두 개에서 bare와 plugin이
모두 성공해 ceiling effect가 발생했다. 이번 라운드는 WIGTN의 assurance
path가 겨냥하는 복수 요구사항, 여러 interface, multi-file feature
implementation에서 다음을 묻는다.

- RQ1: post-reform WIGTN이 bare 실패를 공식 성공으로 바꾸는가?
- RQ2: 둘 다 실패할 때 WIGTN이 독립 acceptance test 통과율을 높이는가?
- RQ3: WIGTN이 bare 성공을 실패로 바꾸는 negative interference가 있는가?
- RQ4: 같은 결과를 얻는 데 추가되는 wall time, output token, command는
  얼마인가?

## 2. 벤치마크 선택

주 벤치마크는 `LiberCoders/FeatureBench` fast split이다.

- feature 단위 실행 평가
- gold patch와 F2P/P2P 제공
- CPU 평가가 가능한 fast split
- Codex 실행을 공식 지원
- 공개 leaderboard에서 GPT-5.5 resolved가 26.7%여서 기존 100% ceiling보다
  처리 효과를 관측할 여지가 있음

SWE-bench Pro는 2026-07-08 공개된 OpenAI 감사에서 public split의 약
30%가 broken으로 추정되었으므로 이번 주효과 평가에서 제외한다.
SWE-Lancer Diamond는 장기 후보로 유지하지만 현재 공개 harness와
WIGTN arm을 같은 로컬 조건으로 신속하게 반복하기 어려워 다음 단계로
미룬다.

## 3. 결과 비의존 task 선택

FeatureBench fast split에서 다음 조건만 사용한다.

1. gold patch, FAIL_TO_PASS, PASS_TO_PASS가 모두 존재한다.
2. 서로 다른 repository를 선택한다.
3. `sha256("wigtn-feature-v1-2026-07-28:" + instance_id)` 오름차순으로
   정렬한다.
4. 상위 후보부터 oracle 감사를 수행한다.
5. clean base F2P 실패, gold 전체 통과, prompt-test 정합성, Docker 재현을
   모두 만족하는 첫 네 과제를 pilot에 고정한다.

모델 성공 여부, 기존 leaderboard의 per-task 결과, gold patch 크기는
선택 조건으로 사용하지 않는다. 과제 탈락은 모델 실행 전에만 가능하며
사유를 machine-readable manifest에 남긴다.

## 4. Arm

| Arm | 입력 |
|---|---|
| Bare | 원본 FeatureBench problem statement와 공통 실행 제약 |
| WIGTN | 동일 입력 + 동결된 `verified-delivery` assurance path 명시 호출 |

WIGTN arm은 plugin 전체를 `.wigtn-eval/plugin`에 복사하고
`skills/verified-delivery/SKILL.md`를 완전히 읽도록 한다. 평가
인프라 디렉터리는 수정하거나 patch에 포함할 수 없다.

모델, reasoning effort, Codex CLI, timeout, container, repository
snapshot은 두 arm에서 동일하다.

## 5. 실행 설계

- 모델: `gpt-5.6-sol`
- reasoning effort: `high`
- Codex CLI: `0.145.0`
- pilot: 네 task × 두 arm × 1회
- 순서: task rank가 홀수면 Bare→WIGTN, 짝수면 WIGTN→Bare
- 모든 실행은 clean instance image에서 시작
- hidden test와 gold patch는 agent에 공개하지 않음
- agent patch만 공식 FeatureBench evaluator로 채점

pilot에서 discordant outcome이 발생하면 방향과 무관하게 해당 task를
새 clean workspace에서 역순으로 한 번 더 실행한다. positive task만
선택적으로 재실행하지 않는다.

## 6. 판정

### 1차 endpoint

- positive discordant: Bare unresolved, WIGTN resolved
- negative discordant: Bare resolved, WIGTN unresolved
- net lift: positive discordant 수 − negative discordant 수

### 2차 endpoint

- FeatureBench acceptance pass rate
- F2P/P2P 개별 결과
- output token, command, wall time
- 변경 파일 수와 production diff 크기
- 완료 주장과 official result의 calibration

둘 다 unresolved인 pair에서 partial pass rate가 높아져도
`resolved quality lift`로 세지 않는다.

## 7. Claim gate

네 task pilot에서 positive discordant가 하나 이상이고 negative
discordant가 없으면 “positive signal”이라고만 쓸 수 있다. 일반 품질
향상 주장은 다음을 모두 만족하기 전 금지한다.

- 별도의 fresh holdout 20 task 이상
- 5개 이상 repository
- 같은 task에 대한 paired arm
- task-level paired bootstrap 95% CI
- McNemar exact test
- 독립 oracle reviewer 2인, 포함 판단 합의도 κ ≥ 0.7
- blind patch reviewer 2인 이상
- positive discordant가 negative discordant보다 반복적으로 많음

pilot이 0 lift면 플러그인을 과제에 맞춰 다시 튜닝한 뒤 같은 task로
주효과를 주장하지 않는다. 해당 task는 development set으로 전환하고
새 holdout을 동결한다.

## 8. 외부 근거

- [FeatureBench official repository](https://github.com/LiberCoders/FeatureBench)
- [FeatureBench ICLR 2026 paper](https://openreview.net/forum?id=41xrZ3uGuI)
- [OpenAI coding-eval audit](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
- [OpenAI SWE-Lancer](https://openai.com/index/swe-lancer/)
