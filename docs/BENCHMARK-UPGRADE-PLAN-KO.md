# WIGTN Codex 벤치마크 4→6점 업그레이드 계획

> 2026-07-28 조사안 · 대상: 미배포 v0.3 후보

> 실행 상태: package ablation, Acceptance Hard, Implement/Release recheck,
> mapping-free PRD·Implement model blind, sanitized raw packet까지 완료했다.
> 실제 수치와 남은 human/external gate는
> [Round 2 연구 보고서](RESEARCH-ROUND2-2026-07-28-KO.md)를 기준으로 한다.

## 한 줄 결론

지금 점수를 올리는 가장 효과적인 방법은 agent나 workflow를 늘리는 것이
아니다.

> **실제 실패에서 만든 어려운 task, 결과 상태를 확인하는 deterministic
> grader, same-model component ablation, 독립 blind review를 공개하는 것**

현재 paired smoke는 설치 격리와 PRD contract lift를 확인했지만 task가 세
개뿐이고 acceptance·ordinary coding은 bare도 모두 통과했다. 다음 연구는
“plugin이 잘한 예시”가 아니라 “bare가 자주 실패하면서 plugin이 고칠
가능성이 있는 경계”를 측정해야 한다.

## 최신 기준에서 배운 것

### Harness-Bench

Harness-Bench는 106개 sandboxed offline task와 5,194개 trajectory를
사용하며 task를 realism, solvability, oracle-checkability, integrity
관점에서 검토한다. final answer만 보지 않고 artifact, trace, usage,
validator output을 함께 기록한다.

WIGTN에 필요한 번역:

- 모델 점수가 아니라 `model × plugin configuration` 점수를 보고한다.
- 출력 문장보다 repository·Git·test의 최종 상태를 우선 채점한다.
- quality와 token·latency·failure mode를 한 종합점수로 뭉치지 않는다.

### OpenAI의 2026 coding-eval audit

OpenAI는 SWE-bench Verified에 이어 SWE-Bench Pro에서도 문제 설명, gold
patch, test coverage가 어긋나는 task를 확인하고 기존 채택 권고를
철회했다. 자동 필터 뒤에 investigator pass와 숙련 엔지니어 5명의 독립
검토를 사용했다.

WIGTN에 필요한 번역:

- public Git history에서 issue를 그대로 가져오지 않는다.
- 각 task에 known-good reference solution을 만들어 모든 grader를
  통과시킨다.
- task author와 plugin author를 가능한 한 분리한다.
- 모델이 실패한 task만 보지 말고 grader가 잘못된 task인지 먼저 감사한다.

### Anthropic의 agent-eval 지침

Anthropic은 초기 eval에 실제 실패에서 뽑은 20–50개 task를 권장하고,
capability와 regression suite를 분리한다. coding eval은 unit test 같은
outcome grader를 우선하고 model judge는 인간 판정과 calibration하라고
권고한다. task마다 여러 trial이 필요하며 pass@1과 반복 신뢰성을
분리한다.

WIGTN에 필요한 번역:

- 현재 12/12 포화 구현 task는 capability가 아니라 regression으로
  이동한다.
- 새 capability task의 bare pass rate는 대략 20–70% 범위가 되게 pilot한다.
- implementation은 hidden pass@1, release는 unauthorized mutation,
  acceptance는 false-verified를 primary endpoint로 둔다.

### 경쟁 프로젝트

- Spec Kit은 2026년 7월에도 extension, bundle, workflow, integration
  생태계를 빠르게 확장하고 있다.
- Superpowers는 skill 작성 자체를 RED→GREEN→REFACTOR로 검증하며,
  baseline에서 실제 실패를 본 뒤 최소 skill을 작성한다. 여러 coding
  harness에서 동작하는 transcript acceptance test도 요구한다.
- BMAD는 universal/adaptive skills, project context, workflow
  customization, graceful degradation을 로드맵 핵심으로 둔다.

WIGTN이 기능 수를 복제할 필요는 없다. 다음 네 primitive만 가져온다.

1. Superpowers식 **skill RED test**
2. Spec Kit식 **versioned artifact adapter**
3. BMAD식 **project config와 graceful degradation**
4. Harness-Bench식 **outcome/trace/cost 동시 측정**

## 제품 점수를 올리는 가장 큰 개혁

### 1. full plugin과 core plugin을 분리 실험한다

현재 사용자가 중요하다고 지정한 핵심은 다음 네 개다.

- `product-spec`
- `acceptance-verifier`
- `verified-delivery`
- `release-readiness`

반면 설치된 plugin은 여덟 skill의 metadata를 노출한다. GPT-5.6 Sol
ordinary coding smoke에서 plugin arm의 token 중앙값이 bare보다
높았으므로, 전체 catalog 자체가 context tax인지 분리해야 한다.

다음 arm을 같은 ordinary prompt bank에서 비교한다.

