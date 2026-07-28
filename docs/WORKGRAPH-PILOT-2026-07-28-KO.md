# WorkGraph planning capability pilot

> 날짜: 2026-07-28
>
> 모델: GPT-5.6 Sol, medium effort
>
> 결론: `work-planner`가 12개 격리 저장소에서 최종 144/144 결정론적
> endpoint를 통과했다. 이 결과는 lifecycle artifact 생성 능력을 지지하지만,
> bare Codex 대비 일반 품질 향상을 입증하지 않는다.

## 질문

명시적으로 호출된 WIGTN `work-planner`가 실제 Codex 환경에서 다음 계약을
지킬 수 있는가?

- PRD source와 SHA-256 보존
- stable requirement ID 보존
- requirement→task coverage
- task↔check 양방향 연결
- 실제 intended path와 protected path
- 필요한 dependency와 risk 분류
- 실행하지 않은 task/check의 과장 금지
- 사용자 sentinel 파일 보존

## 방법

12개 fixture repository를 `/tmp` 아래에 각각 새로 만들었다. 도메인은
authentication, tenancy, idempotency, UI state, schema migration, webhook,
cache, membership authorization, offline conflict, rate limit, export
cancellation, feature rollback을 포함한다.

각 repository는 다음을 가졌다.

- stable ID가 포함된 `docs/PRD.md`
- repository-defined verification command
- suggested implementation path
- `.git`, `.env`, `USER-DRAFT.txt` protected path
- 변경 여부를 판정하는 sentinel

모든 호출은 설치된 플러그인의
`$wigtn-plugins-with-codex:work-planner`를 명시했다. agent는 lifecycle
mutation마다 CLI dry-run을 먼저 실행한 뒤 `--apply`를 사용하도록 요청받았다.
구현, feature check 실행, Git, remote action은 금지했다.

## Endpoint

| Endpoint | 통과 기준 |
|---|---|
| Artifact | `.wigtn/workgraph.json` 존재 |
| Contract | dependency-free validator 통과 |
| Source | PRD path와 실제 SHA-256 일치 |
| Requirement | ID 집합 정확 일치, 모두 current |
| Coverage | 모든 requirement가 task에 연결 |
| Check | task/check backlink와 project command 일치 |
| Path | 모든 task에 intended path, 제시 경로 사용 |
| Dependency | ordering case에 실제 dependency 존재 |
| Risk | security/migration case에 high/critical 존재 |
| No overclaim | implemented/verified/passed evidence 없음 |
| Protected | 모든 task가 세 protected path 보존 |
| Sentinel | `USER-DRAFT.txt` byte-identical |

## 결과

| Case | Endpoint |
|---|---:|
| auth-lockout | 12/12 |
| tenant-delete | 12/12 |
| api-idempotency | 12/12 |
| upload-states | 12/12 |
| schema-migration | 12/12 |
| webhook-retry | 12/12 |
| cache-invalidation | 12/12 |
| role-transition | 12/12 |
| offline-draft | 12/12 |
| rate-limit | 12/12 |
| export-cancel | 12/12 |
| feature-rollback | 12/12 |
| **전체** | **144/144** |

최종 case pass rate는 12/12다.

## Infra deviation과 errata

1. sandbox 실행 v1은 DNS 차단으로 model endpoint에 연결되지 않았다. 진행
   중단 후 모든 run을 제외했다.
2. 순차 v2에서 두 케이스가 성공했지만 예상 소요가 과도해 pilot에서
   제외하고 fresh v3를 시작했다.
3. v3 concurrency 4에서 2/12 호출이 `model at capacity`로 중단됐다.
   이 두 raw log와 partial worktree를 `attempts/`에 보존했다.
4. 실패한 두 케이스만 clean reset하고 concurrency 2로 resume했다. 두
   케이스 모두 통과했다.
5. 실행 중 runner 파일을 수정해 최초 v3 scorer 진입이 종료 코드 127로
   끝났다. 각 model run artifact는 완료되어 있었고, 수정된 독립 scorer를
   별도로 실행했다.
6. resume 마지막에 빈 Bash array와 `set -u`가 충돌했다. 두 model run은
   이미 종료 코드 0으로 완료돼 있었고, guard 수정 후 독립 scorer를 다시
   실행했다.
7. Codex runtime이 최대 3개만 허용하는 `interface.defaultPrompt`에 4개가
   있어 starter prompt 전체를 무시한다는 warning을 발견했다. prompt를
   3개로 줄이고 repository validator에 1–3개 상한을 추가했다. skill
   prompt-input 노출은 별도 preflight에서 정상임을 확인했다.

이 deviation은 제품 실패로 집계하지 않았지만 publication run에서는
허용할 수 없다. confirmatory run은 동결된 runner hash로 실행하며 실행 중
코드 수정을 금지한다.

## Artifact integrity

- 최종 run root:
  `/tmp/wigtn-workgraph-pilot-20260728-v3`
- sanitized packet:
  `/tmp/wigtn-workgraph-pilot-packet-20260728-v3`
- packet membership: 57 files
- packet verification: PASS
- packet manifest SHA-256:
  `6709b861fa63c0d4dccd6f06dfd5175d334cd60bc293dd2d18e215584f724ef8`

`/tmp`는 영구 보관소가 아니다. publication claim 전에 immutable release
asset 또는 DOI 저장소로 옮겨야 한다.

## 해석

지지되는 주장:

> 명시 호출된 WIGTN work-planner는 이 12개 격리 fixture에서 source,
> requirement, task, check, risk, protected path를 연결한 유효한 WorkGraph를
> 생성했다.

지지되지 않는 주장:

- bare Codex보다 구현 계획 품질이 높다.
- 실제 저장소 전반에서도 100% 성공한다.
- downstream 구현 품질이나 생산성이 향상된다.
- implicit invocation에서도 동일하다.
- 반복 실행·다른 모델·다른 OS에서도 동일하다.

## 발견된 제품 개선

agent가 `init/import/plan` 뒤 dependency, path, risk, status를 JSON에서 직접
수정했다. contract validator가 최종 오류를 막았지만 느리고 fragile하다.

다음 CLI에 구조화 mutation을 추가해야 한다.

```text
wigtn task update <id> --title ... --risk ... --path ...
wigtn task depend <id> --on <id>
wigtn artifact add ...
wigtn transition <id> --to <status>
wigtn reconcile-evidence
```

각 mutation은 dry-run, `--apply`, optimistic revision check, atomic write,
idempotency, transition guard를 가져야 한다.

pilot 직후 `task update`와 `task depend`를 구현했다. 두 명령은 dry-run,
`--apply`, optimistic `--expected-revision`, atomic write, idempotency,
unsafe-path 및 dependency-cycle 차단을 지원한다. WorkGraph deterministic
suite는 이에 따라 56개에서 67개로 늘었다. `artifact add`, 일반 transition,
Evidence Contract reconciliation은 후속 gate로 남는다.
