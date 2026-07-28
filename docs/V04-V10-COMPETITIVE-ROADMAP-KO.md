# WIGTN for Codex v0.4 → v1.0 경쟁력 고도화 계획

> 목표: “스킬 모음”을 넘어 Codex 전용 선택적 lifecycle harness로 발전
>
> 원칙: 점수는 구현량이 아니라 사전 정의한 제품·평가 gate를 통과할 때만
> 올린다.

## 1. 최종 목표

WIGTN은 Spec Kit, OpenSpec, Superpowers, BMAD를 기능 수로 복제하지 않는다.
대신 다음 세 축에서 경쟁 가능한 제품을 만든다.

1. **Codex-native lifecycle**: PRD→화면→plan→task→implementation→evidence→release가
   stable ID와 source hash로 연결되고 중단 후 안전하게 resume된다.
2. **Selective harness**: ordinary coding에는 개입하지 않고, 사용자가 고른
   workflow에서만 상태·검증·권한 계약이 활성화된다.
3. **Evidence-first benchmark**: 모델 답변이 아니라 workspace·Git·test·artifact
   최종 상태와 비용을 공개된 task bank로 평가한다.

v1.0의 제품 문구는 아래 수준까지 올리는 것이 목표다.

> WIGTN for Codex는 제품 요구사항에서 안전한 릴리스까지 이어지는
> versioned WorkGraph와 실행 증거를 제공한다. 일반 코딩 성능은 유지하면서
> PRD 결정 품질, acceptance 상태 일관성, lifecycle 복구 가능성, Git 권한
> 보존을 재현 가능한 benchmark에서 개선한다.

## 2. 경쟁작에서 반드시 따라잡을 부분

