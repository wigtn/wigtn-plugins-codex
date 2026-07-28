# GPT-5.6 Sol 일반 코딩 비간섭 게이트

> 실행일: 2026-07-28
> 상태: development gate PASS
> 허용되는 결론: 현재 full9 후보가 이 12개 합성 태스크에서 bare Codex의
> 일반 코딩을 방해했다는 증거는 발견되지 않았다.
> 금지되는 결론: 플러그인이 일반 코드 품질이나 효율을 향상시킨다.

## 왜 이 실험을 했나

WIGTN은 PRD, acceptance verification, verified delivery, release safety,
WorkGraph 같은 선택적 수명주기 기능을 제공한다. 강한 기본 모델에 이
카탈로그를 추가하면 ordinary coding에서도 무거운 절차를 잘못 시작하거나,
정답률·변경 범위·비용을 악화시킬 수 있다. 따라서 새로운 기능의 capability
검증과 별도로 **비간섭 진입 게이트**를 두었다.

## 동결된 프로토콜

- model: `gpt-5.6-sol`
- reasoning effort: `medium`
- arms:
  - `bare`: 플러그인 없음
  - `core4`: product-spec, acceptance-verifier, verified-delivery,
    release-readiness
  - `full8`: 현재 후보에서 work-planner만 제거한 component ablation
  - `full9`: 현재 9-skill 후보
- corpus: Python 4, JavaScript 4, Ruby 4의 합성 bug-fix 12개
- execution: arm별 격리 `CODEX_HOME`, 원격 플러그인·앱 비활성화,
  독립 worktree, seed 고정 paired randomized schedule, 동시성 2
- grader: 실행 전 숨긴 테스트, baseline file hash, protected sentinel,
  unsolicited lifecycle artifact detector
- repetitions: task/arm당 1회, 총 48회
- infrastructure retry: capacity/network로 분류되는 비정상 종료만 최대
  1회 허용하고 원 worktree를 archive한 뒤 초기화

실행 전 코퍼스 자체에 대해 다음 세 조건을 모두 확인했다.

1. 공개 테스트는 결함 fixture에서도 통과한다.
2. 숨은 테스트는 결함 fixture를 실패시킨다.
3. 기준 수정안을 적용하면 공개·숨은 테스트가 모두 통과한다.

Go 태스크도 처음 검토했으나 로컬 Homebrew Go 1.26.3이 `testing` 등
표준 라이브러리를 찾지 못하는 환경 self-test 실패를 보였다. 모델 실패와
섞지 않기 위해 실행 전에 Ruby로 대체했고, 이후 12개 코퍼스를 다시
동결·검증했다. Go 결과는 본 분석에 포함하지 않았다.

## 사전 판정 기준

full9는 아래를 모두 만족해야 PASS다.

1. 예정된 실행과 schedule metadata가 모두 존재한다.
2. bare가 통과한 hidden-test pair를 full9가 하나도 악화시키지 않고,
   전체 hidden pass rate가 bare 이상이다.
3. `.wigtn`, PRD, screen spec, release evidence 등 요청하지 않은
   lifecycle state를 만들지 않는다.
4. 허용 파일 밖 변경률이 bare보다 나쁘지 않다.
5. `USER-DRAFT.txt` sentinel을 100% 보존한다.
6. median total-token overhead가 bare 대비 10% 이하이다.

지연 시간은 cloud serving noise의 영향을 크게 받으므로 기록은 하되 이
파일럿의 합격 조건으로 사후 추가하지 않았다.

## 결과

모델 호출 48/48이 정상 종료했고 infrastructure retry는 0회였다.

| Arm | Hidden | 전체 endpoint | Scope clean | 불필요한 state 없음 | Median tokens | Median duration |
|---|---:|---:|---:|---:|---:|---:|
| bare | 12/12 | 12/12 | 12/12 | 12/12 | 19,070.0 | 40.0s |
| core4 | 12/12 | 12/12 | 12/12 | 12/12 | 14,058.0 | 45.5s |
| full8 | 12/12 | 12/12 | 12/12 | 12/12 | 15,547.0 | 39.0s |
| full9 | 12/12 | 12/12 | 12/12 | 12/12 | 17,103.5 | 47.5s |

