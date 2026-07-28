# WIGTN for Codex v0.3 후보 — 선택적 하네스 연구 보고서

> 2026-07-28 · GPT-5.5 / GPT-5.6 Sol · Opus 비교 제외 · 배포 전 후보

## 초록

이 연구는 “플러그인을 설치하면 코딩을 더 잘한다”가 아니라 다음 질문을
검증한다.

> 강한 기본 모델의 일반 구현 능력은 방해하지 않으면서, PRD 형태,
> acceptance 판정, Git 권한처럼 결과 계약이 중요한 순간에만 얇은
> 하네스가 오류와 변동을 줄일 수 있는가?

현재 결과는 부분적으로 그렇다.

- 같은 GPT-5.6 Sol에서 Acceptance Verifier는 어려운 16개 판정의 정확한
  canonical status를 `10/16 → 14/16`으로 올렸다. paired exact
  McNemar p값은 `0.125`여서 확증적 효과라고 부르기에는 작다.
- Compact PRD 계약은 GPT-5.5와 GPT-5.6 Sol 모두
  `bare/placebo 0/4 → Core/Full 4/4`로 재현됐다. 이는 WIGTN 계약
  일관성이다. mapping-free dual-model blind screen에서는 Core가
  bare보다 평균 `+22.5/100`이었지만 human preference는 아직 아니다.
- Implement hidden outcome은 네 arm 모두 `4/4`였다. GPT-5.6
  Verified Delivery는 bare보다 token이 약 34% 많았고 deterministic
  correctness 향상은 없었다.
- Release Readiness는 GPT-5.6에서 `9/10 → 10/10`이었다. 단 한 건의
  차이이고 통계적으로 확증적이지 않지만, 실패가 “모호한 완료 요청에서
  commit”이라는 zero-tolerance 권한 위반이었다는 점은 제품적으로 중요하다.

따라서 v0.3의 적절한 포지셔닝은 “모델 성능 부스터”가 아니다.

> **PRD·화면 명세·요구사항 증거·릴리스 권한을 명시적으로 만들되,
> ordinary coding에는 개입하지 않는 Codex 전용 선택적 계약 계층**

## 연구 질문과 사전 판정 기준

| ID | 질문 | 1차 지표 | 통과 의미 |
|---|---|---|---|
| RQ-1 | PRD 계약이 catalog 길이가 아니라 내용 때문에 생기는가 | Compact validator | Core/Full이 bare와 길이-matched placebo보다 우수 |
| RQ-2 | Acceptance Verifier가 증거 상태를 더 일관되게 분류하는가 | exact canonical status, false `verified` | 같은 모델 paired 개선 |
| RQ-3 | Verified Delivery가 구현 정답률을 높이는가 | visible·hidden pass@1, 보존 | bare보다 outcome 개선 |
| RQ-4 | Release Readiness가 권한 위반을 막는가 | intended action, unauthorized mutation | 정상 동작 비열등 + 위반 감소 |
| RQ-5 | 하네스가 일반 코딩을 방해하는가 | ordinary outcome, token, latency, 오호출 | outcome 비열등, 비용 별도 보고 |

GPT-5.5+플러그인과 GPT-5.6 bare 비교는 호환성 관찰일 뿐 causal estimate로
쓰지 않는다. 플러그인 효과는 GPT-5.6 bare와 GPT-5.6 treatment만 비교한다.

## 시스템 설계

v0.3 후보는 여덟 스킬을 항상 실행하는 agent framework가 아니다. 핵심
네 스킬 사이에서만 선택적 Evidence Contract를 이어 준다.

```text
product-spec
  └─ stable requirement IDs / Compact·Full profile
      └─ verified-delivery (명시 호출 전용)
          └─ code + executed check evidence
              └─ acceptance-verifier (기본 read-only)
                  └─ canonical status
                      └─ release-readiness
                          └─ 사용자 문장 그대로의 Git authority
```

일반 코딩은 이 흐름으로 자동 승격되지 않는다. `.wigtn/project.json`과
`.wigtn/evidence.json`도 명시적 저장·handoff가 있을 때만 사용한다.

이번 개혁에서 추가한 실행 가능한 primitive는 다음과 같다.

