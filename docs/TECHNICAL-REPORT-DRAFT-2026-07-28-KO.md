# WIGTN Plugin for Codex

## 구현 절차는 줄이고 제품 개발의 계약은 남긴 이유

GPT‑5.5·GPT‑5.6 Sol paired evaluation과 WIGTN Plugin 0.3.0 설계 개정
Technical report v9 · 2026-07-28
상태: 공개 engineering report · 일반 코드 품질 향상 논문 아님

---

## 결론 먼저

WIGTN Plugin은 Codex보다 코드를 더 잘 쓰는 프롬프트 묶음으로 만들지
않았다. 반복해서 요청하는 제품 개발 작업을 재사용 가능한 기능으로
만들었다.

- 아이디어를 구현 가능한 PRD와 화면 명세로 정리한다.
- 요구사항을 작업과 실행 가능한 검사로 연결한다.
- 구현자의 완료 주장과 실제 검증 결과를 구분한다.
- commit, push, PR처럼 저장소를 바꾸는 작업의 권한과 범위를 확인한다.

처음에는 이 기능들을 구현 과정에 더 촘촘히 연결하면 코드 결과도
좋아질 수 있다고 봤다. 실험 결과는 달랐다.

- GPT‑5.6 Sol의 SWE-bench Verified 4개 paired block에서 Bare와 Plugin은
  모두 4/4 성공했다.
- 같은 성공을 얻는 동안 개정 전 Plugin의 중앙값은 wall time 151.7%,
  output token 141.2%, command 32.0%가 더 들었다.
- 더 어려운 FeatureBench 네 과제에서도 무결하고 재현된 positive lift는
  0건이었다.
- GPT‑5.5에서는 PRD 계약 충족이 Bare 0/3에서 Plugin 3/3으로 바뀌었다.
  일반 코딩과 실제 저장소 구현의 성공률은 달라지지 않았다.

이 결과로 제품 방향을 정했다.

> 일반 코딩은 Codex의 기본 동작에 맡긴다. WIGTN Plugin은 PRD 형식,
> 요구사항 ID, 수용 근거, 중단 재개 상태, Git 권한처럼 모델이 스스로
> 알 수 없는 제품 개발 규칙을 맡는다.

0.3.0에서는 구현을 지휘하는 절차를 줄이고 다음 네 경계에 기능을
집중했다.

1. **Specification** — 무엇을 만들지 결정하고 안정적인 요구사항 ID를 남긴다.
2. **Planning** — 요구사항을 task와 executable check로 연결하고 재개 상태를 보존한다.
3. **Verification** — 코드와 실행된 테스트 근거로 요구사항 충족을 판정한다.
4. **Release** — 검증 완료와 Git 실행 권한을 분리한다.

이 보고서가 주장하는 것은 “WIGTN Plugin이 일반 코드 품질을 높였다”가
아니다. **어디에 플러그인을 붙이면 도움이 되고, 어디에서는 오히려
비용이 되는지 측정해 제품을 고쳤다**는 것이다.

---

## 1. 왜 WIGTN Plugin을 만들었나

### 1.1 출발점

Codex를 사용하다 보면 같은 종류의 요청이 반복된다.

- “이 아이디어를 PRD로 정리해줘.”
- “PRD를 화면 명세와 구현 계획으로 바꿔줘.”
- “요구사항이 실제 코드에 반영됐는지 확인해줘.”
- “변경 범위를 검토하고 커밋하거나 PR을 올려줘.”

매번 긴 프롬프트로 작업 순서와 출력 형식을 다시 설명하는 대신,
WIGTN Plugin에 담을 제품 개발 규칙을 호출 가능한 Codex skill로 묶는 것이
출발점이었다. 목표는 모델의 코딩 방식을 통제하는 것이 아니라 반복되는
작업의 입력, 산출물, 완료 조건을 일정하게 만드는 것이었다.

### 1.2 왜 Codex 전용으로 다시 만들었나

기존 Claude Code 플러그인에는 역할 agent, slash command, 고정된
오케스트레이션을 전제로 한 부분이 있다. Codex는 skill 선택 방식과 기본
탐색·구현 루프가 다르다. 그대로 옮기면 같은 역할을 중복하거나 일반
코딩 요청까지 무거운 workflow로 바꿀 수 있었다.

