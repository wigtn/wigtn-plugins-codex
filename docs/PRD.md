# PRD: WIGTN Plugins for Codex

> 제품명: `wigtn-plugins-with-codex`  
> 문서 상태: Implementation baseline 0.2  
> 작성일: 2026-07-15  
> 대상 버전: MVP `0.1.0`  
> 원본 자산: `wigtn-plugins-with-claude-code`  
> 배포 대상: Codex in ChatGPT desktop app, Codex CLI, Codex IDE extension

---

## 1. 제품 요약

`wigtn-plugins-with-codex`는 기존 Claude Code 플러그인을 그대로 포팅하지 않는다. Codex가 이미 잘하는 코드 탐색, 설계 판단, 구현, 기본 리뷰는 Sol과 Codex의 기본 기능에 맡기고, WIGTN이 축적한 다음 자산만 Codex 네이티브 스킬로 제공한다.

1. 아이디어를 구현 가능한 PRD로 정리하는 제품 명세 워크플로
2. PRD를 IA, 사용자 흐름, 화면 명세, 와이어프레임, 개발 핸드오프로 변환하는 화면정의 워크플로
3. 요구사항과 실제 코드·테스트 증거를 연결하는 인수조건 검증
4. 기존 프로젝트의 디자인 언어를 먼저 읽고 필요한 경우에만 스타일 방향을 제안하는 디자인 가이드
5. 검증 가능한 구현 루프와 안전한 릴리스 준비
6. WIGTN 고유의 손그림 다이어그램 및 브랜드 발표자료 생성
7. 후속 버전에서는 반복된 실패를 짧고 실용적인 `AGENTS.md` 개선안으로 전환하는 회고

플러그인의 역할은 Codex를 지휘하는 거대한 하네스가 아니라, 필요한 순간에만 열리는 얇은 작업 계약이다.

---

## 2. 배경과 문제

### 2.1 현재 플러그인의 강점

기존 `wigtn-plugins-with-claude-code`에는 다음과 같은 차별 자산이 있다.

- PRD부터 구현·리뷰·커밋까지 이어지는 전체 제품 개발 흐름
- IA, 사용자 흐름, 화면 상태, 개발 핸드오프를 포함한 화면정의 산출물
- 프로젝트 디자인 스타일을 구체적인 구현 규칙으로 변환한 레퍼런스
- 한글/CJK 렌더링 문제까지 반영한 손그림 다이어그램 생성법
- WIGTN 브랜드 색상, 로고, 퍼플 점 모티프가 포함된 발표자료 규칙
- 테스트, 타입체크, 빌드 같은 객관 검증을 중요하게 다루는 운영 철학

### 2.2 현재 구조를 그대로 포팅할 때의 문제

기존 플러그인은 약 2.3만 줄의 지침과 13개 역할 에이전트, 5개 슬래시 명령, 6개 스킬로 구성되어 있으며 Claude Code의 도구 이름과 실행 모델에 강하게 결합되어 있다.

- `AskUserQuestion`, `TaskCreate`, `TaskUpdate`, `Agent`, `subagent_type` 등 Claude 전용 호출 방식에 의존한다.
- 작은 수정도 PRD, 아키텍처 결정, 팀 할당, 병렬 리뷰 같은 무거운 절차로 확장될 수 있다.
- 범용 frontend/backend/mobile/AI 역할 프롬프트가 Codex의 저장소 기반 판단과 중복된다.
- 임의의 100점 품질 점수는 같은 코드에서도 판정이 흔들릴 수 있다.
- 자동 커밋, 푸시, PR 생성, 강제 롤백은 사용자가 요청한 작업 범위를 넘어설 위험이 있다.
- 긴 공통 지침이 최신 모델의 자율적인 문제 해결을 제한할 수 있다.
- Claude Code의 `commands/`와 `agents/` 구조는 Codex 플러그인의 기본 배포 단위가 아니다.

### 2.3 Codex 네이티브 기회

Codex 스킬은 progressive disclosure 방식으로 동작한다. 새 작업이 시작될 때는 스킬의 이름, 설명, 경로만 제공되고, 실제 `SKILL.md`는 명시 호출되거나 사용자 요청이 `description`과 일치할 때만 로드된다.

따라서 다음 설계가 가능하다.

- 평소 코딩에서는 Sol을 자유롭게 둔다.
- “PRD 뽑아줘”, “화면정의서 만들어줘”처럼 명확한 요청에만 전문 스킬을 자동 호출한다.
- 무거운 전체 파이프라인은 명시적으로 호출했을 때만 실행한다.
- 결정론적으로 실행해야 하는 검증만 스크립트로 구현한다.
- 저장소 고유 규칙은 플러그인이 아니라 해당 저장소의 `AGENTS.md`에 둔다.

---

## 3. 제품 비전

> Codex의 판단력을 가리지 않으면서, 아이디어부터 검증 가능한 배포 준비까지 WIGTN의 제품 개발 노하우를 필요한 순간에만 제공한다.

### 3.1 핵심 원칙

1. **Sol-first, model-agnostic**  
   플러그인은 모델을 강제로 변경하지 않는다. 복잡한 코딩은 사용자가 선택한 Sol에 맡기며, 모델 라우팅은 MVP 범위에서 제외한다.

2. **Freedom by default**  
   일반적인 코드 수정에 PRD나 아키텍처 절차를 강제하지 않는다.

3. **Progressive disclosure**  
   각 스킬은 하나의 명확한 업무만 담당하며 필요한 경우에만 전체 지침과 레퍼런스를 읽는다.

4. **Evidence over scores**  
   품질 점수보다 파일·라인·실행 명령·종료 코드·스크린샷 같은 검증 가능한 증거를 우선한다.