| Primitive | 역할 |
|---|---|
| Evidence Contract schema/validator | 거짓 `verified`, check/status 불일치, 권한 초과, 비이식 경로 차단 |
| requirement importer + resume | WIGTN/Spec Kit/OpenSpec/BMAD Markdown 정규화, 변경 없는 evidence 보존, spec drift 무효화 |
| evidence inspector | source hash drift, 사라진 코드 경로·라인, authority 상태 확인 |
| optional project context | requirement source, 검증 명령, 보호 경로, PRD profile 공유 |
| Screen Contract validator | 5종 산출물, wireframe anchor, FR handoff drift 검증 |
| release-state inspector | branch/upstream/operation/conflict/staged/unstaged/untracked를 mutation 없이 JSON화 |
| eval packet exporter | home/work 제외, 경로·secret redaction, 파일 membership와 SHA-256 무결성 |

## 실험 설계

### 공통 통제

- Codex CLI `0.146.0-alpha.3.1`
- model reasoning effort `medium`
- arm별 격리된 `CODEX_HOME`
- remote plugin과 apps 비활성
- 동일 task·prompt·권한·runtime에서 같은 모델 비교
- task, runner, scorer, plugin, schema hash를 호출 전에 기록
- 결과 문장보다 저장소, Git, test exit, artifact schema를 우선 채점
- quality와 token·latency를 합성 점수로 섞지 않음

### 주 분석에 포함한 실행

| Suite | Task/arm | Model call | 지위 |
|---|---:|---:|---|
| Package ablation | 2 task × 4 arm × 2 model × 2 trial | 32 | pilot |
| Acceptance Hard v7 | 8 task × 3 arm × 2 trial | 48 | confirmatory candidate |
| Implement recheck | 4 task × 4 arm | 16 | current-candidate regression |
| Release recheck | 10 task × 3 arm | 30 | current-candidate regression |
| PRD blind screen | 4 panel × 2 judge | 8 | model-judge screening |
| Implement blind-v2 | 4 panel × 2 judge | 8 | model-judge screening |

모델 판정 blind screen은 deterministic outcome과 분리한다. 사람 두 명의
독립 blind review가 제출되기 전에는 publication-grade human result로
간주하지 않는다.

### 재현 패킷

주 분석 여섯 run root를 `scripts/export-eval-packet.py`로 내보내고
`scripts/verify-eval-packet.py`로 재검증했다.

- local packet: `/tmp/wigtn-v03-eval-packet-final`
- source: 6개
- manifest file: 653개
- manifest content bytes: 5,088,984
- `PACKET-MANIFEST.json` SHA-256:
  `d81ee21e27919bfcaec4d312b5aba01ee5cb07b8c02fa7afde7123a8ecb54247`
- home/cache/work/prompt-input leak: 0

패킷은 run root와 사용자 홈을 치환하고 token-like secret을 redaction하며,
모든 허용 파일의 path·size·SHA-256을 기록한다. 현재 `/tmp` 산출물이므로
논문·블로그 공개 시 release asset이나 별도 artifact storage에 그대로
보존해야 한다. 저장소 문서만 공개하고 raw packet을 잃으면 publication
readiness 점수는 다시 내려간다.

### 제외·정정 이력

실패한 연구 설계를 숨기지 않았다.

- Acceptance v1은 직렬 실행 비용 때문에 중단했다.
- v2는 `code-only`, `stale-test` gold label 결함을 발견해 중단했다.
- v3는 scorer가 지원하지 않는 validator option을 사용해 전부 invalid로
  만들 수 있어 중단했다.
- v4는 common prompt에 treatment 핵심 규칙을 누설해 중단했다.
- v5 48회 뒤 evidence-level audit에서 tenant·external·flaky oracle 결함을
  발견했다. 탐색 자료로만 남기고 aggregate claim에서 제외했다.
- v6는 endpoint DNS 실패로 모델 출력을 하나도 얻지 못해 infra failure로
  제외했다.
- v7은 수정한 oracle과 treatment를 hash로 동결한 뒤 다시 실행했다.
- 최초 delivery blind는 후보 매핑 파일이 judge-visible tree에 있었다.
  실제 접근 흔적은 없지만 완전 blind라 부르지 않고 재평가 대상으로 내렸다.

상세 내역은
`tests/behavior/acceptance-hard-errata.md`와
`tests/behavior/delivery-blind-errata.md`에 있다.

## 결과

### 1. Package ablation: PRD 계약은 내용 효과다

| Model | Arm | PRD 계약 | ordinary coding |
|---|---|---:|---:|
| GPT-5.5 | bare | 0/2 | 2/2 |
| GPT-5.5 | placebo4 | 0/2 | 2/2 |
| GPT-5.5 | core4 | 2/2 | 2/2 |
| GPT-5.5 | full8 | 2/2 | 2/2 |
| GPT-5.6 Sol | bare | 0/2 | 2/2 |
| GPT-5.6 Sol | placebo4 | 0/2 | 2/2 |
| GPT-5.6 Sol | core4 | 2/2 | 2/2 |
| GPT-5.6 Sol | full8 | 2/2 | 2/2 |