Claude 플러그인은 건드리지 않았다. Codex용 구현을 별도 저장소에서
다음 원칙으로 다시 만들었다.

| 원칙 | Codex 구현 |
|---|---|
| 한 기능, 한 책임 | Product Spec, Work Planner, Acceptance Verifier, Release Readiness 등을 독립 skill로 분리 |
| 기본 동작 보존 | 일반 구현·버그 수정에는 Plugin workflow를 자동으로 붙이지 않음 |
| 강한 경로는 명시 호출 | `verified-delivery`는 사용자가 지정했을 때만 실행 |
| 결과로 판정 | 문서 길이나 명령 수가 아니라 코드, 실행 테스트, Git 상태를 사용 |
| 외부 변경은 별도 권한 | review, commit, push, PR 요청을 서로 다른 권한으로 취급 |

### 1.3 만들고자 한 제품

WIGTN Plugin 0.3.0은 다음 기능을 제공한다.

| 기능 | 산출물 또는 판정 |
|---|---|
| Product Spec | Compact/Full PRD, 안정적인 requirement ID, 누락 결정 |
| Screen Spec·Design Direction | IA, 사용자 흐름, 화면 명세, lo-fi handoff |
| Work Planner | requirement→task→check WorkGraph, resume, source drift |
| Acceptance Verifier | 요구사항별 code evidence와 executed-test evidence |
| Verified Delivery | 명시 호출 기반 fast/assurance 구현·검증 경로 |
| Release Readiness | 실제 Git 상태, 변경 범위, 사용자 권한에 따른 commit·push·PR |

문서 생성 도구만 모은 것도 아니고, 항상 실행되는 agent framework도
아니다. 필요한 작업에 해당 skill 하나를 붙이는 구조다.

---

## 2. 왜 모델 성능까지 측정했나

Plugin이 유용한 산출물을 만든다고 해서 구현 과정에도 항상 도움이 되는
것은 아니다. skill 설명, 계획 단계, 별도 검사, evidence 표는 모델의
탐색과 종료 판단을 바꾼다. 성공률이 그대로인데 명령과 token만 늘 수도
있다.

확인할 질문을 네 개로 나눴다.

| 연구 질문 | 측정값 |
|---|---|
| RQ1. 일반 코딩을 방해하는가 | Plugin이 Bare 성공을 실패로 바꾼 pair |
| RQ2. 코드 결과를 개선하는가 | Bare 실패 / Plugin 성공 pair |
| RQ3. 제품 계약을 더 잘 지키는가 | PRD·acceptance contract 충족률 |
| RQ4. 같은 결과에 비용이 얼마나 드는가 | wall time, output token, command |

GPT‑5.5+Plugin과 GPT‑5.6 Bare를 비교하지 않았다. 모델 차이를 Plugin
효과로 오해할 수 있기 때문이다. 각 모델 안에서 같은 task와 같은 실행
조건을 사용하고 Plugin만 켜고 껐다.

---

## 3. 평가 방법

### 3.1 평가층

서로 다른 결과를 하나의 “Plugin 점수”로 합치지 않았다.

| 평가층 | 확인한 것 | 자료 |
|---|---|---|
| 계약 회귀 | manifest, trigger, schema, authority가 깨지지 않는가 | 저장소 정적 검사 |
| 산출물 행동 | PRD·acceptance 형식을 실제 모델이 지키는가 | GPT‑5.5/5.6 smoke, package ablation |
| 실제 bug fix | 같은 코드 과제의 성공률과 비용이 달라지는가 | SWE-bench Verified |
| 어려운 feature | ceiling을 낮추면 positive lift가 생기는가 | FeatureBench development pilot |

### 3.2 외부 과제 포함 기준

코드 품질 평가에는 아래 조건을 모두 만족한 과제만 사용했다.

1. 문제문과 base commit이 고정되어 있다.
2. clean base에서 핵심 test가 실패한다.
3. gold patch가 같은 evaluator를 통과한다.
4. fail-to-pass test가 문제문에 적힌 동작을 검사한다.
5. pass-to-pass test가 기존 동작의 회귀를 검사한다.
6. 격리된 환경에서 재현된다.
7. agent가 hidden test와 reference patch를 볼 수 없다.

원본이 이미 통과하거나, 문제문에 없는 API를 강제하거나, 환경 누락으로
검사가 무너지는 과제는 실행 전에 제외했다.

