# WIGTN Codex 플러그인 경쟁 비교·재평가

> 기준일 2026-07-28 · 미배포 v0.3 후보 · Opus 비교 제외

## 결론부터

이번 변경으로 WIGTN은 “스킬 모음”에서 **선택적 제품 계약 + 검증 가능한
handoff + 권한 경계**를 가진 얇은 Codex harness로 한 단계 나아갔다.
다만 Spec Kit, OpenSpec, Superpowers, BMAD를 전체 범위에서 따라잡았다고
말할 수는 없다.

현재 증거가 허용하는 주장은 다음뿐이다.

> 동일 모델의 테스트 PRD에서 WIGTN Core 4와 Full 8은 bare와 같은 길이의
> placebo가 충족하지 못한 WIGTN Compact PRD 계약을 재현했다. 일반 코딩
> 정답률은 네 arm이 모두 같았고, 구현 품질과 실제 저장소 일반화는 아직
> 입증되지 않았다.

따라서 지금 Full 8을 없애거나 Core 4를 별도 제품으로 배포하지 않는다.
Core 4는 다음 12-task pilot의 유력 후보이고, Compact PRD와 read-only
artifact importer는 유지할 가치가 있다.

## 무엇을 실제로 추가했나

| 변경 | 가져온 패턴 | 현재 상태 | 판단 |
|---|---|---|---|
| Compact/Full PRD profile | Spec Kit의 단계화된 artifact 계약 | profile별 validator와 fixture | 유지 |
| 일반 stable ID 지원 | cross-artifact 일관성 | `FR-` 접두사 대신 요구사항 표를 검증 | 유지 |
| 요구사항 importer | OpenSpec의 artifact resume·interop | WIGTN/Spec Kit/OpenSpec/BMAD Markdown → Evidence Contract | 유지, read-only 한정 |
| Core 4/Placebo 4 builder | harness component ablation | metadata 길이를 맞춘 격리 package | 연구 도구로 유지 |
| outcome summarizer | Harness-Bench식 결과·비용 분리 | PRD/일반 코딩 deterministic outcome + token/latency | 유지 |
| Evidence Contract | artifact handoff·권한 보존 | schema, validator, 10개 정적 사례 | 유지 |

추가하지 않은 것도 중요하다.

- BMAD식 다수 agent·workflow를 복제하지 않았다.
- Smart Ralph식 장기 자율 루프와 상태 daemon을 넣지 않았다.
- cc-thingz식 global hook을 넣지 않았다.
- ordinary coding을 PRD→구현→커밋 lifecycle로 자동 승격하지 않았다.

이 기능들은 범위를 넓히지만, 현재 WIGTN의 가장 큰 미해결 문제인
“실제 구현 품질 향상”을 바로 증명하지 못하고 context tax와 권한 위험을
키울 수 있다.

## 최신 경쟁군과의 냉정한 비교

공식 문서와 저장소를 2026-07-28 기준으로 확인했다.