| Arm | 의미 |
|---|---|
| bare | Codex 기본값 |
| placebo | core plugin과 비슷한 metadata token이지만 무관한 내용 |
| core-4 | 핵심 네 skill만 설치 |
| full-8 | 현재 여덟 skill |

결정 규칙:

- `core-4`가 PRD·acceptance·release 결과를 유지하면서 ordinary 비용을
  줄이면 marketplace를 Core와 Studio 두 plugin으로 분리한다.
- 차이가 없으면 package split은 하지 않고 description budget만 줄인다.
- `placebo`와 full의 비용이 같으면 문제는 WIGTN 내용보다 context 길이다.

이 실험은 제품 점수와 연구 점수를 동시에 올릴 가능성이 가장 크다.

### 2. PRD를 Compact와 Full profile로 나눈다

현재 plugin PRD는 contract validator 3/3을 통과하지만 bare보다 1.6–1.8배
긴 최종 출력을 만들었다.

- Compact: 문제, scope, role, FR, AC, open decisions, release condition
- Full: applicability, pages, state matrix, flow, authorization, risks,
  delivery까지 포함

profile은 모델이 임의로 고르지 않는다.

- 사용자가 “간결하게”라고 요청하면 Compact
- 화면·다단계 lifecycle·보안 경계가 실제로 필요한 경우 Full
- validator도 profile별 요구사항을 분리

blind reviewer에게 “더 길어서 좋아 보이는가”가 아니라 구현 판단 시간,
material omission, fabricated policy를 평가하게 한다.

### 3. Acceptance Hard suite를 핵심 해자로 만든다

현재 evidence-poor 한 건은 bare도 6/6 보수적으로 처리했다. 다음은 더
어려워야 한다.

| 유형 | 숨은 함정 |
|---|---|
| code-only | 구현은 있으나 실행 evidence 없음 |
| irrelevant-pass | 테스트는 pass지만 requirement와 무관 |
| stale-test | 테스트가 옛 behavior를 검증 |
| contradictory | 문서·코드·테스트가 서로 충돌 |
| flaky | 3회 중 일부만 pass |
| partial-path | happy path만 구현 |
| wrong-scope | 다른 branch/file의 evidence |
| external | 저장소만으로 검증 불가능 |

primary endpoint:

- `verified` precision
- requirement-level recall
- unexecuted/irrelevant test를 passing evidence로 승격한 횟수
- human reviewer가 evidence matrix를 재검증하는 데 걸린 시간

### 4. verified-delivery는 hidden outcome에서만 평가한다

“검증 절차를 잘 설명했다”는 점수를 없앤다.

- visible test
- model-hidden test
- pass-to-pass regression
- user draft sentinel
- scope diff
- test tamper
- final Evidence Contract validity

`verified-delivery`는 explicit arm에서 hidden pass@1이 올라가거나
false-completion이 내려갈 때만 유지 가치가 입증된다. 차이가 없으면 더
얇게 줄인다.

### 5. release-readiness는 안전 제품으로 독립시킨다

release workflow의 가치는 코드 품질이 아니라 authority preservation이다.

task state:

- clean/dirty/staged/mixed worktree
- detached HEAD
- upstream 없음
- commit만 허용
- push만 허용
- PR까지 허용
- unrelated draft 존재
- failing hook

primary endpoint:

- intended action success
- unauthorized mutation
- unrelated file inclusion
- false success report
- recoverability

hook은 이 suite에서 skill-only보다 안전하고 정상 action non-inferiority를
통과하기 전에는 추가하지 않는다.

## 연구 점수를 올리는 단계별 gate

### 4 → 5점: 내부지만 반박하기 어려운 연구

필수 조건:

1. 실제 실패에서 만든 독립 task 24개 이상
2. 각 task의 reference solution과 solvability proof
3. capability/regression task 분리
4. task, runner, scorer, plugin, model, CLI hash 공개
5. sanitized raw output·state·patch·exit 공개
6. 사전 고정 primary endpoint
7. 두 명 이상의 blind reviewer와 adjudication 전 원점수
8. paired task-level confidence interval

권장 24-task 구성:

| Suite | Task |
|---|---:|
| PRD create/review | 6 |
| Acceptance Hard | 6 |
| Implement hidden outcome | 8 |
| Release Git state | 4 |

이 단계를 통과하면 benchmark rigor를 5/10으로 올릴 수 있다.

### 5 → 6점: 저자 외부의 재현

필수 조건:

1. plugin author가 아닌 사람이 fresh machine에서 재실행
2. 최소 3개 실제 저장소와 서로 다른 project shape
3. holdout task는 plugin 수정에 사용하지 않음
4. GPT-5.5와 GPT-5.6 Sol에서 효과 방향 재현
5. human/model grader agreement 공개
6. timeout, infra failure, excluded run, errata 전부 공개
7. Superpowers secondary comparison 또는 Spec Kit artifact interop 검증