### 3.3 주효과 평가 설정

| 항목 | 값 |
|---|---|
| 모델 | `gpt-5.6-sol` |
| reasoning | `high` |
| Codex CLI | `0.145.0` |
| benchmark | `princeton-nlp/SWE-bench_Verified` |
| dataset revision | `c104f840cc67f8b6eec6f759ebc8b2693d585d4a` |
| 과제 | `astropy__astropy-12907`, `pytest-dev__pytest-10051` |
| 반복 | 과제당 2회, Bare→Plugin / Plugin→Bare 순서 교차 |
| 환경 | 공식 per-instance Docker, 매 trial clean workspace |
| 판정 | official resolved, pass-to-pass, 비용 |

분석 단위는 `task × repetition`의 paired block 네 개다. 표본이 작고
discordant pair가 없으므로 p-value나 “통계적으로 유의한 향상”을
제시하지 않는다.

---

## 4. 결과

### 4.1 GPT‑5.6 Sol: 성공률은 같고 비용은 늘었다

| 과제 | Bare | 개정 전 Plugin |
|---|---:|---:|
| Astropy, trial 1 | resolved | resolved |
| Astropy, trial 2 | resolved | resolved |
| Pytest, trial 1 | resolved | resolved |
| Pytest, trial 2 | resolved | resolved |
| 합계 | **4/4** | **4/4** |

모든 patch가 fail-to-pass와 pass-to-pass를 통과했다. Plugin이 성공을
망가뜨린 pair도, 실패를 성공으로 바꾼 pair도 없었다.

| 중앙값 | Bare | 개정 전 Plugin | Plugin 증감 |
|---|---:|---:|---:|
| wall time | 120.21s | 302.62s | **+151.7%** |
| output token | 3,613 | 8,715.5 | **+141.2%** |
| command | 12.5 | 16.5 | **+32.0%** |

개정 전 `verified-delivery`는 작은 bug fix에도 별도 harness와 evidence
절차를 반복했다. 공식 결과가 같은 상황에서는 추가 절차가 품질이 아니라
비용으로 남았다.

### 4.2 FeatureBench: positive lift를 확인하지 못했다

SWE-bench 두 과제의 ceiling을 피하려고 Seaborn, Sphinx, MLflow,
Mypy 네 feature 과제를 추가했다.

| 과제 | Bare | Plugin | 판정 |
|---|---:|---:|---|
| Seaborn | 11.76%, unresolved | 첫 실행 100% | reference source 접근으로 무효, 재시험 tie |
| Sphinx | 7.69%, unresolved | 7.69%, unresolved | tie |
| MLflow | 0%, unresolved | 0%, unresolved | tie |
| Mypy | 30%, unresolved | 30%, unresolved | tie |

Seaborn Plugin 실행은 workspace 밖에 설치된 동일 프로젝트의 함수 본문을
읽었다. evaluator 성공 여부와 별개로 무효 처리했다. 새 workspace에서
순서를 바꿔 재시험하자 두 arm 모두 unresolved였다.

무결성 적격 positive와 재현된 positive는 각각 **0건**이다. 첫 네 pair의
중앙값은 command 17→38, output token 10,274→20,663.5였다.

### 4.3 GPT‑5.5: PRD 계약에는 효과가 있었고 코딩 성공률은 같았다

| 평가 | Bare | Plugin | 해석 |
|---|---:|---:|---|
| PRD smoke, 3회 | 0/3 | 3/3 | 명시한 PRD 계약 충족 |
| PRD package ablation, 2회 | Bare/Placebo 0/2 | Core/Full 2/2 | 길이가 아닌 skill 내용 효과 |
| uncertain acceptance, 3회 | 3/3 | 3/3 | 동률 |
| ordinary coding, 3회 | 3/3 | 3/3 | 동률, 쉬운 과제 |
| 실제 Pytest 구현, 1회 | resolved | resolved | 탐색적 비간섭 |

이 결과는 “좋은 PRD를 쓴다”는 보편적 평가가 아니다. WIGTN Plugin이
정의한 requirement ID, 결정 항목, acceptance 형식을 더 안정적으로
생성했다는 뜻이다. 코드 과제에서는 GPT‑5.5도 positive lift가 없었다.

---

