# WIGTN Plugins for Codex

Codex의 일반 코딩 자율성은 유지하면서 제품 명세, 화면정의, 인수조건 검증, 안전한 Git 릴리스, WIGTN 브랜드 자산을 필요한 순간에만 불러오는 skills-first 플러그인입니다.

## Included skills

| Skill | Natural-language examples | Policy |
|---|---|---|
| `product-spec` | “PRD 뽑아줘”, “PRD 검토해줘”, “PRD 디깅해줘” | implicit |
| `screen-spec` | “화면정의서 만들어줘”, “IA와 wireframe 만들어줘” | implicit |
| `acceptance-verifier` | “PRD 요구사항 반영됐는지 검증해줘” | implicit |
| `design-direction` | “이 신규 UI 디자인 방향 잡아줘” | implicit, narrow |
| `verified-delivery` | `$verified-delivery 이 기능 구현해줘` | explicit only |
| `release-readiness` | “커밋해줘”, “푸시해줘”, “PR 올려줘” | implicit, narrow |
| `handdrawn-diagram` | “손그림 아키텍처 만들어줘” | implicit |
| `wigtn-presentation` | “WIGTN 브랜드 발표자료 만들어줘” | implicit, narrow |

## Repository layout

- `.agents/plugins/marketplace.json`: repository marketplace
- `plugins/wigtn-plugins-with-codex/.codex-plugin/plugin.json`: plugin manifest
- `plugins/wigtn-plugins-with-codex/skills/`: eight Codex skills
- `scripts/validate.sh`: manifest, skill, policy, and trigger-contract validation
- `docs/PRD.md`: product contract and implementation decisions

## Validate

```bash
./scripts/validate.sh
```

The trigger fixtures are deterministic contract checks. Actual implicit selection must still be smoke-tested in a new Codex task after installation.

## Design contract

- No automatic Sol/Terra/Luna routing
- No bundled MCP, app, or lifecycle hook in MVP
- No automatic commit, push, PR, issue, deploy, or dependency installation
- `verified-delivery` is explicit-only; ordinary implementation remains ordinary Codex work

Licensed under Apache-2.0.

## Install from GitHub

Register the repository marketplace, then install the plugin:

```bash
codex plugin marketplace add wigtn/wigtn-plugins-codex
codex plugin add wigtn-plugins-with-codex@wigtn
```

In the Codex app, open Plugins, select the WIGTN marketplace, install the plugin, and start a new task. Installed local or Git marketplace copies are cached; refresh the marketplace and reinstall after an update.

## Release behavior

Pull requests and pushes to `main` run the repository contract, official Codex validators when available, and 30 trigger fixtures. Bumping the plugin manifest version on `main` creates a matching GitHub tag and Release. The marketplace itself is served from this repository, so no separate deployment artifact is required.