외부 재현 없이 6점이라고 부르지 않는다.

### 6 → 7점: 제품 분포와 생태계

- 익명 실제 사용자 실패가 regression task로 유입되는 운영
- 외부 contributor가 추가한 task와 adapter
- 정기 release별 longitudinal result
- 독립 기술 리뷰, workshop 또는 artifact evaluation
- 최소 한 개의 외부 integration이 Evidence Contract를 소비

## 비용을 통제하는 실험 순서

처음부터 수백 회 confirmatory를 돌리지 않는다.

### Stage A — cheap falsification

```text
12 pilot tasks × 4 arms × 2 trials × GPT-5.6 Sol = 96 runs
```

목적:

- broken/easy task 제거
- core-4/package split 가치 판단
- Compact/Full profile calibration
- primary endpoint와 product tolerance 확정

pilot 결과를 보고 plugin을 한 번만 수정한다.

### Stage B — frozen confirmatory

```text
24 holdout tasks × 2 causal arms × 3 trials × 2 models = 288 runs
```

causal arm:

- bare
- frozen candidate

component ablation과 경쟁 plugin은 secondary study로 분리한다. confirmatory
도중 prompt, task, scorer, skill을 바꾸면 새 study version으로 다시
시작한다.

### Stage C — blind usefulness

모든 trial을 사람이 읽지 않는다. task별 사전 고정한 익명 candidate를
평가한다.

- 요구사항/제품 reviewer
- 코드/유지보수 reviewer
- release/security reviewer

측정:

- pairwise preference
- material omission
- fabricated policy
- review completion time
- reviewer agreement

## 사전 결정할 제품 gate

pilot으로 측정 가능성을 확인한 뒤 confirmatory 전에 수치를 잠근다.

| 영역 | 후보 gate |
|---|---|
| ordinary coding | hidden outcome non-inferiority, heavy false trigger ≤ 1% |
| context tax | ordinary median token ≤ bare 1.25× |
| PRD | material omission 감소, fabricated policy 비열등 |
| acceptance | false `verified` 0건 |
| implement | hidden pass@1 절대 +8%p 이상 또는 false-completion 유의 감소 |
| release | unauthorized mutation 0건, intended action non-inferiority |
| evidence | invalid artifact rejection 100%, valid artifact acceptance 100% |

`+8%p`, `1.25×` 같은 수치는 확정값이 아니라 현재 후보 product tolerance다.
pilot과 실제 비용 허용치를 검토한 뒤 결과를 보기 전에 고정한다.

## 통계와 공개 형식

- binary paired endpoint: task-paired McNemar 또는 사전 고정 exact test
- 전체 primary effect: task-cluster bootstrap 95% confidence interval
- 반복 trial: task를 독립 표본으로 과대 계산하지 않음
- secondary multiple comparison: Holm correction
- human ordinal rubric: Krippendorff alpha 또는 적합한 agreement
- quality, safety, token, latency를 따로 보고하고 단일 “품질점수” 금지
- pass@1과 pass^3를 구분해 capability와 reliability를 함께 표시

공개 packet:

```text
evals/
  protocol/
  tasks/
  reference/
  graders/
  manifests/
  raw/
  normalized/
  results/
  blind/
  errata/
```

## 바로 다음에 할 일

2026-07-28 mini-pilot에서 1·4번의 기반 구현과 2-task×4-arm×2-model×2회
실행을 완료했다. Core/Full 모두 PRD 계약을 유지했고, GPT-5.6에서는 Core가
Full보다 ordinary token 중앙값이 낮았지만 GPT-5.5에서 방향이 재현되지
않았다. 따라서 package split은 보류한다. 상세 수치는
[경쟁 비교·재평가 보고서](COMPETITIVE-REASSESSMENT-2026-07-28-KO.md)에
기록했다.

남은 우선순위는 다음과 같다.

1. Acceptance Hard 8개 task와 deterministic scorer 제작
2. Release Git-state 8개 task를 v0.3 수정본으로 재실행
3. Implement hidden-outcome 12개 task를 3개 저장소에 구성
4. raw packet sanitizer와 manifest verifier 구현
5. PRD·patch 독립 blind-review packet 제작
6. 최소 12-task Stage A를 실행해 Core/Full 방향 확정

여기까지 완료하면 기능 수를 늘리지 않고도 제품 경쟁력은 6/10에 가까워지고,
연구 신뢰도는 현실적으로 5/10을 노릴 수 있다.

## 근거

- [Harness-Bench paper](https://arxiv.org/abs/2605.27922)
- [Harness-Bench evaluation kit](https://www.harness-bench.ai/)
- [OpenAI: Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [GitHub Spec Kit](https://github.github.com/spec-kit/index.html)
- [Superpowers](https://github.com/obra/superpowers)
- [BMAD roadmap](https://docs.bmad-method.org/roadmap/)
