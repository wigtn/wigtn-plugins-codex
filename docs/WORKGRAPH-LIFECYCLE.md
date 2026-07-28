# WorkGraph lifecycle

## 의미

WIGTN의 lifecycle은 모델 호출 절차가 아니다. 제품 요구사항이 생성된 뒤
구현·검증·릴리스를 거쳐 변경되거나 폐기될 때까지, 각 상태와 근거의 연결을
보존하는 데이터 계약이다.

```text
requirement
  ├─ product/screen artifact
  └─ implementation task
       ├─ dependency task
       └─ executable check
             └─ release gate
```

이 계약이 해결해야 하는 실패는 다음과 같다.

- 요구사항이 바뀌었는데 이전 테스트 결과를 계속 `verified`로 사용한다.
- 구현은 끝났지만 어떤 요구사항을 충족했는지 찾을 수 없다.
- 선행 작업이 끝나지 않았는데 후속 작업을 실행한다.
- 화면정의와 구현 task의 requirement ID가 달라진다.
- release 준비 상태를 commit·push 권한으로 잘못 해석한다.
- 중단 후 재개할 때 완료·차단·stale 작업을 다시 추측한다.

## 상태 책임

| Node | 상태가 답하는 질문 |
|---|---|
| Source | 어떤 원본과 SHA-256을 기준으로 했는가 |
| Requirement | 원본 요구사항이 현재 유효한가 |
| Artifact | PRD·화면·handoff가 현재 요구사항과 일치하는가 |
| Task | 구현이 어느 단계이며 무엇에 의존하는가 |
| Check | 어떤 명령이 실제로 어떤 증거를 만들었는가 |
| Release gate | 필요한 task가 검증됐는가 |

task의 정상 전이는 다음과 같다.

```text
draft → ready → in-progress → implemented → verified
                  └──────→ blocked
any active state → stale
```

- `ready`: 실제 scope·check가 있고 모든 dependency가 `verified`.
- `implemented`: 구현 증거는 있지만 실행 검증이 아직 부족할 수 있음.
- `verified`: linked passing check와 evidence reference가 모두 존재.
- `stale`: source, artifact, requirement, dependency 또는 check가 바뀌어
  이전 판정을 신뢰할 수 없음.
- `blocked`: 구체적인 blocker가 기록됨.

## 선택적 사용

일반 버그 수정이나 대화형 체크리스트에는 WorkGraph를 만들지 않는다. 사용자가
저장형 구현 계획, 세션 간 handoff, resume, requirement 추적을 요청했을 때만
`.wigtn/workgraph.json`을 만든다.

`work-planner`는 계획만 담당한다. `verified-delivery`의 명시 호출만 구현을
허용하고, `acceptance-verifier`가 실행 증거를 평가하며,
`release-readiness`는 사용자가 별도로 부여한 Git 권한만 수행한다.

## 결정론적 보장

현재 contract suite는 다음을 포함한 67개 케이스를 검사한다.

- schema와 stable ID
- cross-reference와 dependency DAG
- unsafe path와 path traversal
- false `verified`와 evidence/check backlink
- source drift의 task·check·gate 전파
- 관련 없는 node 비오염
- dry-run과 반복 apply idempotency
- legacy migration과 atomic write
- CLI init/import/plan/status/next/diff/doctor
- task refinement/dependency dry-run, idempotency, revision conflict, cycle

이 검사는 lifecycle 엔진의 상태 무결성을 입증한다. 모델이 더 좋은 PRD나
코드를 만든다는 증거는 아니며, 그 주장은 별도의 locked task benchmark와
blind 평가가 필요하다.