| 경쟁작 | 현재 구조적 우위 | WIGTN 대응 |
|---|---|---|
| [Spec Kit](https://github.github.com/spec-kit/index.html) | Spec→Plan→Tasks→Implement, workflow·extension·bundle, provenance | WorkGraph, adapter SDK, workflow pack, 설치 provenance |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | change store, propose/apply/archive, artifact resume와 cross-repo store | ChangeSet, drift propagation, archive, multi-root read-only source |
| [Superpowers](https://github.com/obra/superpowers) | 모든 skill을 RED→GREEN→REFACTOR와 drill eval로 개발 | skill별 capability bank·holdout·baseline failure 의무화 |
| [BMAD](https://docs.bmad-method.org/) | project context, adaptive workflow, named agent·module ecosystem | project profile, risk-adaptive gates, extension contract |

경쟁하지 않을 부분:

- 전역 hook으로 모든 coding request를 가로채기
- 기본 다중-agent fan-out
- 무제한 autonomous loop
- 사용자 요청 없는 commit·push·PR·deploy
- Codex 외 플랫폼 수를 마케팅 숫자로 늘리기

이 다섯 가지는 WIGTN의 선택성과 권한 안전성을 약화한다.

## 3. 목표 아키텍처

### 3.1 세 개의 versioned contract

```text
.wigtn/
├── project.json          # 프로젝트 규칙·source·profile
├── workgraph.json        # requirement→artifact→task→gate 의존성
├── evidence.json         # code·check·status·release authority
├── adapters.lock.json    # adapter 버전·provenance
└── runs/
    └── <run-id>/
        ├── manifest.json
        ├── events.ndjson
        └── summary.json
```

각 파일은 JSON Schema, strict validator, migration fixture를 가진다.
상태를 하나의 거대 파일에 중복 저장하지 않는다.

- `project.json`: 저장소에 장기적으로 유효한 설정
- `workgraph.json`: 계획과 작업 의존성
- `evidence.json`: 실제 관찰된 구현·검사·권한

`workgraph.json`은 requirement 본문을 복제하지 않고 source path·hash와
stable ID를 참조한다. `verified`는 계속 `evidence.json`의 실행 결과만
부여할 수 있다.

### 3.2 WorkGraph 1.0

필수 node:

- requirement
- product/screen artifact
- implementation task
- executable check
- release gate

task 필드:

- stable task ID
- linked requirement IDs
- dependency IDs
- intended paths와 protected paths
- risk class
- expected checks
- status
- blocker와 evidence reference

허용 transition:

```text
draft → ready → in-progress → implemented → verified
                     └──────→ blocked
```

- dependency가 충족되지 않으면 `ready`가 될 수 없다.
- passing evidence 없이는 `verified`가 될 수 없다.
- source hash가 바뀌면 연결 task와 evidence를 `stale`로 내린다.
- graph 변경과 release authority는 서로 분리한다.

### 3.3 Codex-native CLI

외부 daemon이나 프레임워크 대신 dependency-free Python CLI부터 만든다.

```text
wigtn init
wigtn import <artifact>
wigtn plan
wigtn status [--json]
wigtn next
wigtn diff
wigtn verify
wigtn doctor
wigtn archive
wigtn pack
```

요구사항:

- 모든 명령은 `--json` 제공
- read-only 명령과 mutation 명령 구분
- mutation은 dry-run plan을 먼저 출력
- idempotent 실행
- schema migration과 rollback 가능한 backup
- macOS/Linux/Windows CI
- network 없이 core lifecycle 동작

### 3.4 스킬 개혁

| 스킬 | v1 역할 | 과감한 결정 |
|---|---|---|
| `product-spec` | Compact/Full PRD + WorkGraph requirement source | model blind 강점 유지, unsupported policy 자동 분리 |
| `product-spec` Review mode | spec contradiction·omission·decision audit | create와 별도 capability bank 운영 |
| `screen-spec` | 화면 5종 + graph artifact mapping | validator 통과 전 handoff 금지 |
| 신규 `work-planner` | requirement를 dependency-aware task graph로 변환 | plan/task gap을 직접 메움 |
| `verified-delivery` | 명시된 task node 하나 또는 작은 batch만 구현 | 전체 프로젝트 자동 구현 모드 폐기 |
| `acceptance-verifier` | atomic subclaim과 executed evidence로 graph gate 갱신 | 가장 강한 핵심 moat로 투자 |
| `release-readiness` | graph gate·Git state·사용자 authority 교집합만 실행 | unauthorized action은 영구 zero-tolerance |
| design/diagram/presentation | 독립 Studio 기능 | core efficacy와 benchmark에서 분리 |

`work-planner` 하나만 신규 skill로 추가한다. status·doctor·archive는 CLI가
담당해 catalog context tax를 늘리지 않는다.

### 3.5 Project profile

플러그인을 쪼개기 전에 한 package 안에서 profile을 제공한다.

| Profile | 활성 lifecycle |
|---|---|
| `lite` | 현재 PRD/evidence/release 계약 |
| `flow` | WorkGraph, resume, change propagation |
| `studio` | flow + screen/design/diagram/presentation |

profile은 skill을 강제 실행하지 않는다. 기본값은 `lite`, 저장소가 명시한
경우에만 `flow` 또는 `studio`다.

Core/Studio 별도 marketplace 분리는 100-task benchmark에서 catalog
overhead가 15% 이상이고 outcome 손실이 없을 때만 한다.

## 4. 범용성과 ecosystem을 올리는 방법

### 4.1 Adapter SDK 1.0

built-in adapter:

- WIGTN Markdown
- Spec Kit
- OpenSpec
- BMAD
- generic Markdown/JSON

adapter manifest:

- name·version
- input/output schema
- capability: read, create, update, archive
- supported fields
- loss policy
- network requirement
- mutation authority

기본은 read-only다. 외부 artifact write-back은 사용자 명시 요청과 dry-run
diff가 있어야 한다.

검증 gate:

- stable ID round-trip loss 0
- 지원 필드 round-trip loss 0
- 미지원 필드는 삭제하지 않고 diagnostic으로 노출
- 12개 이상 실제 upstream artifact fixture
- upstream format change를 nightly contract test로 탐지

### 4.2 Workflow pack

Spec Kit bundle을 복제하지 않고 WIGTN contract pack을 만든다.

```text
pack.json
schemas/
templates/
policies/
evals/
```

초기 공식 pack:

1. SaaS authorization/tenancy
2. API state machine/idempotency
3. Frontend screen lifecycle
4. Safe Git release

pack은 실행 코드를 임의로 주입하지 않는다. schema·template·policy·eval
fixture만 제공한다. install/update/remove provenance와 version pin을
기록한다.

### 4.3 Contributor program

- `eval-task.schema.json`
- reference solution과 solvability proof 의무
- grader test와 fault-injection fixture 의무
- adapter conformance kit
- clean-install reproduction workflow
- monthly benchmark snapshot

ecosystem 점수는 외부 contributor 또는 consumer가 생기기 전까지 5점 이상
부여하지 않는다.

## 5. Benchmark 6 → 8 프로그램

### 5.1 task corpus

최종 목표는 100개 이상의 oracle-checkable task다.

| Suite | Task | 핵심 endpoint |
|---|---:|---|
| PRD Create | 15 | omission, fabricated policy, implementation decision time |
| PRD Review | 10 | material defect recall/precision |
| Screen Spec | 10 | cross-artifact consistency, usable flow |
| WorkGraph lifecycle | 15 | plan correctness, resume, drift, stale propagation |
| Acceptance | 20 | exact status, verified precision, evidence relevance |
| Implement | 15 | hidden pass@1, regression, scope, cost |
| Release | 10 | intended action, unauthorized mutation, recoverability |
| Security/adversarial | 10 | secret, symlink, prompt injection, authority bypass |

일부 task는 여러 suite endpoint를 가진다. unique task는 최소 100개를
유지한다.

source 분포:

- 실제 사용자 실패 30% 이상
- 공개 OSS issue를 감사·재작성한 task 30% 이상
- adversarial synthetic 20% 이하
- lifecycle/interop fixture 20% 내외

### 5.2 dataset split

- development: 40%
- locked holdout: 40%
- external replication: 20%

plugin author는 holdout reference solution과 grader output을 보지 않는다.
task author, plugin author, human reviewer 역할을 분리한다.

task 포함 조건:

1. 두 도메인 전문가가 같은 pass/fail에 동의
2. reference solution이 모든 grader 통과
3. fault patch가 예상 grader에서 실패
4. task description이 grader가 요구하는 사실을 모두 명시
5. clean sandbox에서 세 번 재현

### 5.3 실험 arm

필수 causal arm:

- GPT-5.6 bare
- GPT-5.6 WIGTN treatment

호환성 arm:

- GPT-5.5 WIGTN
- 다음 stable Codex 모델 WIGTN

component ablation:

- placebo metadata
- Evidence Contract only
- skill only
- WorkGraph + skill
- full plugin

모든 arm은 같은 model·effort·timeout·tool·repository snapshot·권한을 쓴다.

### 5.4 반복과 통계

개발 loop:

- task당 1 trial
- 실패군 탐색용
- publication claim 금지

confirmatory:

- task당 최소 3 trials
- pass@1과 pass^3 둘 다 보고
- task-clustered bootstrap 95% CI
- binary paired endpoint는 exact McNemar
- continuous endpoint는 paired bootstrap
- 다중 비교는 Holm correction
- timeout·infra·excluded run을 전부 공개

사전 효과 gate:

| 기능 | 승격 기준 |
|---|---|
| PRD | human pairwise preference ≥65%, decision time 15% 이상 단축 또는 omission 20% 이상 감소 |
| Acceptance | exact status +10%p 이상, 95% CI lower bound >0, verified precision ≥99% |
| Implement | hidden pass@1 +5%p 또는 실패율 20% 상대 감소; 아니면 품질 claim 제거 |
| Release | intended success ≥98%, unauthorized mutation 0/300, unrelated inclusion 0/300 |
| Ordinary coding | correctness non-inferiority margin -2%p, median token overhead ≤10% |
| WorkGraph | resume success ≥95%, stale propagation·ID 보존 100% |
| Adapter | supported-field round-trip loss 0, format-drift detection 100% |

### 5.5 human calibration

- 주관적 PRD·review·screen 평가는 3명 blind reviewer
- 후보 생성 arm과 mapping을 filesystem에서 제거
- adjudication 전 원점수 보존
- Krippendorff’s alpha ≥0.67을 최소 publication gate로 사용
- model judge는 human agreement가 확인된 rubric에서만 보조 scorer로 사용
- reviewer가 task author인 sample은 별도 표시

### 5.6 외부 재현

최소 조건:

- 12개 repository shape
- Python, TypeScript, Go, Rust 중 3개 이상
- macOS/Linux/Windows
- plugin author가 아닌 evaluator 2명
- fresh install과 pinned artifact
- raw trace·patch·state·validator·usage 공개
- private repo는 명시적 egress approval 없이는 사용 금지

## 6. 안전성 연구

[HarnessAudit-Bench](https://arxiv.org/abs/2605.14271)의 문제의식을 반영해
다음 task를 별도 safety suite로 만든다.

- prompt/AGENTS injection으로 commit 권한 탈취
- symlink를 통한 protected-path 우회
- untracked secret 포함
- malicious test가 외부 전송 시도
- stale evidence 재사용
- 다른 branch/commit의 evidence 주입
- adapter path traversal
- pack provenance 변조
- detached HEAD·rebase·conflict에서 잘못된 release
- “완료해줘”를 commit으로 확대 해석

권한 위반은 평균점수로 상쇄하지 않는다. 한 건이라도 발생하면 release
candidate를 차단하고 root-cause fixture를 regression bank에 추가한다.

## 7. Publication 5.5 → 8 프로그램

publication artifact:

1. protocol과 hypothesis
2. task datasheet와 license
3. model/CLI/plugin/scorer hash
4. raw sanitized packet
5. complete exclusion·errata ledger
6. statistical notebook 또는 dependency-free summarizer
7. human raw ratings와 agreement
8. external replication report
9. limitations와 forbidden claims
10. machine-readable result table

공개 순서:

- GitHub release asset에 immutable packet
- Zenodo/OSF DOI
- methods report
- 결과를 재생성하는 one-command script
- 독립 reviewer reproduction
- 이후 기술 블로그

블로그를 먼저 쓰고 benchmark를 나중에 맞추지 않는다.

## 8. 단계별 실행 계획

### Gate 0 — v0.3 baseline 동결

- 현재 plugin·runner·scorer commit
- 653-file packet을 영구 storage에 보존
- v0.3 claim boundary를 release note에 고정
- 이후 task는 development/holdout 표시

통과 조건: clean install에서 현재 full validation과 주요 result 재생성.

### Gate 1 — v0.4 WorkGraph foundation

- WorkGraph schema/validator/migration
- `wigtn init/import/plan/status/next/diff/doctor`
- product-spec/screen-spec/evidence ID 연결
- resume·source drift·stale propagation
- 30개 deterministic contract fixture

목표 점수:

- lifecycle 5.0 → 6.5
- plugin engineering 7.5 → 8.0

### Gate 2 — v0.5 Task execution and change lifecycle

- 신규 `work-planner`
- verified-delivery 단일 task/batch 실행
- change impact·archive
- release gate와 authority 교집합
- macOS/Linux/Windows CI
- 6개 disposable repository

목표 점수:

- lifecycle 6.5 → 7.5
- 범용성 5.0 → 7.0

### Gate 3 — v0.6 Adapter/pack ecosystem

- Adapter SDK와 conformance kit
- built-in adapter 4종
- official pack 4종
- provenance·version pin·update/remove
- 외부 contributor용 task/adapter schema

목표 점수:

- ecosystem 3.0 → 5.0
- lifecycle 7.5 → 8.0

외부 contributor/consumer가 없으면 ecosystem은 4.5에서 동결한다.

### Gate 4 — v0.7 Capability hill-climb

- 40-task development bank
- skill별 RED baseline
- 최소 treatment로 GREEN
- regression과 capability bank 분리
- cost budget enforcement

kill criteria:

- Verified Delivery가 60개 hidden task에서 +5%p를 못 내면 quality feature
  포지셔닝을 제거하고 evidence-only workflow로 축소
- Full PRD가 human preference 65%를 못 넘으면 Compact를 기본·Full을 opt-in
- Core/Full split이 15% context 절감과 outcome 비열등을 동시에 못 내면 보류

### Gate 5 — v0.8 100-task confirmatory

- locked 100-task corpus
- 3 trials
- causal·compatibility·component arm
- 3 human reviewers
- 12 repositories
- 3 OS
- sanitized public packet

목표 점수:

- benchmark rigor 6.0 → 8.0
- general quality evidence 3.5 → 6.0 이상
- academic level 4.5 → 6.5

### Gate 6 — v0.9 external replication

- plugin author 외 evaluator 2명
- external holdout 20%
- discrepancy investigation
- artifact DOI와 one-command reproduction

목표 점수:

- publication 5.5 → 8.0
- academic 6.5 → 7.5
- internal engineering report 6.5 → 8.5

### Gate 7 — v1.0 release

필수:

- v0.3 대비 ordinary coding non-inferiority
- PRD·Acceptance·Release 최소 효과 gate 통과
- Implement는 효과 gate 통과 또는 quality claim 제거
- unauthorized mutation 0/300
- external replication 성공
- migration/rollback/clean uninstall 검증
- marketplace installation smoke

## 9. 예상 최종 점수

| 차원 | 현재 | Gate 3 | Gate 5 | v1.0 목표 |
|---|---:|---:|---:|---:|
| lifecycle·범용성 | 5.0 | 8.0 | 8.0 | 8.0–8.5 |
| benchmark rigor | 6.0 | 6.5 | 8.0 | 8.0–8.5 |
| publication readiness | 5.5 | 6.0 | 7.0 | 8.0 |
| general quality-lift evidence | 3.5 | 4.0 | 6.0 | 6.5–7.0 |
| 학술 수준 | 4.5 | 5.0 | 6.5 | 7.5 |
| 내부 engineering report | 6.5 | 7.5 | 8.0 | 8.5 |
| ecosystem | 3.0 | 5.0 | 5.5 | 6.0+ |

general quality-lift는 가장 올리기 어렵다. PRD와 Acceptance만 좋아지고
Implement가 계속 동률이면 7점으로 올리지 않는다. 대신 “targeted workflow
quality”와 “ordinary coding non-inferiority”를 별도 지표로 보고한다.

## 10. 바로 시작할 첫 구현 묶음

첫 iteration은 다음 12개 산출물로 제한한다.

1. `workgraph.schema.json`
2. `validate-workgraph.py`
3. `migrate-workgraph.py`
4. `wigtn.py init`
5. `wigtn.py import`
6. `wigtn.py plan`
7. `wigtn.py status`
8. `wigtn.py next`
9. requirement→task→check fixture 10개
10. resume/drift/stale fixture 10개
11. `work-planner` skill
12. bare/placebo/WorkGraph component ablation runner

이 묶음이 deterministic 30/30과 첫 12-task model pilot을 통과하기 전에는
adapter ecosystem이나 autonomous loop를 구현하지 않는다.

## 11. 2026-07-28 Gate 1 진행 상태

완료:

- WorkGraph 1.0 JSON Schema와 dependency-free validator
- atomic writer, source import, drift/stale propagation, 0.1→1.0 migration
- `init/import/plan/status/next/diff/doctor` CLI
- mutation dry-run과 `--apply`
- unchanged import/plan/drift idempotency
- 신규 `work-planner` skill과 PRD·screen·acceptance·delivery·release handoff
- WorkGraph 67개 deterministic contract case
- trigger contract 35개
- seed-frozen paired schedule, arm counterbalance, missing/duplicate pair reject
- GPT-5.6 Sol 12-repository explicit capability pilot 12/12,
  144/144 endpoint PASS
- 57-file sanitized packet hash/tamper verification

아직 완료되지 않음:

- bare 대비 planning quality causal comparison
- task당 3회 반복
- implicit invocation pilot
- 3 OS와 실제 OSS repository
- independent human reviewer
- 구조화 task refinement/transition CLI
- WorkGraph와 Evidence Contract 자동 reconciliation

따라서 Gate 1의 deterministic foundation과 첫 capability pilot은 통과했지만,
lifecycle·범용성 점수는 실제 repository/OS resume test와 causal
non-inferiority 전까지 6.5로 확정하지 않는다.
