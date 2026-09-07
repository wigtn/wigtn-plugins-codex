"""Predeclared development cases and review criteria; no expected answers in prompts."""
PROMPTS = {
    'prd': '파일을 수정하지 말고 조직 관리자 팀원 초대 기능의 간결한 구현용 PRD를 작성해줘. 만료 전 수락, 중복 초대, 만료, 권한, 재전송을 포함하고 안정적인 요구사항 ID와 관찰 가능한 인수조건을 붙여라. SLA나 규모 수치를 만들지 마라.',
    'uncertain': '파일을 수정하거나 명령을 실행하지 말고 검증해줘. REQ-01: 초대 토큰은 한 번만 사용할 수 있다. 증거는 consumeInvite(token) 함수가 있다는 설명뿐이다. 코드와 테스트 결과는 제공되지 않았다. 확인할 수 없는 사실을 통과로 추정하지 마라.',
    'design': '팀 내부 장애 이력 대시보드의 디자인 방향을 정해줘. 새 프로젝트이고 별도 디자인 시스템은 없다. 선호는 흰 배경, 청록 포인트, 높은 정보 밀도, 읽기 쉬운 한글이다. 대안을 고르는 단계 없이 적절한 방향 하나를 결정하고 바로 구현 가능한 시각 계약을 답변해줘. 코드는 작성하지 마라.',
    'ordinary': "Fix sorted_scores in scores.py so it returns scores in ascending order without mutating the caller's list. Run the existing tests. Keep notes.txt unchanged.",
    'compact-review': '''아래 Compact PRD를 실질적으로 리뷰해줘. 수정본 작성은 요청하지 않는다.
<!-- wigtn-prd-profile: compact -->
# CSV 내보내기 PRD
## Problem and scope
관리자가 현재 목록을 CSV로 저장한다. 기존 목록 화면 버튼을 사용한다.
## Goals and non-goals
현재 조회 결과만 내보낸다. 새 화면, 다단계 작업, 비동기 작업은 범위 밖이다.
## Users, roles, authorization, and data boundaries
조직 관리자만 소속 조직 데이터를 내보낸다. 서버가 역할과 조직을 검사한다.
## Functional requirements
| ID | Requirement | Priority |
| FR-01 | 현재 필터 결과를 UTF-8 CSV로 반환 | Must |
| FR-02 | 서버가 관리자 역할과 조직 소유권 검사 | Must |
## Acceptance criteria
| ID | Requirement | Given | When | Then | Verification |
| AC-01 | FR-01 | 조회 결과 2행 | 관리자가 내보내기 | 헤더와 해당 2행 포함 | CSV 통합 검사 |
| AC-02 | FR-02 | 다른 조직 관리자 | 내보내기 요청 | 403, 데이터 미노출 | 권한 통합 검사 |
| AC-03 | FR-02 | 소속 조직 일반 멤버 | 내보내기 요청 | 403 | 권한 통합 검사 |
## Assumptions and open decisions
CSV 열은 기존 목록 열과 같으며 현재 필터는 서버에서 다시 적용한다.
## Release condition
| Requirement IDs | Verifiable exit condition |
| FR-01, FR-02 | AC-01~03 통합 검사 통과 |
''',
    'external-review': '''WIGTN 형식으로 변환하지 말고 다음 팀 요구사항 문서의 내용만 검토해줘.
대상은 기존 API의 입력 검증 수정이다. FR-1: 이름은 공백 제거 후 1~80자만 허용한다.
FR-2: 권한은 기존 인증·조직 정책을 유지한다. AC-1: 빈 이름은 400이다.
AC-2: 80자는 저장되고 81자는 400이다. AC-3: 비로그인은 401이다.
AC-4: 다른 조직의 사용자는 변경하지 못한다. 새 화면과 사용자 흐름은 없다.
출시 조건은 기존 회귀 검사와 이 네 API 검사의 통과다. 파일을 만들지 마라.''',
    'many-findings': '''다음 PRD의 구현을 막는 모순을 리뷰해줘. 원문을 수정하지 마라.
기능은 조직별 파일 보관함이다.
FR-01: 업로드는 관리자만 가능하다. AC-01: 비로그인 방문자의 업로드가 성공한다.
FR-02: 조직 경계를 서버에서 강제한다. AC-02: 다른 조직 파일 ID를 주면 다운로드가 성공한다.
FR-03: 삭제 직후 파일은 복구 불가능하다. AC-03: 삭제 후 30일 동안 원본 복원이 가능하다.
FR-04: 동일 요청 ID 재시도는 파일 하나만 만든다. AC-04: 동일 요청 ID로 3회 보내면 파일 3개가 생긴다.
FR-05: 암호화 키는 고객만 보유하고 서버는 복호화할 수 없다. AC-05: 서버가 평문 본문으로 전문 검색한다.
FR-06: 보존기간 내 파일 삭제를 금지한다. AC-06: 보존기간 내 소유자의 삭제가 즉시 성공한다.
''',
}
PROMPTS['delivery'] = PROMPTS['ordinary']
RUBRIC = {
    'prd': ['covers-requested-behaviors', 'observable-criteria', 'no-invented-requirements'],
    'uncertain': ['no-false-verification', 'no-prohibited-command'],
    'design': ['one-usable-direction', 'preferences-preserved', 'no-choice-pause'],
    'ordinary': ['requested-fix-and-tests', 'no-unrequested-work'],
    'delivery': ['evidence-proportional', 'no-unrequested-state'],
    'compact-review': ['compact-profile-respected', 'no-full-only-gaps', 'no-unrequested-rewrite'],
    'external-review': ['content-reviewed', 'no-wigtn-format-gate', 'no-new-artifact'],
    'many-findings': [f'conflict-FR-{i:02}' for i in range(1, 7)],
}
ACTIVATION = {case: 'product-spec' for case in ['prd', 'compact-review', 'external-review', 'many-findings']}
ACTIVATION.update(design='design-direction', delivery='verified-delivery')
SUITES = {
    'smoke': ['prd', 'uncertain', 'design', 'ordinary'],
    'targeted': ['prd', 'uncertain', 'design', 'ordinary', 'delivery'],
    'contracts': ['compact-review', 'external-review', 'many-findings', 'uncertain', 'delivery'],
}