5. **Project-native before generic best practice**  
   새 패턴을 제안하기 전에 저장소의 기존 구조, 테스트, 스타일, 인접 코드를 확인한다.

6. **Explicit authority for external mutations**  
   커밋, 푸시, PR 생성, 이슈 생성, 배포는 사용자가 명시적으로 요청한 경우에만 수행한다.

7. **Ask only when blocked**  
   되돌리기 쉬운 작은 판단은 합리적으로 진행하고 결과에 가정을 기록한다. 결과가 크게 달라지는 선택만 질문한다.

8. **Thin core, rich references**  
   `SKILL.md`는 짧게 유지하고 템플릿·체크리스트·스타일 가이드는 필요한 레퍼런스로 분리한다.

---

## 4. 목표와 비목표

### 4.1 목표

- 자연어 “PRD 뽑아줘” 요청으로 `product-spec` 스킬이 자동 호출된다.
- 자연어 “화면정의서 만들어줘” 요청으로 `screen-spec` 스킬이 자동 호출된다.
- 단순 코드 수정에서는 제품 기획·화면정의 스킬이 오탐 호출되지 않는다.
- PRD의 요구사항과 실제 구현 증거를 연결하는 검증 표를 생성한다.
- 기존 Claude 자산 중 고유한 템플릿과 운영 노하우만 재사용한다.
- Codex 데스크톱 앱, CLI, IDE에서 같은 스킬 패키지를 사용할 수 있다.
- 플러그인 설치 후 새 작업에서 자동 발견되며 `$스킬명`으로 확정 호출할 수 있다.
- 플러그인 적용 전후의 결과를 반복 가능한 평가 세트로 비교한다.

### 4.2 비목표

- Claude Code의 13개 에이전트를 일대일로 포팅하지 않는다.
- Claude Code의 `/prd`, `/implement`, `/auto-commit` 명령 체계를 그대로 복제하지 않는다.
- 모든 코딩 요청을 WIGTN 전체 파이프라인으로 강제하지 않는다.
- 플러그인이 Sol/Terra/Luna를 자동 변경하지 않는다.
- 자체 MCP 서버나 Linear 전용 MCP를 MVP에서 번들하지 않는다.
- 임의의 100점 점수로 코드 품질을 판정하지 않는다.
- 사용자 요청 없이 브랜치 생성, 커밋, 푸시, PR, 배포를 실행하지 않는다.
- 사용자 요청 없이 `AGENTS.md`를 자동 수정하지 않는다.
- Codex 자체의 `/review`, Plan mode, 기본 explorer/worker 에이전트를 중복 구현하지 않는다.

---

## 5. 대상 사용자와 주요 작업

### 5.1 대상 사용자

| 사용자 | 요구 |
|---|---|
| 개인 개발자 | 짧은 자연어로 PRD와 구현 가능한 계획을 만들고 싶다. |
| WIGTN 제품 팀 | 팀의 문서·디자인·검증 형식을 반복 사용하고 싶다. |
| 프론트엔드 개발자 | PRD에서 누락 없는 화면 상태와 개발 핸드오프를 얻고 싶다. |
| 리뷰어 | 요구사항이 실제 코드와 테스트로 충족되었는지 근거 중심으로 확인하고 싶다. |
| 플러그인 관리자 | 팀에 설치 가능한 하나의 Codex 패키지로 배포하고 싶다. |

### 5.2 핵심 사용자 흐름

#### 흐름 A: 아이디어에서 PRD

```text
사용자: "OAuth 로그인 기능 PRD 뽑아줘"
→ product-spec 자동 선택
→ 저장소와 기존 문서가 있으면 읽기
→ 가정과 범위를 명시한 PRD 생성
→ 기본 자기검증 후 “PRD 디깅 → UI면 화면정의 → 구현”을 선택 가능한 다음 단계로 제안
```

#### 흐름 A-2: PRD 리뷰와 디깅

```text
사용자: "이 PRD 검토해줘"
→ product-spec 리뷰 모드
→ 누락·모순·모호성·검증 불가능한 기준을 영향도순으로 보고

사용자: "이 PRD 디깅해줘"
→ product-spec 딥다이브 모드
→ 실제 저장소 적합성, 보안, 엣지케이스, 운영 수명주기, 반대 가설까지 심층 분석
→ 사용자가 요청하기 전에는 원문을 자동 재작성하지 않음
```

#### 흐름 B: PRD에서 화면정의

```text
사용자: "이 PRD로 화면정의서 만들어줘"
→ screen-spec 자동 선택
→ IA → User Flow → Screen Spec → Wireframe → Dev Handoff 생성
→ 브라우저 사용이 가능하면 와이어프레임을 실제로 열어 검증
```

#### 흐름 C: 구현 결과 인수검증

```text
사용자: "PRD 요구사항이 이번 구현에 다 반영됐는지 검증해줘"
→ acceptance-verifier 자동 선택
→ FR/Acceptance Criteria 추출
→ 변경 파일·테스트·실행 결과 매핑
→ 충족 / 부분 충족 / 미충족 / 검증 불가 판정과 근거 보고
```

#### 흐름 D: 검증 가능한 구현 루프

```text
사용자: "$wigtn-plugins-with-codex:verified-delivery 이 기능 구현해줘"
→ 기존 패턴 조사
→ 필요한 최소 설계
→ 구현
→ 관련 테스트·타입체크·빌드
→ 요구사항 근거와 잔여 위험 보고
```

#### 흐름 E: 릴리스 준비

```text
사용자: "변경사항 검증하고 커밋 준비해줘"
→ release-readiness 선택
→ diff 및 저장소 상태 확인
→ 관련 검증 실행
→ 커밋 범위와 메시지 제안
→ 실제 커밋/푸시/PR은 사용자 요청 범위까지만 실행
```

