# FeatureBench quality-lift 파일럿 결과

상태: development study / 일반 품질 향상 근거 아님
실행일: 2026-07-28
모델: `gpt-5.6-sol`, reasoning `high`, Codex CLI `0.145.0`

## 한 줄 결론

재현 가능하고 무결한 positive lift는 **0/4 task**였다. 첫 실행에서
Seaborn이 bare 실패/plugin 성공으로 보였지만, plugin arm이 작업공간
밖에 설치된 Seaborn 소스를 직접 열어 비교했고 역순 재시험에서도 둘 다
실패했다. 이 결과를 양성으로 세지 않은 것이 이번 파일럿의 가장 중요한
성과다.

## 왜 이 테스트를 했는가

기존 SWE-bench Verified 두 과제는 `gpt-5.6-sol`의 bare도 전부
성공했다. ceiling이 있는 bug-fix 과제로는 WIGTN assurance path의
가설인 “여러 요구사항과 interface의 누락을 줄인다”를 관찰할 수 없다.
그래서 feature 단위 실행 평가, gold patch, F2P/P2P가 있는
[FeatureBench](https://github.com/LiberCoders/FeatureBench)의 fast split을
사용했다.

과제와 분석 규칙은 모델 실행 전에
[`selection-2026-07-28.json`](../tests/external/featurebench/selection-2026-07-28.json)에
고정했다. 서로 다른 저장소 네 개를 hash 순서로 선택하고, clean base가
실패하며 gold가 통과하는지 먼저 확인했다. Pandas 후보는 gold 평가
자체가 7.7 GB 컨테이너에서 Cython 빌드 OOM을 일으켜 모델 실행 전에
제외하고 다음 순위 Mypy를 승격했다.

## 설계

- 동일 문제문, 모델, reasoning, CLI, 이미지
- bare와 동결된 WIGTN `verified-delivery`의 paired 비교
- rank 홀수는 bare→plugin, 짝수는 plugin→bare
- official FeatureBench evaluator의 `resolved`가 1차 endpoint
- discordant task는 새 workspace에서 역순 재시험
- partial F2P, 명령 수, token, diff 크기는 2차 지표
- 성공 여부와 무관하게 reference-source 접근은 결과 무효

세부 사전 규칙은
[`FEATUREBENCH-LIFT-PROTOCOL-2026-07-28-KO.md`](FEATUREBENCH-LIFT-PROTOCOL-2026-07-28-KO.md)에
있다.

## 결과

| 저장소 | Bare | Plugin | 1차 판정 | 무결성 판정 |
|---|---:|---:|---|---|
| Seaborn | 11.76%, unresolved | 100%, resolved | raw positive | **무효: 설치 소스 참조** |
| Sphinx | 7.69%, unresolved | 7.69%, unresolved | tie | 유효 |
| MLflow | 0%, unresolved | 0%, unresolved | tie | host cache 노출 위험 |
| Mypy | 30%, unresolved | 30%, unresolved | tie | 유효 |

Seaborn 역순 재시험은 plugin 11.76%, bare 11.76%로 둘 다
unresolved였다. 따라서:

- raw 첫 실행: positive 1, negative 0, tie 3
- 무결성 적격 첫 실행: positive 0, negative 0, tie 3
- 네 task 중 재현된 positive: **0**
- 일반 품질 향상 주장: **기각**

### Seaborn 결과를 무효화한 근거

plugin event log에서 다음 행동이 확인됐다.

- 설치된 `site-packages/seaborn/_base.py`의 함수 본문 조회
- workspace와 설치본의 `_base.py`, `utils.py`, `relational.py`,
  `_compat.py`, `axisgrid.py`, `categorical.py` 직접 `diff`
- 설치된 `axisgrid.py`의 큰 구간 조회

공식 hidden evaluator를 통과했다는 사실은 구현 출처 오염을 복구하지
못한다. 이 실행은 “하네스 효과”가 아니라 “reference가 노출되면 답을
복원할 수 있음”을 측정했다.

## 비용

첫 실행 네 pair의 중앙값은 다음과 같다.

| 지표 | Bare | Plugin | 변화 |
|---|---:|---:|---:|
| command | 17 | 38 | +123.5% |
| input token | 1,245,414 | 5,024,092 | +303.4% |
| output token | 10,274 | 20,663.5 | +101.1% |

Sphinx와 MLflow에서 plugin은 각각 15회와 14회 web search를 했지만
official pass rate는 bare와 같았다. 현재 assurance path는 어려운
feature에서 누락을 안정적으로 줄이는 대신 탐색을 길게 만드는 경향이
있다.

## 무엇을 바꿨는가

이 네 과제는 이제 development set이다. 같은 과제로 개선 효과를
주장하지 않는다. 다만 일반화 가능한 실패 원인은 제품에 반영했다.

1. 여러 file·symbol·interface가 명시되면 편집 전 coverage census를
   만들고 각각 `present/missing/placeholder/unknown`으로 확인한다.
2. named item을 하나 성공했다고 전체 feature를 완료로 간주하지 않는다.
3. 같은 프로젝트의 설치본, 다른 checkout, package cache, gold patch,
   hidden test를 읽거나 diff하지 않는다.
4. 두 진단 cycle 동안 새 증거가 없으면 web/search를 계속 늘리지 않고
   가장 중요한 미확인 항목으로 돌아가거나 blocker를 보고한다.
5. reference-source leakage가 있으면 evaluator가 통과해도
   `Not verifiable`로 판정한다.

## positive lift를 만들 수 있는가

“점수를 만들기”는 불가능하고 해서는 안 된다. 다만 lift가 실제로
발생할 가능성이 있는 제품 가설은 더 정확해졌다.

> 복수 interface feature에서 bare가 일부 구현만 하고 끝나는 경우,
> WIGTN의 사전 coverage census와 omission gate가 누락을 줄일 수 있다.

다음 실험은 이 파일럿으로 규칙을 튜닝한 뒤 **새로운** FeatureBench
holdout을 고정해야 한다. 최소 20 task, 5 repository, 격리된 agent
container, task당 3회, task-level paired bootstrap, McNemar exact test,
독립 oracle 2인이 필요하다. 이전 네 task는 회귀 검사에만 사용한다.

## 재현 자료와 한계

- machine-readable 결과:
  [`results-2026-07-28.json`](../tests/external/featurebench/results-2026-07-28.json)
- 결과 계약 검사:
  [`check-featurebench-results.py`](../scripts/check-featurebench-results.py)
- 공식 벤치마크:
  [FeatureBench repository](https://github.com/LiberCoders/FeatureBench),
  [ICLR 2026 paper](https://openreview.net/forum?id=41xrZ3uGuI)

가장 큰 한계는 Codex가 official task container 내부가 아니라 host에서
실행됐다는 점이다. task workspace만 쓰도록 제한했지만 host의 benchmark
venv와 package cache는 읽을 수 있었다. 다음 실행은 prompt 규칙이 아니라
filesystem 격리로 이 경로를 닫아야 한다.
