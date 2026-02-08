# Todo

## Sprint 2: Backend Rebuild (Completed)
- [x] **API 계약서 작성** → `docs/api-contract.md`
    - [x] 7개 엔드포인트 스키마 정의
    - [x] TypeScript interface 정의
    - [x] 인디케이터 키 테이블 (프론트-백 공통)
- [x] **main.py 재작성**
    - [x] 메서드명 불일치 수정 (`get_all_country_summaries` → `build_master_snapshot`)
    - [x] `analytics.py` import 및 엔드포인트 연결 (correlation, green-growth, forecast)
    - [x] 새 엔드포인트 추가 (`/meta/countries`, `/meta/indicators`)
    - [x] CORS를 `localhost:3000`으로 제한
- [x] **deep_un.py 수정**
    - [x] 아카이브된 `EN.ATM.CO2E.PC` 인디케이터 제거
    - [x] `get_country_profile_v2()` 추가 — `{current, history, growth_5y}` 스키마
    - [x] `get_countries_meta()`, `get_indicators_meta()` 추가
- [x] **인프라 정리**
    - [x] 루트 `.gitignore` 생성
    - [x] 중복 파일 삭제 (`next.config.ts`, `postcss.config.mjs`)
- [x] **E2E 검증 (curl)**
    - [x] `GET /api/v2/country/KOR` — 200 OK, 스키마 일치 확인
    - [x] `GET /api/v2/analytics/correlation/co2_emissions/gdp_per_capita` — pearson_r=0.32, n=201
    - [x] `GET /api/v2/analytics/green-growth` — 랭킹 반환 확인
    - [x] `GET /api/v2/analytics/forecast/KOR/renewable_energy` — 2030 예측값 3.78
    - [x] `GET /api/v2/meta/countries` — 217개국 반환
    - [x] `GET /api/v2/meta/indicators` — 4개 클러스터, 키 목록 반환

## Backlog (Frontend — Antigravity 담당)
- [ ] `docs/api-contract.md` 기반으로 프론트엔드 타입 정의
- [ ] `page.tsx` 데이터 키를 백엔드 키와 일치시키기 (api-contract 참조)
- [ ] 국가 드롭다운을 `/api/v2/meta/countries`에서 동적 로딩
- [ ] 인디케이터 설정을 `/api/v2/meta/indicators`에서 동적 로딩
- [ ] correlation scatter plot 페이지 추가
- [ ] green-growth 랭킹 테이블 추가
- [ ] forecast 차트 (2030 예측선) 추가

## Backlog (Backend — Claude Code 담당)
- [ ] 실제 FAO/IRENA API 연동 (현재 World Bank만 사용)
- [ ] 정책 브리핑 자동 생성 엔드포인트
- [ ] 테스트 코드 작성 (pytest)
- [ ] 에러 핸들링 개선 (API 장애 시 graceful degradation)

## Sprint 1 Archive
- [x] 초기 백엔드 구현 (v1)
- [x] 초기 프론트엔드 구현 (Next.js + Tailwind)
- [x] Production Upgrade (50+ 인디케이터, analytics.py)
- See `docs/PROJECT_AUDIT.md` for full Sprint 1 post-mortem.

## Review Notes (Sprint 2)
- **근본 원인 해결**: API 계약서를 먼저 작성하고, 백엔드를 이에 맞춰 재작성.
- **4개 치명적 버그 전부 수정**: 메서드명 불일치, 키 불일치, 스키마 불일치, 아카이브 코드.
- **Dead Code 해소**: `analytics.py`의 모든 함수가 실제 엔드포인트에 연결됨.
- **검증 완료**: curl로 모든 엔드포인트 테스트, 실제 데이터 반환 확인.
- **다음 단계**: Antigravity가 `api-contract.md`를 기반으로 프론트엔드를 리팩토링.