Core 4와 description 총길이가 같은 placebo4가 실패했으므로 단순 catalog
길이만으로 생긴 결과는 아니다. 반면 이 validator는 WIGTN 계약과 정렬돼
있다.

파일시스템에 후보 매핑을 만들지 않은 PRD blind screen 결과는 다음과 같다.

| Arm | model-judge quality /100 | completeness | implementability | decision hygiene | traceability | concision | omissions | fabrications |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 68.8 | 3.88 | 3.25 | 1.50 | 3.00 | 2.12 | 6 | 40 |
| placebo4 | 73.8 | 3.62 | 3.12 | 1.50 | 3.38 | 3.12 | 8 | 44 |
| core4 | 91.2 | 3.75 | 3.38 | 3.75 | 3.88 | 3.50 | 8 | 4 |
| full8 | 96.2 | 4.00 | 3.88 | 3.62 | 4.00 | 3.75 | 2 | 5 |

Core 4는 bare보다 평균 `+22.5`, Full 8은 `+27.5`점이었고 각각 8/8
paired judge-panel에서 이겼다. 두 judge는 top candidate를 4/4 panel에서
같게 골랐고 pairwise 순서도 21/24가 일치했다.

이 결과는 validator 모양만 맞췄다는 반론을 약화하지만 제거하지는 못한다.
두 judge 모두 Codex 모델이고 사람 reviewer가 아니며, 후보의 구조만 보고
WIGTN 형식을 추론했을 가능성도 있다. 따라서 **재현 가능한 model-judge
screening**으로 보고, independent human preference라고 부르지 않는다.

ordinary coding은 16/16 모두 정답이고 heavy workflow 오호출이 없었다.
따라서 현재 task에서 “설치만으로 일반 코딩이 망가졌다”는 증거는 없다.
그러나 token 분산이 크고 trial이 둘뿐이라 효율 개선 주장도 금지한다.

### 2. Acceptance Hard v7: 상태 일관성은 개선, 확증은 아직

| Arm | exact status | false verified | valid artifact | 보존 | no commit | token 중앙값 | 시간 중앙값 |
|---|---:|---:|---:|---:|---:|---:|---:|
| GPT-5.6 bare | 10/16 | 0 | 16/16 | 16/16 | 16/16 | 31,738.5 | 133.5s |
| GPT-5.6 + verifier | 14/16 | 0 | 16/16 | 16/16 | 16/16 | 33,831.5 | 125.0s |
| GPT-5.5 + verifier | 14/16 | 0 | 16/16 | 16/16 | 16/16 | 33,508.0 | 110.0s |

GPT-5.6 paired comparison은 bare만 맞은 사례 0, plugin만 맞은 사례 4였다.
정확도 차이는 `+25%p`, exact McNemar p=`0.125`다. 방향은 좋지만 n=16에서
유의성을 확보하지 못했다.

차이는 flaky check 두 건, stale test 한 건, external precursor 한 건에서
생겼다. 플러그인은 특히 “flaky suite는 증거가 아니지만 독립적인 안정
runtime assertion은 작은 observable requirement를 검증할 수 있다”는
구분을 더 일관되게 적용했다.

하지만 false `verified`는 bare도 0건이었다. 따라서 이 suite가 지지하는
문장은 “거짓 승인을 줄였다”가 아니라 **세밀한 상태 분류 일관성이
향상되는 방향을 보였다**이다.

GPT-5.6 treatment의 token 중앙값은 bare보다 약 6.6% 높고 시간 중앙값은
약 6.4% 낮다. 표본과 분산 때문에 어느 쪽도 효율 효과로 일반화하지 않는다.

### 3. Implement: correctness lift는 없고 비용은 늘었다

| Arm | visible | hidden | perfect | test tamper | draft loss | unintended commit | scope violation | tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GPT-5.6 bare | 4/4 | 4/4 | 4/4 | 0 | 0 | 0 | 0 | 26,240 |
| GPT-5.6 ordinary plugin | 4/4 | 4/4 | 4/4 | 0 | 0 | 0 | 0 | 29,586 |
| GPT-5.6 verified-delivery | 4/4 | 4/4 | 4/4 | 0 | 0 | 0 | 0 | 35,050 |
| GPT-5.5 verified-delivery | 4/4 | 4/4 | 4/4 | 0 | 0 | 0 | 0 | 31,560 |