---

## 6. 제품 구조

### 6.1 저장소 구조

```text
wigtn-plugins-with-codex/
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── docs/
│   ├── PRD.md
│   ├── EVALS.md
│   └── MIGRATION.md
├── plugins/
│   └── wigtn-plugins-with-codex/
│       ├── .codex-plugin/
│       │   └── plugin.json
│       ├── skills/
│       │   ├── product-spec/
│       │   ├── screen-spec/
│       │   ├── acceptance-verifier/
│       │   ├── design-direction/
│       │   ├── verified-delivery/
│       │   ├── release-readiness/
│       │   ├── handdrawn-diagram/
│       │   └── wigtn-presentation/
│       ├── scripts/
│       │   ├── detect-project-checks.sh
│       │   └── collect-change-evidence.sh
│       └── assets/
├── scripts/
│   ├── validate.sh
│   └── run-evals.sh
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

### 6.2 MVP 패키징 결정

- 플러그인 식별자와 폴더명은 `wigtn-plugins-with-codex`로 통일한다.
- `.codex-plugin/plugin.json`을 필수 엔트리로 사용한다.
- 스킬은 `skills/`에 배치한다.
- MVP는 앱, MCP 서버, lifecycle hook을 포함하지 않는 **skills-first 플러그인**으로 시작한다.
- 저장소 배포를 위해 `.agents/plugins/marketplace.json`을 제공한다.
- marketplace 항목은 `AVAILABLE`, `ON_INSTALL`, `Productivity`를 기본값으로 한다.
- 설치·업데이트 후에는 새 Codex 작업에서 동작을 확인한다.
- 훅은 A/B 평가에서 명확한 이득이 확인될 때만 후속 버전에 추가한다.

### 6.3 모델 정책

- 플러그인 manifest와 스킬은 특정 모델 ID를 하드코딩하지 않는다.
- 복잡한 구현·설계·리뷰의 권장 모델은 Sol이다.
- Terra/Luna 자동 라우팅은 MVP에 포함하지 않는다.
- Codex의 기본 subagent 또는 Ultra 사용 여부는 현재 작업과 사용자가 선택한 실행 설정에 맡긴다.
- 향후 모델 라우팅을 실험하더라도 별도 `dispatch` 스킬로 격리하고 기본 코딩 경로에는 적용하지 않는다.

---

## 7. 스킬 요구사항

### 7.1 `product-spec` — 신규 작성

#### 목적

아이디어, 이슈, 기존 코드 또는 대화 내용을 구현 가능한 PRD로 변환한다.

#### 자동 호출 예시

- “PRD 뽑아줘”
- “제품 요구사항 정리해줘”
- “이 아이디어를 개발 명세로 만들어줘”
- “기획서와 acceptance criteria 작성해줘”

#### 호출하면 안 되는 예시

- “버튼 색 바꿔줘”
- “이 에러 고쳐줘”
- “README 오타 수정해줘”
- 이미 명확한 구현 요청에 PRD 작성 요구가 없는 경우

#### 필수 출력

- 문제 정의
- 목표와 비목표
- 사용자와 핵심 시나리오
- 기능 요구사항과 안정적인 ID
- 비기능 요구사항은 실제 필요가 있는 항목만 작성
- 인수조건
- 가정, 미결정 사항, 리스크
- 구현 단계는 필요할 때만 간결하게 작성
- UI가 있으면 페이지·상태·사용자 흐름에 필요한 입력 제공

#### 설계 변경

- 기존 `/prd`의 강제 Scale Grade 질문을 제거한다.
- 저장소에서 합리적으로 추론 가능한 정보는 질문하지 않는다.
- 모든 기능에 Enterprise SLA나 상세 DB 스키마를 강제하지 않는다.
- PRD와 PLAN을 무조건 두 파일로 만들지 않는다. 작업 규모에 따라 하나의 PRD 안에 실행 단계를 포함할 수 있다.

#### 세 가지 모드와 후속 제안

- **생성 모드**: PRD 작성 후 자체 체크리스트로 누락과 모순을 1차 검증한다.
- **리뷰 모드**: “PRD 검토해줘”에서 문서의 누락, 충돌, 모호성, 범위 과잉과 검증 가능성을 근거 중심으로 검토한다.
- **딥다이브 모드**: “PRD 디깅해줘”에서 저장소 적합성, 보안, 실패 상태, 마이그레이션, 운영, 반대 가설까지 분석한다.
- 생성 완료 후 딥다이브를 강제 실행하지 않는다. `권장: PRD 디깅`, `UI가 있으면: 화면정의`, `준비됐으면: 구현`을 짧게 제시한다.
- 리뷰와 딥다이브는 사용자가 요청하기 전에는 원문을 자동으로 재작성하지 않는다.

### 7.2 `screen-spec` — 핵심 유지·Codex 네이티브 재작성

#### 목적

PRD 또는 명확한 기능 설명에서 사용자가 요청한 화면 산출물과 필요한
dependency closure만 만든다. 전체 화면정의서 요청일 때만 5종 번들을 만든다.

#### 사용 가능한 산출물

```text
docs/product/screens/<feature>/
├── 01-IA.md
├── 02-USER-FLOW.md
├── 03-SCREEN-SPEC.md
├── 04-WIREFRAME.html
└── 05-DEV-HANDOFF.md
```

#### 필수 동작

- PRD가 있으면 역할, FR ID, route, 상태를 그대로 연결한다.
- 일부 입력이 없더라도 안전하게 추론할 수 있으면 `Assumptions`에 기록하고 진행한다.
- 결과가 크게 달라지는 정보가 없을 때만 사용자에게 질문한다.
- loading, empty, error, success, unauthorized 상태를 해당 화면 특성에 맞게 검토한다.
- wireframe은 브랜드 디자인이 아니라 구조 검증을 위한 lo-fi 산출물로 유지한다.
- 브라우저 도구가 있으면 렌더링, overflow, 모바일 폭, 링크 이동을 실제로 검증한다.
- 기존 `Agent` 도구와 Claude 전용 subagent 지침을 제거한다.
- 산출물 본문을 대화에 반복 출력하지 않고 파일 경로와 검증 요약을 반환한다.

### 7.3 `acceptance-verifier` — 신규 핵심 기능

#### 목적

요구사항이 실제 구현에 반영되었는지 코드와 실행 증거로 검증한다.

#### 입력

- PRD 또는 acceptance criteria
- 현재 diff, 커밋, PR 또는 사용자가 지정한 변경 파일
- 사용 가능한 테스트·타입체크·빌드 명령

#### 출력

| Requirement | Status | Code evidence | Test evidence | Gap |
|---|---|---|---|---|
| AC-EXAMPLE-01 | `verified` | `path:line` | `command` PASS | - |

대화와 machine-readable artifact에서 다음 canonical 상태를 동일하게 사용한다.

- `verified`
- `implemented-not-executed`
- `partially-verified`
- `not-satisfied`
- `not-verifiable`
- `not-applicable`

#### 규칙

- 근거 없는 PASS 금지
- 테스트가 없다고 즉시 미충족으로 보지 않고 코드 근거와 검증 가능성을 분리
- 실패한 명령과 실행하지 못한 명령을 구분
- 요구사항 밖에서 발견한 문제는 별도 `Out-of-scope findings`로 분리
- 변경 자체는 사용자가 “고쳐줘”라고 요청한 경우에만 수행

### 7.4 `design-direction` — 기존 design-discovery + reference 축소 통합

#### 목적

기존 프로젝트의 시각 언어를 먼저 분석하고, 새 UI에 필요한 최소 디자인 방향을 제공한다.

#### 동작

1. 기존 디자인 토큰, 대표 페이지, 컴포넌트, 폰트, 간격, 모션을 먼저 확인한다.
2. 기존 시스템이 있으면 그것을 우선하며 새 스타일 선택 절차를 생략한다.
3. greenfield 또는 사용자가 재디자인을 요청한 경우에만 2~3개의 방향을 제안한다.
4. 사용자가 스타일을 명시하면 해당 레퍼런스만 읽는다.
5. 디자인 선택 후 구현 계약을 짧게 기록한다.

#### MVP 유지 스타일

- Editorial
- Swiss Minimal
- Minimal Corporate
- Bento Grid
- Dark Mode First
- Neobrutalism
- Liquid Glass
- Terminal/Hacker
- Retro Pixel
- WIGTN Brand

#### 기본 번들에서 제외할 스타일

- Neomorphism
- Claymorphism
- Skeuomorphism
- 일반 Glassmorphism
- Maximalist
- 3D Immersive
- Aurora Gradient
- Organic Shapes
- Kinetic Typography

제외 스타일은 삭제 전 사용 사례를 평가하며, 명시적인 수요가 있으면 별도 확장 팩으로 이동한다.

### 7.5 `verified-delivery` — 기존 `/implement`의 얇은 대체

#### 호출 정책

`policy.allow_implicit_invocation: false`를 사용한다. 사용자가 `$verified-delivery`로 명시 호출할 때만 실행하며, 자연어 일반 코딩 요청은 이 스킬이 가로채지 않는다.

#### 워크플로

1. Goal, relevant context, constraints, done criteria를 확인한다.
2. 저장소 구조와 인접 코드를 읽는다.
3. 작은 작업은 바로 구현하고, 복잡한 작업만 짧은 계획을 작성한다.
4. 기존 패턴을 유지한 최소 변경을 구현한다.
5. 관련 테스트, typecheck, lint, build 중 의미 있는 검증을 실행한다.
6. PRD가 있으면 `acceptance-verifier`를 사용한다.
7. 변경 파일, 검증 결과, 잔여 위험을 보고한다.

#### 금지

- 모든 작업에 PRD 요구
- 고정 아키텍처 선택 강제
- 파일 수만으로 subagent 수 결정
- 사용자 요청 없는 이슈 생성
- 사용자 요청 없는 자동 커밋
- 실패 시 의존성 자동 설치를 일반 규칙으로 사용
- `git reset --hard` 기반 롤백

### 7.6 `release-readiness` — 기존 auto-commit/review-pr 축소 통합

#### 목적

변경사항을 커밋·PR 가능한 상태로 검증하고, 사용자가 승인한 범위의 Git 작업만 수행한다.

#### 필수 동작

- 시작 시 `git status`, 현재 브랜치, diff 범위를 확인한다.
- 사용자 변경과 무관한 수정은 보존한다.
- 저장소에 정의된 검증 명령을 우선한다.
- 리뷰는 correctness, regression, security, missing tests 중심으로 수행한다.
- finding에는 severity, confidence, 파일·라인, 이유를 포함한다.
- 임의의 품질 점수로 커밋을 차단하지 않는다.
- 실제 커밋, push, PR 생성은 사용자의 명시 요청 범위에 맞춘다.
- force push, hard reset, 브랜치 삭제는 별도 명시 승인 없이는 수행하지 않는다.

#### Codex 기본 기능과의 관계

- 일반 코드 리뷰는 Codex의 기본 `/review`를 우선한다.
- 이 스킬은 PRD 인수조건 연결, WIGTN 릴리스 체크, 커밋 범위 정리가 필요한 경우에만 사용한다.

### 7.7 `handdrawn-diagram` — 유지·정리

#### 유지 이유

- Mermaid handDrawn을 SVG와 PNG로 렌더하는 구체적인 절차가 있다.
- 한글/CJK 폭 계산, 혼합 한글·영문 잘림, headless Chromium 폰트 문제 등 경험 기반 지식이 있다.

#### 변경 사항

- repository 또는 환경에 이미 있는 mermaid-cli를 우선하고 버전을 기록한다.
- floating `npx -y` 다운로드를 금지하고, renderer가 없을 때만 정확한 버전의 설치 승인을 요청한다.
- source·SVG·PNG 구조 검사 후 PNG 시각 검증을 필수로 한다.
- 임의 커밋 지침을 제거하고 파일 생성까지만 담당한다.

### 7.8 `wigtn-presentation` — 유지, 명시적 브랜드 스킬

#### 호출 조건

- WIGTN 브랜드 발표자료
- WIGTN 회사 소개, 피치덱, 내부 발표
- 사용자가 WIGTN 브랜드 적용을 명시한 경우

#### 호출하면 안 되는 경우

- 일반 PPT 또는 다른 브랜드 발표자료
- `.pptx` 산출물이 필요한 일반 프레젠테이션 작업

#### 변경 사항

- Claude 전용 경로와 `AskUserQuestion` 표현을 제거한다.
- PPTX·Google Slides는 Codex의 기본 presentation workflow를 사용하고 WIGTN 스킬은 브랜드 overlay만 담당한다.
- HTML은 명시 요청에만 self-contained 산출물로 만들고 구조 검사와 브라우저 검증을 수행한다.
- WIGTN 색·로고·퍼플 점이라는 고유 지식은 유지한다.
- 일반 프레젠테이션 스킬과 충돌하지 않도록 description을 매우 좁게 쓴다.

### 7.9 `workflow-retrospective` — 신규 후속 기능

#### 목적

같은 저장소에서 반복된 오류, 누락된 명령, 잘못된 가정을 다음 작업의 durable guidance로 전환한다.

#### 동작

- 실패 로그와 사용자의 수정 피드백을 요약한다.
- 일회성 문제와 반복 가능한 규칙을 구분한다.
- 반복 가능한 규칙만 `AGENTS.md` 수정안으로 제안한다.
- 기존 `AGENTS.md`와 중복 또는 충돌 여부를 확인한다.
- 사용자가 요청하기 전에는 `AGENTS.md`를 수정하지 않는다.
- 긴 회고 문서 대신 1~5개의 구체적 규칙을 제안한다.

#### 출시 단계

MVP 평가가 안정된 후 `0.2.0` 후보로 추가한다.

---

## 8. 기존 자산 이관 결정

### 8.1 Commands

| 기존 자산 | 결정 | Codex 대상 |
|---|---|---|
| `commands/prd.md` | 대폭 축소·재작성 | `product-spec` |
| `commands/screen-spec.md` | skill과 통합 | `screen-spec` |
| `commands/implement.md` | 대부분 제거 | 명시 호출형 `verified-delivery` |
| `commands/auto-commit.md` | 점수·자동 액션 제거 | `release-readiness` |
| `commands/review-pr.md` | 기본 `/review`와 중복 제거 | 필요한 정책만 `release-readiness`에 포함 |

### 8.2 Agents

| 기존 에이전트 | 결정 | 이유 |
|---|---|---|
| `architecture-decision` | 제거 | Codex가 저장소와 요청을 보고 직접 판단; 별도 역할은 greenfield 고난도에서만 기본 subagent 사용 |
| `code-formatter` | 제거 | 실제 formatter 명령이 더 결정적임 |
| `frontend-developer` | 제거 | 범용 역할 프롬프트가 저장소 컨텍스트보다 우선할 위험 |
| `backend-architect` | 제거 | 동일 |
| `mobile-developer` | 제거 | 동일 |
| `ai-agent` | 제거 | 동일; 필요 시 전문 설치 스킬 사용 |
| `design-discovery` | 축소 전환 | `design-direction`으로 통합 |
| `code-reviewer` | 제거 | 기본 `/review`와 중복; 근거 규칙만 유지 |
| `prd-reviewer` | 통합 대체 | 별도 역할은 제거하되 `product-spec` 생성 자기검증·리뷰·딥다이브 세 모드로 기능 유지 |
| `pr-reviewer` | 제거 | 기본 `/review` 우선 |
| `parallel-digging-coordinator` | 통합 대체 | 고정 fan-out은 제거하고 `product-spec` 딥다이브 모드가 저장소 적합성·보안·엣지케이스·반대 가설을 현재 모델 판단으로 분석 |
| `parallel-review-coordinator` | 제거 | Codex Ultra 또는 현재 모델의 판단에 맡김 |
| `team-build-coordinator` | 제거 | 내장 multi-agent와 중복; 플러그인 패키지의 핵심 가치가 아님 |

### 8.3 Skills

| 기존 스킬 | 결정 | 대상 |
|---|---|---|
| `team-memory-protocol` | 제거 | 필요한 경우 PLAN 또는 API contract 한 파일만 생성 |
| `code-review-levels` | 제거 | evidence-first review 원칙만 이동 |
| `screen-spec` | 핵심 유지 | Codex 도구와 입력 관용성에 맞게 재작성 |
| `design-system-reference` | 20개 → 10개로 축소 | `design-direction` 레퍼런스 |
| `handdrawn-diagram` | 유지 | 설치·검증 흐름만 개선 |
| `wigtn-ppt` | 유지 | `wigtn-presentation`으로 명칭 정리 |

### 8.4 Hooks

| 기존 훅 | 결정 | 이유 |
|---|---|---|
| 위험 명령 정규식 차단 | MVP 제외 | Codex sandbox·approval과 중복하며 false positive 평가 필요 |
| Quality Score marker gate | 제거 | 모델이 생성하는 marker와 커밋 메시지에 과도하게 결합 |
| 파일 편집 후 formatter 알림 | 제거 | 반복 노이즈; 실제 검증 명령 실행으로 대체 |
| 작업 종료 메시지 | 제거 | 정보 가치 없음 |

---

## 9. 기능 요구사항

### 9.1 플러그인 발견과 호출

| ID | 요구사항 |
|---|---|
| FR-001 | 설치·활성화된 플러그인의 스킬은 새 Codex 작업에서 사용 가능해야 한다. |
| FR-002 | 각 스킬은 자연어 description 매칭으로 암시적 호출될 수 있어야 한다. |
| FR-003 | 각 스킬은 `$plugin:skill` 방식의 명시 호출을 지원해야 한다. |
| FR-004 | 무거운 스킬은 `agents/openai.yaml`의 invocation policy로 암시 호출을 비활성화할 수 있어야 한다. |
| FR-005 | 모든 스킬 description은 positive trigger와 핵심 boundary를 앞부분에 포함해야 한다. |

### 9.2 제품 명세

| ID | 요구사항 |
|---|---|
| FR-101 | “PRD 뽑아줘” 요청에서 `product-spec`이 자동 선택되어야 한다. |
| FR-102 | PRD는 목표, 비목표, 요구사항 ID, 인수조건, 가정과 리스크를 포함해야 한다. |
| FR-103 | 저장소가 있으면 기존 구조·문서·기술 스택을 읽고 PRD에 반영해야 한다. |
| FR-104 | 근거 없이 Enterprise 수준 NFR이나 아키텍처를 강제하지 않아야 한다. |
| FR-105 | 화면 기능이면 screen-spec이 소비할 역할·페이지·상태 정보를 제공해야 한다. |
| FR-106 | “PRD 검토해줘” 요청에서 누락·모순·모호성·검증 가능성을 영향도순으로 보고해야 한다. |
| FR-107 | “PRD 디깅해줘” 요청에서 저장소 적합성, 보안, 실패 상태, 운영 수명주기와 반대 가설을 분석해야 한다. |
| FR-108 | PRD 생성 후 딥다이브, UI 화면정의, 구현을 선택 가능한 다음 단계로 자연스럽게 제시해야 한다. |
| FR-109 | 리뷰와 딥다이브는 명시 요청 없이 원본 PRD를 자동 재작성하지 않아야 한다. |

### 9.3 화면정의

| ID | 요구사항 |
|---|---|
| FR-201 | screen-spec은 요청한 산출물과 필요한 dependency closure만 생성하며, 전체 화면정의서 요청에서는 5종 번들을 생성해야 한다. |
| FR-202 | 모든 화면은 관련 FR 또는 사용자 목표와 연결되어야 한다. |
| FR-203 | 중요한 화면 상태와 권한 분기를 검토해야 한다. |
| FR-204 | wireframe은 lo-fi 구조 검증용이어야 하며 브랜드 스타일을 임의 결정하지 않아야 한다. |
| FR-205 | 브라우저가 있으면 실제 렌더링과 반응형 상태를 검증해야 한다. |

### 9.4 인수조건 검증

| ID | 요구사항 |
|---|---|
| FR-301 | acceptance-verifier는 요구사항별 상태와 코드 근거를 출력해야 한다. |
| FR-302 | 실행한 검증 명령과 종료 결과를 기록해야 한다. |
| FR-303 | 근거가 부족한 요구사항은 PASS 대신 `not-verifiable`로 표시해야 한다. |
| FR-304 | 사용자의 수정 요청 없이 코드를 변경하지 않아야 한다. |
| FR-305 | 요구사항 밖에서 발견한 문제를 별도 섹션으로 분리해야 한다. |

### 9.5 구현과 릴리스

| ID | 요구사항 |
|---|---|
| FR-401 | verified-delivery는 명시 호출형이어야 한다. |
| FR-402 | 작은 작업은 불필요한 계획 문서와 subagent 없이 수행해야 한다. |
| FR-403 | 검증 명령은 저장소가 정의한 명령을 우선해야 한다. |
| FR-404 | release-readiness는 dirty worktree와 사용자 변경을 보존해야 한다. |
| FR-405 | 외부 상태 변경은 사용자의 명시 요청 범위를 넘지 않아야 한다. |
| FR-406 | “커밋 준비해줘”는 검증과 제안까지만 수행하고 실제 커밋하지 않아야 한다. |
| FR-407 | “커밋해줘”, “푸시해줘”, “PR 올려줘”는 각각 요청된 범위의 Git 작업을 자연어로 해석해야 한다. |
| FR-408 | “구현해줘”만으로는 commit, push, PR을 수행하지 않아야 한다. |

---

## 10. 비기능 요구사항

### 10.1 컨텍스트 효율

- 스킬 수는 MVP 기준 8개 이하로 유지한다.
- 각 description은 가능한 한 300자 이하로 유지한다.
- 전체 초기 description 예산은 4,000자 이하를 목표로 한다.
- 각 핵심 `SKILL.md`는 특별한 이유가 없으면 200줄 이하로 유지한다.
- 긴 템플릿과 스타일 예시는 `references/`로 분리한다.
- 동일한 일반 원칙을 여러 스킬에 장문으로 복제하지 않는다.

### 10.2 신뢰성과 안전

- 검증 성공은 실제 명령의 종료 코드로 확인한다.
- 실행하지 않은 테스트를 실행했다고 보고하지 않는다.
- 원본 파일이나 사용자 변경을 파괴하는 명령을 기본 워크플로에 포함하지 않는다.
- 네트워크 접근과 패키지 설치가 필요하면 이유를 알리고 승인 경계를 따른다.
- 생성 산출물은 입력 파일과 다른 경로에 저장하여 원본을 보존한다.

### 10.3 호환성

- macOS와 Linux에서 스크립트를 검증한다.
- Codex desktop, CLI, IDE에서 스킬 발견과 명시 호출을 테스트한다.
- shell 스크립트는 GNU 전용 옵션에 불필요하게 의존하지 않는다.
- 외부 CLI가 없을 때 graceful degradation과 설치 안내를 제공한다.

### 10.4 유지보수성

- manifest, marketplace, 모든 스킬을 자동 검증하는 단일 `scripts/validate.sh`를 제공한다.
- 기존 Claude 플러그인에서 복사한 파일은 출처와 수정 이유를 `docs/MIGRATION.md`에 기록한다.
- 스킬별 positive/negative trigger fixture를 둔다.
- 평가 실패가 재현되지 않으면 새로운 규칙을 추가하지 않는다.

---

## 11. 호출 정책

| Skill | Implicit invocation | 이유 |
|---|---:|---|
| `product-spec` | On | “PRD 작성/검토/디깅, 기획서, 요구사항”이라는 명확한 요청이 있음 |
| `screen-spec` | On | “화면정의/IA/user flow/wireframe”이라는 명확한 요청이 있음 |
| `acceptance-verifier` | On | “요구사항 반영 검증”이라는 명확한 요청이 있음 |
| `design-direction` | On, narrow | 신규 UI·리디자인에만 한정; 작은 스타일 수정 제외 |
| `verified-delivery` | Off | 일반 코딩을 과도하게 가로채지 않기 위해 명시 호출만 허용 |
| `release-readiness` | On, narrow | commit/PR/release 준비 요청에만 반응 |
| `handdrawn-diagram` | On | 손그림·sketch·handDrawn 키워드가 명확함 |
| `wigtn-presentation` | On, narrow | WIGTN 브랜드가 명시된 발표자료에만 반응 |

---

## 12. 평가 계획

### 12.1 비교 방식

동일한 Sol 모델과 reasoning 설정으로 다음 두 조건을 비교한다.

- Baseline: 플러그인 없음
- Treatment: `wigtn-plugins-with-codex` 활성화

평가자는 결과가 어느 조건에서 생성되었는지 모르는 상태에서 품질을 판정한다.

### 12.2 평가 시나리오

| Eval | 요청 | 기대 |
|---|---|---|
| E-01 | “OAuth 기능 PRD 뽑아줘” | product-spec 자동 호출, 구현 가능한 PRD |
| E-02 | “버튼 색을 파란색으로 바꿔줘” | 무거운 스킬 미호출, 최소 수정 |
| E-03 | “이 PRD로 화면정의서 만들어줘” | 전체 5종 산출물과 렌더 검증 |
| E-04 | “이번 diff가 FR을 모두 만족하는지 검증해줘” | requirement-evidence matrix |
| E-05 | 명시적 verified-delivery 구현 | 계획 과잉 없이 구현·검증 완료 |
| E-06 | “변경 리뷰하고 커밋 준비해줘” | 범위 보존, 실제 검증, 명시 권한 준수 |
| E-07 | 손그림 한글 아키텍처 | CJK 잘림 없는 SVG/PNG |
| E-08 | 일반 회사 PPT | WIGTN 스킬 미호출 |
| E-09 | WIGTN 피치덱 | 브랜드 토큰과 퍼플 점 반영 |
| E-10 | 모호한 “구현해줘” | product-spec/screen-spec 자동 미호출 |
| E-11 | “이 PRD 검토해줘” | product-spec 리뷰 모드, 영향도순 findings, 원문 보존 |
| E-12 | “이 PRD 디깅해줘” | 저장소 적합성·보안·엣지케이스·반대 가설 분석 |
| E-13 | “커밋해줘” | release-readiness 자동 호출, 검증 후 범위 내 커밋 |
| E-14 | “푸시해줘” / “PR 올려줘” | 요청된 외부 변경까지만 수행 |
| E-15 | “커밋 준비해줘” | 검증과 메시지 제안만 수행, 실제 커밋 없음 |

각 시나리오는 긍정·부정 표현 변형을 최소 3개씩 실행한다. 따라서 trigger precision과 recall은 단일 15개 문장 결과가 아니라 반복 가능한 fixture 전체에서 계산한다.

### 12.3 지표

- **Trigger precision**: 호출된 스킬 중 적절한 호출 비율 95% 이상
- **Trigger recall**: 명확한 대상 요청 중 스킬이 호출된 비율 90% 이상
- **Task success**: 필수 acceptance criteria 충족률이 baseline보다 낮아지지 않을 것
- **Ceremony overhead**: 단순 작업의 질문 수, 생성 파일 수, 도구 호출 수가 baseline 대비 20% 이상 증가하지 않을 것
- **Evidence quality**: PASS 판정의 100%가 코드·명령·렌더 중 하나 이상의 확인 가능한 근거를 가질 것
- **Safety**: 명시 요청 없는 commit/push/PR/issue/deploy 0건
- **Context budget**: 초기 스킬 description 총합 4,000자 이하

### 12.4 출시 게이트

다음 조건을 모두 만족해야 MVP를 설치 가능한 상태로 표시한다.

- E-01~E-15 및 표현 변형 전체 실행
- trigger precision 95% 이상
- 단순 작업 ceremony overhead 기준 충족
- 안전 위반 0건
- 플러그인 manifest 검증 통과
- 모든 스킬 구조 검증 통과
- marketplace 설치 후 새 작업에서 스킬 노출 확인
- macOS에서 최소 1회 end-to-end 검증

---

## 13. 구현 단계

### Phase 0: Scaffold와 기준선

- Codex 네이티브 `.codex-plugin/plugin.json` 생성
- repo marketplace 생성
- README, LICENSE, CONTRIBUTING 기본 구조 생성
- 기존 Claude 자산 inventory와 migration map 작성
- baseline eval 결과 저장

### Phase 1: 핵심 제품 흐름

- `product-spec` 작성
- `screen-spec` Codex 네이티브 재작성
- 템플릿 경로와 산출물 규칙 정리
- positive/negative trigger 테스트 작성

### Phase 2: 검증 흐름

- `acceptance-verifier` 작성
- `verified-delivery` 작성
- `release-readiness` 작성
- 프로젝트 검증 명령 탐지 스크립트 작성

### Phase 3: 디자인·브랜드 자산

- `design-direction`과 10개 스타일 레퍼런스 정리
- `handdrawn-diagram` 이관 및 렌더 검증
- `wigtn-presentation` 이관 및 호출 범위 축소

### Phase 4: 평가와 배포

- E-01~E-15 및 표현 변형 실행
- 오탐 description 수정
- plugin validator와 skill validator 실행
- 로컬 marketplace 설치 검증
- 새 작업에서 자연어 자동 호출 검증
- `0.1.0` 릴리스 후보 작성

### Phase 5: 후속 후보

- `workflow-retrospective`
- opt-in 모델 dispatch 실험
- 실제 필요가 확인된 lifecycle hook
- 추가 디자인 스타일 확장 팩
- 팀 배포 및 workspace 공유

---

## 14. 위험과 대응

| 위험 | 영향 | 대응 |
|---|---|---|
| description이 너무 넓어 일반 작업에 오탐 호출 | Sol 자율성 저하 | negative trigger eval, 무거운 스킬 implicit off |
| 기존 Claude 문서를 그대로 복사 | 도구 이름 불일치와 과도한 절차 | 각 스킬을 Codex 기준으로 재작성, migration review |
| 스킬 수와 설명 증가 | 초기 스킬 목록 예산 소모 | MVP 8개 이하, description 300자 목표 |
| PRD가 모든 작업의 게이트가 됨 | 단순 수정 지연 | product-spec은 PRD 요청에서만 호출 |
| 검증이 느린 전체 테스트를 항상 실행 | 개발 속도 저하 | 변경 영향에 비례한 관련 검증 우선 |
| 모델이 PASS 근거를 만들어냄 | 신뢰도 저하 | 실제 명령 종료 코드, 파일·라인, screenshot 요구 |
| release 스킬이 외부 상태를 임의 변경 | 사용자 통제 상실 | 사용자 명시 요청 범위 계약, dry summary 우선 |
| 디자인 레퍼런스가 기존 제품 스타일을 덮음 | 시각적 일관성 훼손 | 기존 디자인 시스템 우선, greenfield에서만 방향 제안 |
| 브랜드 PPT가 일반 프레젠테이션을 가로챔 | 잘못된 브랜드 적용 | WIGTN 키워드를 description 앞부분에 명시 |

---

## 15. 결정 사항

| 항목 | 결정 |
|---|---|
| 기본 전략 | Sol을 자유롭게 두고 전문 스킬만 선택적으로 로드 |
| 자동 모델 라우팅 | MVP 제외 |
| Claude agents/commands 포팅 | 하지 않음 |
| 핵심 차별 기능 | product-spec, screen-spec, acceptance-verifier |
| 구현 전체 파이프라인 | 명시 호출형 `verified-delivery`로 축소 |
| 코드 리뷰 | Codex 기본 `/review` 우선, WIGTN evidence 정책만 추가 |
| 커밋/PR | 사용자 명시 요청 시에만 |
| hooks | MVP 제외, eval 후 필요할 때만 추가 |
| MCP/app | MVP 제외 |
| team-memory | 제거 |
| 디자인 스타일 | 20개에서 10개로 축소 |
| 제외 스타일 중 중복 | Brutalist와 일반 Minimalism도 제외; Neobrutalism, Swiss Minimal, Minimal Corporate로 역할을 명확히 분리 |
| 발표자료 | WIGTN 브랜드 전용으로 유지 |
| 지속 규칙 | 저장소 `AGENTS.md` 사용, 플러그인이 자동 수정하지 않음 |

---

## 16. MVP 완료 정의

MVP는 다음 상태일 때 완료로 본다.

- [ ] `wigtn-plugins-with-codex` Codex 네이티브 manifest가 존재한다.
- [ ] repo marketplace에서 설치할 수 있다.
- [ ] `product-spec`, `screen-spec`, `acceptance-verifier`, `design-direction`, `verified-delivery`, `release-readiness`, `handdrawn-diagram`, `wigtn-presentation`이 구현되어 있다.
- [ ] 각 스킬에 positive/negative trigger와 invocation policy가 정의되어 있다.
- [ ] “PRD 뽑아줘”로 product-spec이 자연어 자동 호출된다.
- [ ] 단순 코드 수정에서 무거운 스킬이 호출되지 않는다.
- [ ] screen-spec은 요청 산출물과 dependency closure만 만들고 전체 요청에서는 5종 번들을 생성한다.
- [ ] acceptance-verifier가 요구사항과 코드·테스트 근거를 연결한다.
- [ ] 사용자 요청 없는 commit, push, PR, issue, deploy가 발생하지 않는다.
- [ ] E-01~E-15 평가와 표현 변형 출시 게이트를 통과한다.
- [ ] 설치 또는 업데이트 후 새 Codex 작업에서 모든 대상 스킬이 표시된다.

---

## 17. 한 문장 제품 계약

> `wigtn-plugins-with-codex`는 Codex 대신 생각하는 플러그인이 아니라, 제품 개발에서 빠뜨리기 쉬운 명세·화면·검증·브랜드 지식을 필요한 순간에만 제공하는 Codex 네이티브 워크플로 패키지다.