bare와 paired hidden-test 결과는 core4/full8/full9 모두 improved 0,
harmed 0, tied-pass 12였다. full9 token median은 bare보다 10.3% 낮아
사전 guardrail을 통과했다. 반면 duration median은 18.8% 높았다.
태스크별 paired token은 full9가 bare보다 낮은 경우 6개, 높은 경우
6개였고 paired difference 중앙값은 -1,847.5 token이었다. duration의
paired difference 중앙값은 +4.5초였다.
표본이 작고 cloud latency가 통제되지 않았으므로 어느 쪽도 효율 향상이나
저하의 증거로 해석하지 않는다.

추가 audit에서 기존 scheduler가 각 pair의 arm 순서를 seed로
무작위화했지만 작은 표본에서 위치를 정확히 균형화하지는 않았음을
확인했다. full9의 pair 내 1·2·3·4번째 위치는 각각 4·1·4·3회였다.
correctness는 전 arm 12/12라 본 gate 판정을 바꾸지 않지만 latency/token
비교에는 잠재적 교란이다. confirmatory 실행 전 scheduler를 block-wise
cyclic rotation으로 수정하고, 4-arm/12-pair fixture에서 각 arm이 각
위치에 정확히 3회 놓이는 회귀 검사를 추가했다. 본 파일럿 수치는 기존
동결 schedule의 결과로 그대로 보존했다.

## 냉정한 판정

**과도한 하네스라는 신호는 이 파일럿에서 발견되지 않았다.** full9가
ordinary coding 요청에서 WorkGraph나 PRD를 멋대로 만들지 않았고, hidden
correctness·scope·sentinel을 악화시키지 않았다. 따라서 현재 후보를 더 큰
비간섭 검증으로 보내는 engineering gate는 통과했다.

하지만 모든 arm이 12/12를 기록해 ceiling effect가 크다. 0/12 harmed는
회귀율이 0이라는 뜻이 아니다. 단순 rule-of-three 근사로도 관측되지 않은
위험의 95% 상한은 약 25%다. 이 결과만으로 “모든 실제 저장소에서
동일하다”, “플러그인이 품질을 높인다”, “토큰을 절감한다”는 문구를 쓰면
과장이다.

또한 `full8`은 역사적 v0.2 릴리스가 아니라 동일 후보에서
`work-planner` catalog/skill만 제거한 component ablation이다. 이 비교는
WorkGraph 노출의 증분 비간섭을 보는 데는 유효하지만 과거 버전과의 회귀
비교는 아니다.

## 다음 confirmatory gate

다음 단계는 결과를 본 뒤 같은 문제를 반복하는 것이 아니라 별도 hash로
동결한 held-out bank여야 한다.

- 최소 30개 태스크, Python/JavaScript/Ruby 각 10개
- boundary, state machine, parsing/serialization, path/security,
  async/concurrency, multi-file integration을 난이도별 층화
- 공개 테스트만으로 정답이 드러나지 않는 hidden grader
- task/arm당 최소 3회, task를 분석 단위로 한 paired bootstrap과
  improved/harmed discordance 공개
- block-wise cyclic arm rotation으로 실행 위치를 정확히 균형화
- primary comparison은 bare vs full9, core4/full8은 component secondary
- 실제 OSS issue snapshot 또는 허가된 실제 저장소 태스크를 별도 층으로
  추가
- correctness 외 scope violation, unsolicited state, token, wall time을
  각각 보고하고 합성 점수 하나로 숨기지 않음

현재 결과는 confirmatory 실행의 타당성을 지지하지만, publication-level
일반화나 품질 향상 claim을 지지하지 않는다.

## 재현 자료

- local run root: `/tmp/wigtn-ordinary-gate-20260728-v1`
- sanitized packet: `/tmp/wigtn-ordinary-gate-packet-20260728-v1`
- packet files: 234
- packet manifest SHA-256:
  `625ab4d391aaf83a93cbf7b54a6ad99d9f6aab18a5f4c417643c8bb803f5bb94`
- frozen run manifest SHA-256:
  `a4c9815a9c67c2c688aaa070e0792e027a9b49e1488feb38e69755bba62ce2ba`
- result JSON SHA-256:
  `029f5daa1e5acc4a1dc1050f58b15a92dff1d5987886410f9ab2bb9a6ddca6e2`

`scripts/export-eval-packet.py`로 worktree, Codex home, staging,
prompt-input을 제외하고 경로·secret을 정리했으며
`scripts/verify-eval-packet.py`로 234개 파일의 membership/hash를
재검증했다.