모든 arm이 hidden test까지 통과했다. Verified Delivery는 GPT-5.6 bare보다
token이 약 33.6% 많았다. 이 결과에서 Verified Delivery를 “코드를 더 잘
짜는 모드”라고 부르는 것은 틀리다.

현재 유지 이유는 correctness lift가 아니라 명시적 requirement→code→check
handoff, final diff audit, 중요한 작업의 추적성이다. 이 가치가 비용을
정당화하는지는 더 어려운 구현 task와 실제 저장소에서 다시 검증해야 한다.

매핑 파일을 judge-visible tree에서 제거한 blind-v2도 같은 결론이다.

| Arm | model-judge quality /100 | bare 대비 | win/tie/loss |
|---|---:|---:|---:|
| GPT-5.6 bare | 95.6 | 기준 | - |
| GPT-5.6 ordinary plugin | 91.2 | -4.4 | 1/4/3 |
| GPT-5.6 verified-delivery | 95.0 | -0.6 | 2/3/3 |
| GPT-5.5 verified-delivery | 85.0 | -10.6 | 0/2/6 |

두 judge의 top candidate 일치는 1/4 task, pairwise 순서 일치는
17/24였다. GPT-5.6 Verified Delivery와 bare의 차이는 사실상 동률이며
judge agreement도 낮다. deterministic hidden outcome 4/4 동률과 함께
보면 구현 품질 향상 주장은 지지되지 않는다.

### 4. Release: 작은 표본의 안전 신호

| Arm | perfect | intended action | zero-tolerance violation | tokens | 시간 |
|---|---:|---:|---:|---:|---:|
| GPT-5.6 bare | 9/10 | 9/10 | 1 | 12,745 | 24s |
| GPT-5.6 + release-readiness | 10/10 | 10/10 | 0 | 17,884 | 46s |
| GPT-5.5 + release-readiness | 10/10 | 10/10 | 0 | 10,620 | 38s |

유일한 GPT-5.6 bare 실패는 `vague-complete` 요청에서 commit한 사례였다.
플러그인은 중단했다. 1건 차이라 일반화할 수 없고 비용은 증가했다.
그럼에도 commit/push/PR 권한 위반은 평균 품질점수로 상쇄할 수 없는
zero-tolerance 사건이므로 Release Readiness와 명시적 authority mapping은
유지한다.

## 기능별 판정과 제품 결정

| 기능 | 현재 근거 | 판정 | 수정·운영 방향 |
|---|---|---|---|
| Product Spec | contract `0/4 → 4/4`, model blind Core +22.5 | 유지 | Compact 기본, human blind로 과잉 문서·fabrication 재검증 |
| PRD Review | 정적 review contract, 독립 outcome 없음 | beta | omission·fabrication·결정 시간 blind bank 추가 |
| Screen Spec | 5종 template + 새 cross-artifact validator | 유지 | 실제 screen bundle task와 시각 QA benchmark 필요 |
| Acceptance Verifier | GPT-5.6 `10/16 → 14/16`, p=.125 | 가장 유망 | atomic subclaim과 relevance/flaky/external 규칙 유지, task 확대 |
| Verified Delivery | hidden outcome 동률, token +33.6% | explicit beta | 일반 구현 자동 호출 금지, traceability 가치 별도 측정 |
| Release Readiness / Auto Commit | 9/10 → 10/10, 권한 위반 1→0 | 유지 | release-state inspector 사용, 더 많은 dirty/conflict task 필요 |
| Design Direction | project-first 지시, behavior evidence 없음 | 보조 기능 | 디자인 시스템이 있을 때만 호출, 제품 핵심 주장서 제외 |
| Diagram / Presentation | render·visual QA 계약, behavior evidence 없음 | 독립 도구 | core efficacy 주장과 분리 |

## 경쟁 제품과의 위치

2026-07-28 공식 자료 기준으로 WIGTN은 범위 경쟁에서 이기지 못한다.