## 5. 실험 뒤 무엇을 바꿨나

### 5.1 구현 경로를 둘로 나눴다

| 경로 | 사용하는 경우 | 실행 범위 |
|---|---|---|
| Fast | 국소 변경, 낮은 위험, 저장소 테스트 실행 가능 | inspect → minimal patch → focused test → 관련 suite 1개 |
| Assurance | auth, schema, persistence, concurrency, migration, 복수 요구사항 | stable ID, invariant, provenance, evidence artifact |

Fast path에서는 다음 작업을 하지 않는다.

- 작은 수정에 requirement matrix나 WorkGraph를 만든다.
- 저장소 테스트가 있는데 같은 happy path를 별도 harness로 다시 만든다.
- 사용자가 저장·인계를 요청하지 않았는데 evidence JSON을 생성한다.
- 관련 suite가 통과한 뒤 근거 없이 검사를 계속 추가한다.

### 5.2 외부 정답 접근과 무한 탐색을 막았다

- workspace 밖 동일 프로젝트, package cache, gold/reference source를
  구현 근거로 사용하지 않는다.
- 여러 file·symbol·interface가 명시된 작업만 편집 전 coverage census를
  작성한다.
- 두 diagnostic cycle 동안 새 증거가 없으면 탐색을 넓히지 않는다.
- reference leakage가 발생하면 evaluator 성공과 관계없이
  `Not verifiable`로 판정한다.

### 5.3 개정 후 한 번의 forward-test

같은 Pytest 과제에서 개정한 Plugin을 한 번 실행했다.

| 지표 | 개정 전 Plugin 중앙값 | 개정 후 1회 |
|---|---:|---:|
| official resolved | 2/2 | pass |
| output token | 10,470.5 | 4,466 |
| command | 23 | 10 |

output token은 57.3%, command는 56.5% 줄었다. 단일 개발 세트 결과라서
일반화하지 않는다. 개정 방향이 실제 실행에 반영됐는지 확인한
forward-test로만 사용한다.

---

## 6. WIGTN Plugin 0.3.0의 방향

### 6.1 코딩을 감싸는 하네스에서 제품 계약을 지키는 Plugin으로

개정 전에는 `verified-delivery`가 구현 과정 전체를 한 경로로 감쌌다.
0.3.0은 기능을 다음 위치로 옮겼다.

```text
일반 구현·버그 수정
  └─ Codex native workflow 또는 Fast path

제품 개발 계약이 필요한 작업
  ├─ Product Spec        요구사항과 결정
  ├─ Work Planner        task, check, resume, drift
  ├─ Acceptance Verifier code·executed-test evidence
  └─ Release Readiness   Git 상태와 실행 권한
```

### 6.2 0.3.0에 추가한 것

| 영역 | 구현 |
|---|---|
| Evidence Contract | 거짓 `verified`, 누락 gap, source drift, 권한 없는 외부 작업을 validator로 차단 |
| WorkGraph | requirement→task→check 상태, 중단 재개, source hash 변경 시 stale 전파 |
| Requirement import | WIGTN Plugin PRD뿐 아니라 Spec Kit, OpenSpec, BMAD 형식을 정규화 |
| Project context | 선택적 `.wigtn/project.json`으로 검증 명령과 보호 경로 공유 |
| Screen contract | IA·flow·screen·wireframe·handoff의 연결과 requirement anchor 검사 |
| Release state | branch, upstream, conflict, staged, unstaged, untracked를 mutation 없이 점검 |
| Evidence inspection | 파일 변경과 hash drift 뒤 기존 완료 판정을 재검사 |
| 평가 분리 | 정적 계약, model behavior, 외부 benchmark를 별도 suite로 운영 |

이 상태 파일들은 일반 코딩 때 자동 생성되지 않는다. 사용자가 저장형
계획, 세션 간 재개, 감사 가능한 handoff를 요청했을 때만 사용한다.

### 6.3 제품 메시지

WIGTN Plugin의 제품 메시지는 다음 한 문장으로 제한한다.

> Codex의 구현 능력은 그대로 사용하고, PRD에서 검증과 안전한 Git
> 릴리스까지 필요한 제품 개발 계약만 추가한다.

“코드를 더 잘 짜게 한다”, “모델 성능을 높인다”, “모든 저장소에서
품질이 오른다”는 표현은 현재 근거로 사용하지 않는다.

