# Lessons Learned

## Patterns & Rules
- World Bank API indicator codes get archived over time. Always verify codes against the live API before hardcoding them.
- `EN.ATM.CO2E.PC` (CO2 per capita) was archived; replacement is `EN.GHG.CO2.PC.CE.AR5`.
- Use `per_page=20000` with the World Bank API to get all country×year combos in one request.
- **API Contract First**: 프론트엔드-백엔드 작업 전 반드시 공유 인터페이스(TypeScript type 또는 OpenAPI spec)를 먼저 정의한다.
- **1개로 검증, N개로 확장**: 50개 인디케이터를 한번에 구현하지 말고, 1개로 풀스택 E2E 검증 후 확장한다.
- **메서드명은 호출처와 일치시킨다**: `main.py`가 호출하는 메서드명과 `deep_un.py`에 정의된 메서드명이 다르면 런타임 크래시.

## Mistakes to Avoid
- Don't assume indicator codes from documentation are still valid — the World Bank archives and replaces indicators.
- Don't use `asyncio.get_event_loop()` (deprecated); use `asyncio.get_running_loop()` instead.
- FastAPI's `on_event("startup")` is deprecated; use the `lifespan` context manager pattern.
- **프론트엔드와 백엔드 키 이름이 달라도 컴파일/빌드 시 에러가 안 난다** — TypeScript `any`를 쓰면 키 불일치를 잡을 수 없다. 반드시 구체적 타입 사용.
- **설정 파일 중복 금지**: `next.config.js`와 `next.config.ts`가 둘 다 있으면 Next.js가 혼란. 하나만 유지.
- **아카이브된 코드를 lessons.md에 기록하고도 실제 코드에서 제거하지 않으면 의미 없다.**
- **analytics.py처럼 좋은 코드를 만들어놓고 main.py에 연결하지 않으면 dead code다** — 모듈을 만들면 즉시 import하고 엔드포인트에 연결.

## Useful Strategies
- Fetch all indicator data at server startup via `lifespan`, so endpoints respond instantly without cache-miss latency.
- Use `pd.pivot_table()` + `interpolate(limit=3)` for clean time-series DataFrames from sparse API data.
- Pre-compute derived metrics (growth rates) at load time rather than per-request.
- **풀스택 검증 순서**: API 스키마 정의 → 백엔드 엔드포인트 1개 → curl로 응답 확인 → 프론트엔드 연결 → 화면에 숫자 확인 → 확장.
- **PROJECT_AUDIT.md 참조**: `docs/PROJECT_AUDIT.md`에 전체 버그/결함 목록과 재구축 전략이 정리되어 있다.