| 프로젝트 | 강점 | WIGTN이 따라간 부분 | 여전히 큰 격차 |
|---|---|---|---|
| [Spec Kit](https://github.github.com/spec-kit/index.html) | Spec→Plan→Tasks→Implement, 35 integrations, 138 extensions·25 presets·workflow/bundle 생태계 | versioned artifact와 Compact/Full 계약 | task/plan 생성, extension API, 도구 범용성 |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | 30개 이상 assistant, proposal/spec/design/tasks/apply/archive와 cross-repo Store(beta) | read-only importer와 stable ID handoff | native change store, resume/edit/archive lifecycle, 외부 adopter |
| [Superpowers](https://github.com/obra/superpowers) | Codex 공식 marketplace 포함 다중 harness, RED→GREEN→REFACTOR, drill eval, 자동 plan·subagent workflow | placebo/component ablation과 회귀 fixture | 실제 실패 기반 skill TDD bank, cross-platform 재현, 방법론 전체 범위 |
| [BMAD](https://docs.bmad-method.org/) | v6의 idea→planning→agentic implementation, named agents, guided workflow, project context, Builder/modules | 얇은 project-aware 계약과 선택적 실행 | lifecycle·agent 범위, customization, ecosystem 규모 |
| [Smart Ralph](https://github.com/tzachbon/smart-ralph) | 상태·resume를 가진 지속 구현 loop와 다수 helper skill | 채택하지 않음 | 장기 작업 지속성. 대신 WIGTN은 무단 자율 실행 위험이 낮음 |
| [cc-thingz](https://github.com/alexei-led/cc-thingz) | hook 중심 자동화와 marketplace breadth | 채택하지 않음 | 자동 정책 집행. WIGTN은 hook 안전성 근거가 아직 없음 |
| [codex-spec](https://github.com/shenli/codex-spec) | 저장소 안 task context와 spec 중심 진행 상태 | Evidence Contract의 상태 handoff | task graph, resume UX, lifecycle 완결성 |

WIGTN의 상대적 강점은 범위가 아니라 다음 세 가지다.

1. 커밋·푸시·PR·배포 권한을 artifact에서 명시적으로 보존한다.
2. `verified`를 코드 존재가 아니라 실행 check와 연결한다.
3. 강한 모델의 일반 코딩을 건드리지 않는 것을 제품 요구사항으로 둔다.

반대로 수명주기·생태계·범용성은 여전히 Spec Kit/OpenSpec/BMAD보다
명백히 약하다. importer 하나를 추가했다고 “호환 생태계”가 생긴 것은
아니다. 현재 importer는 외부 artifact를 읽어 `not-verifiable` 상태로
정규화할 뿐, 원본 도구의 lifecycle을 실행하거나 되쓰지 않는다.

## Package ablation

### 프로토콜

| 항목 | 값 |
|---|---|
| 모델 | GPT-5.5, GPT-5.6 Sol |
| effort | medium |
| arm | bare, placebo4, core4, full8 |
| task | Compact PRD, ordinary JavaScript fix |
| 반복 | 모델×arm×task당 2회 |
| 성공 실행 | 32/32 |
| 격리 | arm별 `CODEX_HOME`, remote plugin/apps 비활성 |
| 권한 | read-only, approval `never` |
| scorer | PRD validator, ordinary-fix deterministic scorer |
| 비용 | CLI total tokens, final bytes, wall time를 품질과 분리 |

Placebo 4는 Core 4와 description 총문자 수가 같지만 제품·검증 지시가 없는
중립 metadata다. 이로써 “플러그인이 있다는 사실”과 WIGTN 지시 내용을
부분적으로 분리했다.

### 결과

값은 2회 중앙값이다. 표본이 작으므로 token·latency 차이에 유의성이나
일반성을 부여하지 않는다.

| 모델 | Arm | PRD 계약 | PRD bytes | PRD tokens | 일반 코딩 | 일반 tokens | 일반 시간 |
|---|---|---:|---:|---:|---:|---:|---:|
| GPT-5.5 | bare | 0/2 | 5,428.5 | 3,413.5 | 2/2 | 1,704.5 | 7.5s |
| GPT-5.5 | placebo4 | 0/2 | 5,241 | 4,074.5 | 2/2 | 2,947.5 | 7.5s |
| GPT-5.5 | core4 | 2/2 | 5,975 | 11,989.5 | 2/2 | 3,051 | 9s |
| GPT-5.5 | full8 | 2/2 | 6,440.5 | 7,634.5 | 2/2 | 1,997 | 9s |
| GPT-5.6 Sol | bare | 0/2 | 5,750 | 6,977.5 | 2/2 | 5,873.5 | 8.5s |
| GPT-5.6 Sol | placebo4 | 0/2 | 5,026 | 9,933.5 | 2/2 | 2,658.5 | 6s |
| GPT-5.6 Sol | core4 | 2/2 | 6,478.5 | 8,136 | 2/2 | 2,756 | 7.5s |
| GPT-5.6 Sol | full8 | 2/2 | 6,047 | 9,717.5 | 2/2 | 3,251 | 10s |

### 해석

- PRD 계약 효과는 같은 모델·같은 prompt에서 양 모델 모두
  `bare/placebo 0/4 → core/full 4/4`였다.
- 같은 길이 placebo가 실패했으므로 catalog 길이만으로 생긴 효과는 아니다.
- 일반 코딩은 16/16 모두 정답이고 heavy workflow 오호출이 없었다.
- GPT-5.6 일반 코딩에서 Full 8 token 중앙값은 placebo보다 약 22% 높고
  Core 4는 약 4% 높았다. Core 축소 가설과 방향은 맞지만 `n=2`다.
- GPT-5.5는 token 분산이 너무 커 같은 방향이 재현되지 않았다.
- Compact profile의 최종 PRD는 이전 full-profile smoke의 plugin 중앙값보다
  GPT-5.5에서 약 26–31%, GPT-5.6에서 약 18–23% 작았다.
- PRD 계약은 여전히 bare보다 시간과 대체로 token을 더 쓴다. “효율적”이라는
  표현은 품질 계약 대비 비용이라는 한정 없이 쓰면 안 된다.

### 채점기 감사에서 발견한 문제

초기 재집계에서 GPT-5.5 결과 두 개를 validator가 오답 처리했다.

- `ORG-INV-001`을 `FR-`로 시작하지 않는다는 이유로 거부
- Markdown code span인 `` `INV-FR-001` ``을 ID로 인식하지 못함

둘 다 안정적인 ID였으므로 모델 실패가 아니라 grader defect다. validator를
기능 요구사항/인수조건 표와 릴리스 매핑을 직접 읽도록 고치고 두 형식을
회귀 fixture로 추가했다. 이 수정은 pilot 분석 중 이뤄졌으므로 허용되지만,
confirmatory에서는 scorer hash를 먼저 고정하고 절대 수정하면 안 된다.

## 점수 재평가

| 차원 | 이전 | 현재 | 냉정한 이유 |
|---|---:|---:|---|
| plugin engineering | 6.0 | 7.5/10 | schema, resume/drift, project context, screen/release validator |
| lifecycle·범용성 | 3.0 | 5.0/10 | PRD→screen→evidence→release handoff, native plan/task store는 없음 |
| ecosystem | 2.0 | 3.0/10 | adapter 3종 fixture뿐이며 외부 consumer·contributor 없음 |
| benchmark rigor | 4.0 | 6.0/10 | hard bank, hidden outcome, Git state, frozen hashes, 공개 errata |
| publication readiness | 4.0 | 5.5/10 | sanitized 653-file packet과 mapping-free model blind; human/external 재현 없음 |
| general quality-lift evidence | 2.0 | 3.5/10 | PRD blind 강한 방향, acceptance +25%p 방향; implement lift는 없음 |

학술·벤치마크 수준은 **4.5/10**, 내부 engineering report는 **6.5/10**
정도로 보는 것이 맞다. 상세 protocol과 결과는
[Round 2 연구 보고서](RESEARCH-ROUND2-2026-07-28-KO.md)가 이 초기
재평가를 갱신한다.

이 결과는 기술 블로그나 engineering report에는 가치가 있다. “강한 모델에
무거운 harness를 덧씌우지 않고, 어디에만 계약을 넣을지 placebo ablation으로
결정했다”는 내용은 구체적이고 재현 가능하다. 반면 “WIGTN이 Codex 품질을
높인다”는 제목이면 현재도 과장이고, 냉정하게 말해 홍보 글에 가깝다.

## 제품 결정

### 지금 유지

- 핵심 4개 스킬과 선택적 Evidence Contract
- Compact/Full PRD profile
- stable ID와 profile validator
- read-only requirement importer
- Full 8의 explicit/selective invocation 원칙

### 지금 배포하지 않음

- Core/Studio marketplace 분리
- global hook
- 자동 장기 agent loop
- ordinary coding 자동 lifecycle
- “품질/효율 향상 입증” 마케팅 문구

Core/Studio 분리는 다음 조건을 만족할 때만 한다.

1. 12개 이상의 pilot task에서 Core가 핵심 outcome을 Full과 비열등하게 유지
2. ordinary task에서 Full 대비 context 비용 감소 방향이 두 모델에서 재현
3. Screen/Design/Diagram/Presentation이 빠져 생기는 발견성 손실을 측정
4. 기존 Full 사용자 migration과 설치 UX를 설계

## 다음 실험 우선순위

내부 synthetic 단계에서 Acceptance Hard 8개, Implement hidden task 4개,
Release Git-state 10개, PRD·Implement dual-model blind screen까지 완료했다.
다음 우선순위는 기능 추가가 아니라 다음 독립성 gate다.

1. 두 명의 human blind reviewer와 adjudication 전 원점수
2. 명시적 egress 승인을 받은 실제 저장소 3개 이상의 disposable holdout
3. 실제 실패 기반 Acceptance/Implement task를 각각 20–50개로 확대
4. 외부 evaluator의 fresh-machine raw packet 재현
5. 실제 Spec Kit/OpenSpec/BMAD 산출물 12개 이상의 format-drift 검증

최소 20–50개 실제 실패 task와 task당 여러 trial을 권하는
[Anthropic agent eval 지침](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents),
oracle-checkable task와 artifact/trace/usage를 함께 공개하는
[Harness-Bench](https://arxiv.org/abs/2605.27922), task와 grader 자체를
숙련자가 감사해야 한다는
[OpenAI coding-eval audit](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
수준에 맞추려면 이 다섯 묶음이 필요하다.

그 전까지 최종 제품 문구는 다음이 가장 정확하다.

> WIGTN for Codex는 일반 코딩을 대체하는 agent framework가 아니다.
> PRD, 요구사항 증거, 명시적 구현 전달, Git 릴리스처럼 결과 형태와 권한이
> 중요한 순간에만 검증 가능한 계약을 추가한다. 테스트 PRD에서 계약
> 일관성은 개선됐지만, 일반 구현 품질과 효율 향상은 아직 검증 중이다.