---

## 7. 어디까지 믿을 수 있나

### 현재 근거가 지지하는 주장

| 주장 | 판정 | 근거 |
|---|---|---|
| WIGTN Plugin이 정해진 PRD 계약의 재현성을 높인다 | 제한적으로 지지 | GPT‑5.5 smoke 0/3→3/3, ablation 0/2→2/2 |
| 일반 코딩의 성공을 크게 망가뜨리지 않는다 | 개발 표본에서 지지 | ordinary gate와 paired bug fix 동률 |
| 개정 전 heavy workflow는 같은 성공에 비용을 늘렸다 | 선택한 GPT‑5.6 과제에서 지지 | 4/4 tie, token·wall·command 증가 |
| WIGTN Plugin이 일반 코드 품질을 높인다 | 지지되지 않음 | 유효하고 재현된 positive lift 0 |
| 모델이 강할수록 항상 하네스를 줄여야 한다 | 미검증 | 두 모델과 작은 표본만 관측 |

### 한계

- SWE-bench 주효과는 Python bug fix 두 과제, 네 pair다.
- FeatureBench 파일럿은 네 과제이며 positive lift가 없다.
- GPT‑5.5 실제 저장소 복제는 한 과제, 한 반복이다.
- 독립 oracle 감사자와 blind human reviewer 수가 부족하다.
- 프론트엔드, 데이터베이스, 대규모 migration 결과는 없다.
- 0.3.0 개정 후 외부 holdout 반복은 아직 완료하지 않았다.

현재 가장 강하게 말할 수 있는 결과는 다음과 같다.

> 선택한 GPT‑5.6 Sol bug fix에서 개정 전 WIGTN Plugin은 성공률을
> 바꾸지 않고 비용을 늘렸다. 이 결과를 반영해 일반 구현 절차를 줄이고
> 제품별 계약과 검증·릴리스 경계에 기능을 집중했다.

---

## 8. 다음 검증

| 우선순위 | 평가 | 종료 조건 |
|---|---|---|
| P0 | 개정 후 fresh holdout 20 task | 5개 이상 repo, task당 3회, reference source 격리 |
| P0 | Fast/Assurance routing 10 task | 잘못된 Assurance 호출 0, median output overhead ≤25% |
| P1 | GPT‑5.5 실제 저장소 복제 | 2개 과제×2회, 순서 교차 |
| P1 | 독립 oracle 감사 | 포함·제외 합의 κ≥0.7 |
| P1 | blind patch review | arm을 숨긴 reviewer 2인 이상 |
| P2 | PRD→implementation 12 feature | 요구사항 누락, clarification, rework 측정 |
| P2 | release state 60 fixture | 권한 없는 mutation 0 |
| P2 | cross-platform | macOS/Linux와 fresh install 재현 |

fresh holdout이 끝나기 전에는 일반 코드 품질 향상을 제품 주장으로 쓰지
않는다. 0.3.0 릴리스의 합격 기준은 코드 lift가 아니라 다음 세 가지다.

1. 일반 코딩 요청에서 불필요한 heavy workflow를 호출하지 않는다.
2. 저장형 제품 계약의 drift와 거짓 완료 판정을 결정론적으로 막는다.
3. commit, push, PR은 사용자가 부여한 권한 안에서만 실행한다.

---

## 9. 재현 자료

- [외부 평가 프로토콜](EXTERNAL-EVAL-PROTOCOL-2026-07-28-KO.md)
- [SWE-bench machine-readable protocol](../tests/external/protocol-2026-07-28.json)
- [SWE-bench 결과와 제외 기록](../tests/external/swe-bench-verified/results-2026-07-28.json)
- [FeatureBench 사전 프로토콜](FEATUREBENCH-LIFT-PROTOCOL-2026-07-28-KO.md)
- [FeatureBench 파일럿과 leakage 감사](FEATUREBENCH-LIFT-PILOT-2026-07-28-KO.md)
- [FeatureBench 결과](../tests/external/featurebench/results-2026-07-28.json)
- [SWE-bench evaluation reference](https://www.swebench.com/SWE-bench/reference/harness/)
- [Anthropic, Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [OpenAI, Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
- [Claw-SWE-Bench](https://arxiv.org/abs/2606.12344)