- [Spec Kit](https://github.github.com/spec-kit/index.html)은
  Spec→Plan→Tasks→Implement, 35 integrations, 138 extensions, 25 presets와
  workflow/bundle 생태계를 제공한다.
- [OpenSpec](https://github.com/Fission-AI/OpenSpec)은 30개 이상 assistant,
  proposal/spec/design/tasks/apply/archive lifecycle과 cross-repo Store
  beta를 제공한다.
- [Superpowers](https://github.com/obra/superpowers)는 Codex 공식
  marketplace를 포함한 다중 harness, RED→GREEN→REFACTOR, drill eval,
  자동 plan·subagent 방법론을 제공한다.
- [BMAD](https://docs.bmad-method.org/) v6는 아이디어에서 agentic
  implementation까지 named agents, guided workflow, project context,
  Builder와 modules를 제공한다.

WIGTN이 좁힌 격차는 versioned artifact, resume/drift, project context,
cross-artifact validation이다. 여전히 plan/task native lifecycle,
extension API, cross-platform validation, 외부 adopter와 contributor가
없다.

따라서 경쟁 전략은 기능 수 복제가 아니다. **Codex에 맞춘 얇은 선택성,
검증 가능한 evidence, Git authority preservation**을 더 강하게 만드는
것이 맞다.

## 냉정한 점수

| 차원 | 이전 | 현재 후보 | 근거 |
|---|---:|---:|---|
| plugin engineering | 6.5 | 7.5/10 | schema, resume/drift, project context, screen/release validators |
| lifecycle·범용성 | 3.5 | 5.0/10 | PRD→screen→evidence→release handoff, native plan/task store는 없음 |
| ecosystem | 2.5 | 3.0/10 | importer 3종과 fixtures뿐, 외부 consumer·contributor 없음 |
| benchmark rigor | 4.5 | 6.0/10 | hard bank, hidden outcome, Git state, hashes, errata, paired arm |
| publication readiness | 4.0 | 5.5/10 | sanitized packet, blind model screen, protocol; human/external replication 미완 |
| general quality-lift evidence | 2.0 | 3.5/10 | acceptance +25%p 방향, implement lift 없음, n 작음 |

“각 항목을 2~3점 올린다”는 목표는 제품 코드를 더 쓴다고 달성되지 않는다.
특히 ecosystem과 general quality evidence를 그만큼 올리려면 외부 사용자,
독립 reviewer, 실제 저장소 holdout이 필요하다. 지금 숫자를 더 높이면
평가가 아니라 자기채점이 된다.

학술·벤치마크 수준은 **4.5/10**, 재현 가능한 내부 engineering report
수준은 **6.5/10**으로 보는 것이 맞다. 기술 블로그·설계 보고서로는 충분히
가치가 있지만 “WIGTN이 GPT-5.6의 일반 코딩 품질을 향상시킨다”는 논문형
주장은 아직 방어할 수 없다.

## 허용되는 제품 문구

사용 가능:

> WIGTN for Codex는 일반 코딩을 대체하지 않는다. PRD, 화면 명세,
> acceptance evidence, Git release처럼 결과 형태와 권한이 중요한 순간에
> 선택적 계약을 추가한다. 테스트 fixture에서 PRD 계약 일관성과 acceptance
> 상태 분류가 개선되는 방향을 보였고, ordinary implementation correctness
> 향상은 아직 입증되지 않았다.

사용 금지:

- “플러그인을 쓰면 GPT-5.6 코딩 품질이 올라간다”
- “Verified Delivery가 hidden-test 성능을 높인다”
- “token-efficient하다”
- “모든 실제 저장소에서 재현된다”
- “학술적으로 유의한 성능 향상을 입증했다”

## 남은 publication gate

1. 두 명의 독립 사람이 PRD와 implementation blind packet을 평가하고
   원점수·불일치·adjudication을 공개한다.
2. 사용자 지정 실제 저장소 3개 이상에서 외부 전송을 명시 승인받아
   disposable copy holdout을 실행한다.
3. Acceptance Hard를 최소 30–50개 실제 실패 기반 task로 확대하고
   task당 3회 이상 반복한다.
4. Verified Delivery는 bare pass rate가 20–70%인 더 어려운 hidden task로
   다시 평가한다. 계속 동률이면 더 얇게 만들거나 core 주장에서 뺀다.
5. 외부 evaluator가 fresh machine에서 raw packet과 hash로 재실행한다.
6. 외부 도구 하나가 Evidence Contract를 실제 소비하거나 contributor가
   adapter/task를 추가해야 ecosystem 점수를 올린다.

`wigtn-game`과 `wigtn-introduce` disposable copy를 이용한 12-call pilot은
runner와 scorer까지 준비됐지만, 해당 저장소 내용을 모델 서비스로 보내는
명시적 egress 승인이 없어 실행하지 않았다. 이것을 우회 실행하는 것은
연구 품질을 높이는 행동이 아니라 권한 경계를 깨는 행동이다.
