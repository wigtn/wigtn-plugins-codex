<div align="center">

# WIGTN Plugin for Codex

**Codex의 자율성은 그대로. PRD·작업 계획·검증·Git 권한은 필요한 순간에만.**

![Version](https://img.shields.io/badge/version-0.5.3-6C5CE7?style=for-the-badge)
![Skills](https://img.shields.io/badge/core_skills-9-00B894?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Codex-111827?style=for-the-badge)
![License](https://img.shields.io/badge/license-Apache--2.0-0984E3?style=for-the-badge)

</div>

---

## 왜 WIGTN Plugin for Codex인가요?

Codex는 코드 탐색, 설계 판단, 구현과 기본 리뷰를 이미 잘합니다. WIGTN
Plugin은 그 능력을 무거운 절차로 감싸지 않습니다. 대신 PRD 필수 항목,
화면정의 산출물, 요구사항별 실행 근거, commit·push·PR 권한처럼
**결과가 명확한 규칙**만 skill로 제공합니다.

```text
일반 코딩 요청       → Codex가 평소처럼 자유롭게 처리
PRD·명세·검증 요청  → 해당 WIGTN skill 선택
전체 구현·검증 요청 → qualified $verified-delivery를 명시했을 때만 실행
```

핵심 원칙은 간단합니다.

- 평소에는 가볍게: 일반 수정에 PRD나 팀 배정을 강제하지 않습니다.
- 점수보다 증거: 파일, 라인, 테스트 결과와 실행 로그로 판단합니다.
- 프로젝트 우선: 일반론보다 저장소의 기존 패턴과 디자인 언어를 먼저 읽습니다.
- 권한은 명확하게: 요청 없이 커밋, 푸시, PR, 배포를 실행하지 않습니다.

---

## 빠른 시작

GitHub 마켓플레이스를 등록하고 플러그인을 설치하세요.

```bash
codex plugin marketplace add wigtn/wigtn-plugins-codex
codex plugin add wigtn-plugins-with-codex@wigtn
```

세션 지식 자동 축적이 필요한 사용자만 별도 hook 플러그인을 설치합니다.

```bash
codex plugin add wigtn-knowledge-wiki@wigtn
```

두 플러그인은 릴리스 버전을 함께 올립니다. Core만 설치해도 되고,
Knowledge Wiki가 필요할 때 같은 버전의 별도 플러그인을 추가하면 됩니다.

Codex 앱에서는 Plugins를 열어 WIGTN 마켓플레이스를 선택한 뒤 플러그인을 설치하고 새 작업을 시작하면 됩니다. 설치 후에는 별도 명령을 외울 필요 없이 자연어로 요청하세요.

```text
"OAuth 로그인 기능 PRD 뽑아줘"
"이 PRD로 화면정의서 만들어줘"
"요구사항이 실제 구현에 반영됐는지 검증해줘"
"변경사항 검증하고 커밋해줘"
```

특정 스킬을 확실히 지정하고 싶다면 `$스킬명`으로 호출할 수 있습니다.

```text
$wigtn-plugins-with-codex:product-spec OAuth 로그인 PRD 만들어줘
$wigtn-plugins-with-codex:verified-delivery 이 기능 구현하고 검증해줘
```

---

## 전체 워크플로

```text
아이디어
  │
  ▼
product-spec ───────── PRD 생성·검토·딥다이브
  │
  ├── screen-spec ──── IA·사용자 흐름·화면 명세·와이어프레임
  │        │
  │        └── design-direction ── 프로젝트 네이티브 디자인 방향
  │
  ▼
work-planner ───────── requirement→task→check WorkGraph·resume·drift
  │
  ▼
verified-delivery ──── 명시 호출 기반 구현·로컬 검증
  │
  ▼
acceptance-verifier ── 요구사항 ↔ 코드·테스트 증거 매핑
  │
  ▼
release-readiness ──── 안전한 커밋·푸시·PR
```

문서나 발표가 필요할 때는 `handdrawn-diagram`, `wigtn-presentation`을 독립적으로 사용할 수 있습니다.

---

## 포함된 9개 Core 스킬

| 스킬 | 하는 일 | 자연어 호출 예시 | 호출 정책 |
|---|---|---|---|
| `product-spec` | 구현 가능한 PRD 생성, 리뷰, 딥다이브 | “PRD 뽑아줘” | 자동 |
| `screen-spec` | 요청한 IA, User Flow, 화면 명세, self-contained lo-fi HTML 와이어프레임 또는 개발 핸드오프 | “화면정의서 만들어줘” | 자동 |
| `work-planner` | 요구사항을 저장·재개 가능한 dependency-aware WorkGraph로 변환 | “이 계획을 WorkGraph로 저장해줘” | 자동·저장형 전용 |
| `acceptance-verifier` | PRD 요구사항과 코드·실행 테스트 증거를 연결해 충족 여부 판정 | “요구사항 반영됐는지 검증해줘” | 자동 |
| `design-direction` | 기존 디자인 시스템을 먼저 읽고 신규 UI 방향 제안 | “이 UI 디자인 방향 잡아줘” | 자동·제한적 |
| `verified-delivery` | 구현에 비례적인 requirement→code→executed-check 근거 추가 | `$verified-delivery로 구현해줘` | **명시 호출 전용** |
| `release-readiness` | 변경 범위를 보존하며 검증, 커밋, 푸시, PR 수행 | “커밋해줘”, “PR 올려줘” | 자동·제한적 |
| `handdrawn-diagram` | Mermaid handDrawn 소스·SVG·PNG를 구조 및 시각 검증 | “손그림 아키텍처 만들어줘” | 자동·스타일 명시형 |
| `wigtn-presentation` | Codex 발표 생성 위에 WIGTN 잉크 네이비·퍼플 점 브랜드를 적용 | “WIGTN 발표자료 만들어줘” | 자동·WIGTN 명시형 |

### 자동 호출과 명시 호출

대부분의 스킬은 요청 의도가 설명과 일치할 때 Codex가 자동으로 선택합니다. `verified-delivery`만 예외입니다. 일반적인 코딩 요청이 의도치 않게 전체 전달 파이프라인으로 커지는 것을 막기 위해 `$wigtn-plugins-with-codex:verified-delivery`를 명시해야 합니다.

---

## v0.5.3: 하네스 경량화·스택 중립화

- 항상 노출되는 Core 스킬 설명 합계를 2,980자에서 2,162자로 줄여
  선택 신호는 유지하면서 기본 컨텍스트 부담을 약 27% 낮췄습니다.
- Screen Spec의 본문·템플릿·참조 자료를 30,960 bytes에서 13,558 bytes로
  줄이고, 요청한 산출물과 그 의존 자료만 읽도록 정리했습니다.
- 화면 템플릿에서 임의의 라우트·HTTP 상태 코드·breakpoint·CSS token과
  Next.js, Supabase, Auth.js, Zod, TanStack 같은 스택 가정을 제거했습니다.
- Verified Delivery의 상세 증거 계약과 Acceptance Verifier의 저장형 JSON
  handoff는 필요한 요청에서만 읽도록 분리했습니다.
- Presentation의 중복 브랜드·디자인 지침을 하나의 계약으로 합쳐 4,825
  bytes에서 3,082 bytes로 줄였습니다.
- 새 Screen Spec 플레이스홀더와 외부 리소스·anchor·요구사항 연결 검증은
  그대로 유지하고 회귀 검사를 보강했습니다.

---

## v0.5.2: 권한·검증 하드닝

- Knowledge Wiki의 큐 작업은 캡처 당시의 push 권한을 넘어서지 못하며,
  처리 전에 목적지가 바뀌거나 24시간 TTL이 지난 작업은 폐기합니다.
- 잘못된 timeout이나 손상된 작업 하나가 뒤의 큐를 막지 않으며, 처리 후에는
  transcript 본문 대신 상태 메타데이터만 남깁니다.
- 읽기 전용 doctor가 설정 범위, 목적지 namespace, 큐 상태, Codex 실행 가능
  여부를 transcript 노출 없이 점검합니다.
- HandDrawn PNG는 청크·CRC·IDAT·IEND까지 검증하고, 발표와 wireframe은
  CSS `@import`, 원격 `url()`, media resource를 포함한 외부 의존성을 차단합니다.
- Core와 Knowledge Wiki 매니페스트를 0.5.2 lockstep으로 검증하며 어느 한쪽의
  버전·정책·경로 오류도 CI와 릴리스를 통과하지 못합니다.
- Design Direction의 9개 스타일 레퍼런스를 98,899 bytes에서 18,479 bytes로
  줄이고 결정 규칙·접근성·금지 패턴·완료 조건만 남겼습니다.

Knowledge Wiki 상태만 진단할 때는 설치된 플러그인의 번들 스크립트를
`--json`으로 실행합니다. 설정이나 큐를 수정하지 않습니다.

```bash
python3 plugins/wigtn-knowledge-wiki/scripts/knowledge_wiki/doctor.py --json
```

---

## v0.5.1: 시각 산출물 전달 강화

- HandDrawn은 Mermaid CLI 버전을 기록하고 CJK native SVG label, source·SVG·PNG 구조 검사, 실제 PNG 육안 검사를 적용합니다.
- WIGTN Presentation은 PPTX·Slides 생성기를 중복하지 않는 브랜드 overlay이며, HTML은 명시 요청에만 self-contained로 만듭니다.
- Screen Spec wireframe은 CDN 없이 반응형으로 동작하고 외부 의존성·viewport·내부 anchor를 검사합니다.
- 런타임 문서의 죽은 참조와 연결되지 않은 bundled resource를 정적 계약에서 차단합니다.

---

## v0.5.0: GPT‑5.6 Sol 하네스 다이어트

- PRD는 Compact가 기본이며 실제 추가 계약이 필요한 경우만 Full로 승격합니다.
- Screen Spec은 요청 산출물과 dependency closure만 만들고 전체 요청만 5종 번들을 만듭니다.
- Work Planner는 저장·resume·drift가 필요한 WorkGraph 요청에만 개입합니다.
- Verified Delivery는 암시 호출을 차단하고 중복 fast/assurance 절차를 하나의 비례형 evidence 계약으로 줄였습니다.
- Acceptance 결과는 대화와 JSON에서 같은 canonical 상태를 사용합니다.
- Knowledge Wiki와 Stop hook은 별도 `wigtn-knowledge-wiki` 플러그인으로 분리했습니다.

---

## v0.4.0: 옵트인 Knowledge Wiki

v0.4.0에서 도입한 기능은 v0.5.0부터 별도 플러그인으로 제공됩니다. 허용된 저장소의 Codex 세션에서 재사용 가능한 기술 지식만
일반화해 팀 위키의 `per-user/` 영역에 축적합니다. 설치만으로는 동작하지
않으며, 별도 설정에서 `enabled: true`와 좁은 `include` 범위를 지정해야 합니다.
시크릿·개인정보·조직 식별 정보는 결정론 검사와 독립 LLM 감사를 모두
통과해야 하고, `shared/` 자동 게시와 기존 미push 커밋이 있는 상태의 push는
차단합니다.

---

## v0.3.0: PRD·상태·검증·릴리스 규칙

v0.3.0은 `product-spec` → `work-planner` → `verified-delivery` →
`acceptance-verifier` → `release-readiness` 사이에서 요구사항·코드·실행
검사·릴리스 권한을 선택적 JSON handoff로 연결합니다. 일반 답변에는
상태 파일을 만들지 않으며, 저장 산출물이나 세션 간 handoff가 명시된 경우에만
사용합니다.

| 영역 | v0.3.0 변경 |
|---|---|
| Evidence Contract | 거짓 `verified`, 누락된 gap, 권한 없는 외부 작업, 비이식 경로를 결정론적으로 차단 |
| 핵심 4개 스킬 | 사람용 보고서와 기계 판독용 canonical status·authority를 연결 |
| PRD profile | 간결한 요청은 Compact, 복잡한 lifecycle은 Full 계약으로 분리 |
| Artifact interop | Spec Kit·OpenSpec·BMAD 정규화, 변경 없는 evidence resume, spec drift 시 무효화 |
| Project context | 선택적 `.wigtn/project.json`으로 요구사항 출처·검증 명령·보호 경로·profile 공유 |
| Evidence status | source hash drift, 사라진 코드 증거, canonical status와 release authority 점검 |
| Screen contract | 선택 산출물과 dependency closure, wireframe anchor, FR handoff drift를 결정론적으로 검증 |
| Release state | branch/upstream/충돌/staged/unstaged/untracked를 mutation 없이 JSON 점검 |
| 평가 분리 | trigger/evidence 정적 계약과 실제 model behavior smoke를 별도 실행 |
| 비용 회귀 | bare/placebo4/core4/full9를 GPT‑5.5/5.6 Sol에서 분리하고 품질·token·latency를 별도 공개 |

WorkGraph는 PRD를 많이 쓰게 만드는 절차가 아니라, 사용자가 저장형 계획을
요청했을 때만 다음 연결을 보존하는 선택적 상태계약입니다.

```text
requirement → product/screen artifact → implementation task
            → executable check → release gate
```

source hash가 바뀌면 연결된 artifact·task·check·release gate가 `stale`로
전파됩니다. passing check와 evidence reference가 없으면 task는 `verified`가
될 수 없고, release gate는 Git 권한을 부여하지 않습니다.

```bash
python3 plugins/wigtn-plugins-with-codex/scripts/wigtn.py --json init
python3 plugins/wigtn-plugins-with-codex/scripts/wigtn.py --json init --apply
python3 plugins/wigtn-plugins-with-codex/scripts/wigtn.py --json import docs/PRD.md --apply
python3 plugins/wigtn-plugins-with-codex/scripts/wigtn.py --json plan --apply
python3 plugins/wigtn-plugins-with-codex/scripts/wigtn.py --json status
python3 plugins/wigtn-plugins-with-codex/scripts/wigtn.py --json next
python3 plugins/wigtn-plugins-with-codex/scripts/wigtn.py --json diff --check
python3 plugins/wigtn-plugins-with-codex/scripts/wigtn.py --json doctor
```

mutation 명령은 `--apply`가 없으면 dry-run이며, 동일한 import·plan·drift
적용은 revision을 올리지 않습니다. 자세한 상태 의미는
[WorkGraph lifecycle](docs/WORKGRAPH-LIFECYCLE.md)을 참고하세요.

## 구현 하네스를 줄인 이유

GPT‑5.5·GPT‑5.6 Sol 평가에서 일반 구현 성공률의 positive lift는
확인되지 않았고, 개정 전 heavy workflow는 같은 성공에 더 많은 token과
시간을 사용했습니다. v0.3.0은 모델을 장문 절차로 감싸는 대신 결과의
형태, 상태 전이, 검증 근거와 권한 경계를 더 정확히 만드는 방향으로
개편했습니다.

| 영역 | 고도화 |
|---|---|
| `product-spec` | 생성·검토·deep dive 계약 분리, 조건부 섹션, 안정적인 요구사항 ID, PRD validator |
| `verified-delivery` | 사전 위험 invariant, failure-focused test, 최종 diff 재검토, 요구사항별 실행 증거 |
| `acceptance-verifier` | 요구사항마다 code evidence와 executed-test evidence를 분리한 read-only matrix |
| `release-readiness` | review·prepare·commit·push·PR 권한을 사용자 문장 그대로 분리 |
| 자동 호출 | 일반 구현·버그 수정·리팩터링은 기본 Codex에 맡기고 heavy workflow 오호출 방지 |
| 설치 UX | 모든 starter prompt를 설치된 플러그인의 qualified skill name으로 고정 |
| 검증 | 공식 manifest/skill validator, 저장소 계약, lexical trigger 49건을 함께 실행 |

### 검증된 주장과 아직 검증되지 않은 주장

2026년 GPT‑5.5/5.6 Sol 평가가 지지하는 범위는 좁습니다.

| 주장 | 판정 |
|---|---|
| 테스트 fixture에서 Product Spec 계약 충족률을 높였다 | 지지됨 |
| 익명 model-judge PRD screen에서 Core/Full이 bare보다 높았다 | 지지됨, human blind는 미완 |
| Acceptance canonical status 일관성을 높였다 | 방향 지지됨 (`10/16 → 14/16`, p=.125) |
| 모호한 완료 요청에서 무단 Git mutation을 막았다 | 지지됨 |
| 일반 코딩을 token-efficient하게 만든다 | 현재 fixture에서는 반증됨 |
| `verified-delivery`가 deterministic/블라인드 구현 품질을 높인다 | 현재 fixture에서는 지지되지 않음 |
| 모든 실제 저장소에 일반화된다 | 아직 입증되지 않음 |

따라서 `verified-delivery`는 “코드를 더 잘 짜는 모드”가 아니라, 중요한
작업에서 requirement→code→executed check 증거를 남기는 explicit beta로
제공합니다.

---

## Claude Code 버전과 무엇이 다른가요?

이 플러그인은 기존 Claude Code 플러그인을 디렉터리째 복사한 포팅이 아니라, Codex에 맞춘 선택적 재설계입니다.

| Claude Code 플러그인 | Codex 플러그인 |
|---|---|
| 14개 역할 에이전트와 5개 슬래시 명령 | 하나의 책임을 가진 9개 스킬 |
| 고정된 병렬 팀 오케스트레이션 | Codex의 기본 탐색·구현 판단 활용 |
| `/prd`, `/implement`, `/auto-commit` | 자연어 자동 선택과 `$스킬명` 명시 호출 |
| 숫자 기반 품질 게이트 | 코드·테스트·실행 결과 기반 증거 |
| 전체 파이프라인 중심 | 필요한 순간에만 열리는 얇은 워크플로 |

Claude 전용 도구 이름, 고정 서브에이전트 fan-out, 자동 모델 라우팅, 자동 의존성 설치와 파괴적 롤백은 포함하지 않습니다. 자세한 설계 배경은 [마이그레이션 문서](docs/MIGRATION.md)를 참고하세요.

---

## 저장소 구조

```text
.
├── .agents/plugins/marketplace.json
├── docs/
│   ├── PRD.md
│   ├── EVALS.md
│   ├── EVIDENCE-CONTRACT.md
│   └── MIGRATION.md
├── plugins/wigtn-plugins-with-codex/
│   ├── .codex-plugin/plugin.json
│   ├── references/
│   ├── schemas/
│   ├── scripts/
│   └── skills/
│       ├── product-spec/
│       ├── screen-spec/
│       ├── work-planner/
│       ├── acceptance-verifier/
│       ├── design-direction/
│       ├── verified-delivery/
│       ├── release-readiness/
│       ├── handdrawn-diagram/
│       └── wigtn-presentation/
├── plugins/wigtn-knowledge-wiki/
│   ├── .codex-plugin/plugin.json
│   ├── hooks/hooks.json
│   ├── scripts/knowledge_wiki/
│   └── skills/knowledge-wiki/
├── scripts/
└── tests/
```

---

## 검증

매니페스트, 스킬 구조, 정책과 트리거 계약을 한 번에 검사합니다.

```bash
./scripts/validate.sh
```

결정론적 trigger·evidence 계약만 실행하려면:

```bash
./scripts/run-static-contracts.sh
```

이 suite에는 plugin resource 무결성, 다이어그램·HTML 발표 계약,
responsive wireframe portability, WorkGraph lifecycle·drift·migration·CLI의
67개 결정론적 케이스와 paired schedule 무결성 검사도 포함됩니다.

신규 `work-planner`의 모델 기반 capability pilot은 12개 격리 저장소에서
별도로 실행합니다.

```bash
./scripts/run-workgraph-pilot.sh
WIGTN_WORKGRAPH_PILOT_ROOT=/tmp/fresh-run \
  ./scripts/run-workgraph-pilot.sh --execute
```

이 pilot은 lifecycle artifact가 올바르게 생성되는지 검사하며 bare 대비
품질 향상을 주장하지 않습니다.
[2026-07-28 WorkGraph capability 보고서](docs/WORKGRAPH-PILOT-2026-07-28-KO.md)에
12/12 case, 144/144 endpoint, infra deviation, raw packet hash, 허용되는 주장
경계를 공개했습니다.

일반 코딩에서 하네스가 방해되지 않는지 확인하는 4-arm gate는:

```bash
WIGTN_ORDINARY_GATE_ROOT=/tmp/fresh-ordinary-gate \
  bash scripts/run-ordinary-gate.sh --execute
```

GPT-5.6 Sol 48회 파일럿은 bare/core4/full8/full9 모두 hidden test 12/12,
scope·sentinel·불필요한 lifecycle state 12/12로 통과했습니다. 모든 arm이
만점이라 품질 향상 근거로는 쓰지 않으며, 정확한 판정 기준과 ceiling
effect는 [일반 코딩 비간섭 보고서](docs/ORDINARY-NONINTERFERENCE-GATE-2026-07-28-KO.md)에
공개했습니다.

격리된 bare/plugin 실제 모델 smoke는 명시적으로 실행합니다.

```bash
./scripts/run-behavior-evals.sh --execute
```

Core 4의 내용 효과와 catalog 길이 효과를 분리하는 package ablation은:

```bash
./scripts/run-package-ablation.sh --execute
```

Acceptance evidence, Implement/Release, 실제 저장소 pilot은 각각:

```bash
bash scripts/run-acceptance-hard.sh --execute
bash scripts/run-delivery-recheck.sh --execute
bash scripts/run-actual-repo-pilot.sh --execute
```

비용이 큰 model eval은 명시적 `--execute`에서만 호출합니다. 익명 구현
비교는 delivery 결과가 존재할 때
`bash scripts/run-delivery-blind.sh --execute`로 별도 실행합니다.
Package ablation의 PRD를 익명 비교하려면
`bash scripts/run-prd-blind.sh --execute`를 실행합니다. 두 blind runner는
판정 시점에 후보 매핑 파일을 만들지 않으며 model judge 결과를 human
sign-off로 취급하지 않습니다.

트리거 fixture 49건은 skill 설명의 lexical 경계를 점검할 뿐 실제 모델
router를 검증하지 않습니다. 현재 paired behavior smoke는 PRD, acceptance,
IA, 일반 코딩 4개 계약만 다룹니다. Evidence Contract fixture도 결정론적인
계약 검사입니다.
behavior smoke의 성공은 실행 건전성만 뜻하며 품질 향상을 입증하지 않습니다.
자세한 주장 경계와 재현 절차는 [평가 가이드](docs/EVALS.md)를 참고하세요.
내부 oracle을 주효과에서 제외하고 SWE-Skills-Bench, FeatureBench,
SWE-Lancer, Terminal-Bench, ISO/INCOSE 기준으로 재설계한 통합 초안은
[2026-07-28 기술 리포트 초안](docs/TECHNICAL-REPORT-DRAFT-2026-07-28-KO.md)에
정리했습니다.
GPT‑5.5/5.6 Sol 36회 paired smoke의 수치와 한계는
[2026-07-28 behavior smoke 보고서](docs/BEHAVIOR-SMOKE-2026-07-28.md)에
공개했습니다.
다음 단계의 task bank, package ablation, blind review, 외부 재현 gate는
[벤치마크 4→6점 업그레이드 계획](docs/BENCHMARK-UPGRADE-PLAN-KO.md)에
정리했습니다.
경쟁군에서 선택적으로 가져온 기능, 32회 package ablation 결과, Core/Full
분리 보류 결정은
[경쟁 비교·재평가 보고서](docs/COMPETITIVE-REASSESSMENT-2026-07-28-KO.md)에
공개했습니다.
Acceptance Hard, Implement/Release, 파일시스템 매핑을 제거한 PRD·코드
blind screen, 기능별 제품 결정과 최종 claim boundary는
[v0.3 선택적 하네스 연구 보고서](docs/RESEARCH-ROUND2-2026-07-28-KO.md)에
정리했습니다.
WorkGraph, adapter/pack ecosystem, 100-task confirmatory benchmark, 외부
재현까지의 제품·연구 gate와 중단 기준은
[v0.4→v1.0 경쟁력 고도화 계획](docs/V04-V10-COMPETITIVE-ROADMAP-KO.md)에
정리했습니다.
FeatureBench 네 저장소에서 실행한 feature-level paired 파일럿, 첫
양성처럼 보인 결과의 reference leakage 적발, 역순 재현 실패와 다음
격리 holdout 설계는
[FeatureBench quality-lift 파일럿](docs/FEATUREBENCH-LIFT-PILOT-2026-07-28-KO.md)에
정리했습니다. 재현 가능하고 무결한 positive lift는 아직 0/4입니다.

Pull Request와 `main` 푸시에서는 저장소 계약, 사용 가능한 공식 Codex
validator, lexical trigger fixture 49건, Evidence Contract fixture를 검사합니다.
`main`에서 어느 플러그인 매니페스트든 버전을 올리면 두 버전의 일치 여부를
검사하고 동일 버전의 GitHub tag와 Release를 생성합니다.

v0.3.0의 구조·trigger·Evidence Contract·WorkGraph 검증은 완료됐습니다.
실제 저장소 confirmatory study와
독립 인간 blind review가 완료되기 전까지는 전체 품질 향상 문구를 사용하지
않습니다.

---

## 안전 설계

- 일반 코딩에 PRD·작업 계획·검증 절차를 강제하지 않습니다.
- `verified-delivery`는 명시적으로 호출해야 합니다.
- 사용자 요청 없이 커밋, 푸시, PR, 이슈 생성 또는 배포를 하지 않습니다.
- 저장소의 기존 변경사항을 사용자 작업으로 취급하고 보존합니다.
- Core에는 MCP, 앱, lifecycle hook, 자동 Sol/Terra/Luna 라우팅을 번들하지 않습니다.

---

## 라이선스

[Apache License 2.0](LICENSE)
