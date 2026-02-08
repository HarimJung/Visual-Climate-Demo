# Visual Climate Engine: Project Audit & Architecture Document

> 이 문서는 프로젝트의 현재 상태를 정직하게 진단하고, 무엇을 하려 했는지, 왜 현재 상태가 문제인지, 그리고 어떻게 고쳐야 하는지를 정리한 문서입니다.

---

## 1. 우리가 하려던 것 (Original Vision)

**한 줄 요약**: UN 산하 기구(FAO, IRENA, WHO, UNDP, OECD) 데이터를 통합해서, 정책 담당자가 30초 만에 국가별 기후/경제 리포트를 뽑아볼 수 있는 대시보드.

**구체적으로**:
- 50+ 지표를 4개 정책 클러스터(에너지 전환, 농업 회복력, 도시 건강, 경제 리스크)로 묶어서
- 200+ 국가, 34년치(1990-2023) 시계열 데이터를 수집하고
- Pearson 상관분석, Green Growth 탐지, 2030 선형 예측까지 제공하며
- Next.js + Tailwind + Recharts로 인터랙티브 대시보드 시각화

---

## 2. 현재 파일 구조

```
Claude/
├── CLAUDE.md                          # Agent 워크플로우 지침
├── docs/
│   ├── PRD.md                         # 제품 요구사항 (이상향)
│   └── PROJECT_AUDIT.md               # ← 이 문서
├── tasks/
│   ├── todo.md                        # 스프린트 추적
│   ├── backend_mission.md             # 백엔드 구현 명세
│   └── lessons.md                     # 교훈 기록
├── backend/
│   ├── main.py                        # FastAPI 서버 (81줄)
│   ├── requirements.txt               # Python 의존성
│   ├── data/
│   │   └── world_bank_cache.json      # 캐시 (102MB!)
│   └── src/
│       ├── collectors/
│       │   └── deep_un.py             # ETL 파이프라인 (466줄)
│       └── logic/
│           ├── __init__.py
│           └── analytics.py           # 분석 엔진 (197줄) ← 사용되지 않음!
└── frontend/
    ├── app/
    │   ├── layout.tsx                  # 루트 레이아웃
    │   ├── page.tsx                    # 메인 대시보드 (391줄)
    │   └── globals.css                # 글로벌 스타일
    ├── package.json
    ├── next.config.js                 # API 프록시 설정
    ├── next.config.ts                 # ← 사용 안 됨, 중복!
    ├── postcss.config.js              # PostCSS 설정
    ├── postcss.config.mjs             # ← 사용 안 됨, 중복! (잘못된 플러그인명)
    ├── tailwind.config.ts
    ├── tsconfig.json
    └── node_modules/                  # 364개 디렉토리
```

---

## 3. 치명적 버그 목록 (Critical Bugs)

### BUG #1: 서버가 시작하자마자 크래시한다

`main.py:31`에서 `collector.get_all_country_summaries()` 호출 → **이 메서드는 존재하지 않는다.**

```python
# main.py가 호출하는 것:
collector.get_all_country_summaries()    # ← 존재하지 않음
collector.get_country_full_profile()     # ← 존재하지 않음

# deep_un.py에 실제로 있는 것:
collector.build_master_snapshot()         # ← 이게 맞음
collector.get_country_cluster_profile()   # ← 이게 맞음
```

**결과**: `AttributeError: 'DeepUNCollector' object has no attribute 'get_all_country_summaries'`. 서버는 시작은 되지만, 어떤 엔드포인트를 호출해도 500 에러.

### BUG #2: 프론트엔드-백엔드 데이터 키가 완전히 다르다

프론트엔드가 기대하는 키:
```typescript
// page.tsx:168-172
{ key: 'renewable_energy_share', ... }
{ key: 'co2_emissions_per_capita', ... }
{ key: 'access_to_electricity', ... }
{ key: 'fossil_fuel_consumption', ... }
```

백엔드가 실제로 보내는 키:
```python
# deep_un.py:58-60
"renewable_energy":       "EG.FEC.RNEW.ZS"
"co2_emissions":          "EN.GHG.CO2.PC.CE.AR5"
"access_electricity":     "EG.ELC.ACCS.ZS"
"fossil_fuel_energy_pct": "EG.USE.COMM.FO.ZS"
```

**결과**: 모든 MetricCard와 TimeSeriesChart에 `undefined`가 전달된다. 대시보드는 "Data Unavailable" 또는 빈 카드만 보여준다.

### BUG #3: 응답 데이터 구조 불일치

프론트엔드가 기대하는 구조:
```typescript
{
  iso3: "KOR",
  name: "Korea, Rep.",
  data: {
    energy_transition: {
      renewable_energy_share: {
        current: 2.5,
        history: { "1990": 1.2, "1991": 1.3, ... },
        growth_5y: 0.08
      }
    }
  }
}
```

백엔드가 실제로 보내는 구조 (`get_country_cluster_profile`):
```python
{
  "energy_transition": {
    "1990": { "co2_emissions": 5.8, "renewable_energy": 1.2, ... },
    "1991": { "co2_emissions": 6.1, "renewable_energy": 1.3, ... },
    ...
  }
}
```

**차이점**:
- `iso3`, `name` 필드 없음
- `data` wrapper 없음
- 구조가 `year → indicators` (백엔드) vs `indicator → {current, history, growth_5y}` (프론트엔드)
- **완전히 다른 데이터 스키마**

**결과**: 프론트엔드가 `profile.data.energy_transition`에 접근하면 `undefined`. 아무것도 렌더링 안 됨.

### BUG #4: 아카이브된 인디케이터 코드 중복 사용

```python
# deep_un.py:56-57 — 둘 다 에너지 클러스터에 있음
"co2_emissions":  "EN.GHG.CO2.PC.CE.AR5",  # 새 코드
"co2_per_capita": "EN.ATM.CO2E.PC",         # ← 아카이브됨! 0건 반환!
```

`lessons.md`에 "아카이브됨"이라고 기록해놓고, 코드에서 여전히 사용 중.

---

## 4. 설계 결함 목록 (Design Flaws)

### FLAW #1: analytics.py는 완전한 Dead Code

`analytics.py`에 197줄의 코드가 있다:
- `calculate_correlation()` — 사용 안 됨
- `detect_green_growth()` — 사용 안 됨
- `forecast_trend()` — 사용 안 됨
- `build_country_report()` — 사용 안 됨

`main.py`에서 `analytics.py`를 **import하지 않는다**. correlation 엔드포인트는 `main.py`에서 직접 구현했고, 나머지 함수들은 어디에서도 호출되지 않는다.

### FLAW #2: 102MB 캐시 파일이 프로젝트에 포함

`backend/data/world_bank_cache.json`이 102MB. 루트에 `.gitignore`가 없다. 이대로 `git add .`하면 102MB JSON이 커밋된다.

### FLAW #3: 설정 파일 중복 및 충돌

| 파일 | 상태 |
|------|------|
| `next.config.js` | 실제 사용됨 (API 프록시) |
| `next.config.ts` | 빈 보일러플레이트, 사용 안 됨 |
| `postcss.config.js` | 실제 사용됨 |
| `postcss.config.mjs` | `@tailwindcss/postcss` — 존재하지 않는 플러그인 |

Next.js는 `.js`와 `.ts`가 둘 다 있으면 혼란을 일으킬 수 있다.

### FLAW #4: 타입 안전성 없음

TypeScript를 쓰고 있지만 핵심 컴포넌트에 `any`를 쓴다:

```typescript
function MetricCard({ label, value, trend, unit, icon, colorClass }: any)  // any!
function TimeSeriesChart({ title, data, dataKey, color, unit }: any)        // any!
```

TypeScript를 쓰는 의미가 없다. 타입으로 프론트-백 간 계약을 정의했다면, BUG #2와 #3은 컴파일 시점에 잡혔을 것이다.

### FLAW #5: 보안 허점

```python
# main.py:18-23
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 모든 도메인 허용
    allow_credentials=True,        # 쿠키도 허용
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`allow_origins=["*"]` + `allow_credentials=True`는 보안 안티패턴.

### FLAW #6: 서버 시작 시 30-60초 블로킹

`lifespan`에서 모든 데이터를 동기적으로 로딩한다. 캐시가 없으면 World Bank API에 50+ 요청을 보내면서 서버가 30-60초간 응답 불가. Health check 엔드포인트도 없고, readiness probe도 없다.

### FLAW #7: PRD와 현실의 괴리

| PRD가 약속한 것 | 현실 |
|------|------|
| FAO, IRENA, WHO, UNDP, OECD, UNCTAD | World Bank API 하나만 사용 |
| Multi-Agent 구조 (Librarian + Analyst) | 단일 Collector 클래스 |
| SDMX 프로토콜 지원 | JSON만 파싱 |
| 정책 브리핑 자동 생성 | 미구현 |
| Zero-Hallucination Guardrail | 미구현 |

PRD는 "비전 문서"이지, 현재 시스템의 설명서가 아니다.

### FLAW #8: 프론트엔드 하드코딩

- 국가 목록이 16개로 하드코딩 (`page.tsx:248-265`). 백엔드는 200+ 국가 데이터를 갖고 있다.
- API URL이 `http://localhost:8000`으로 하드코딩 (`page.tsx:270`).
- 클러스터별 인디케이터 설정이 프론트엔드에 하드코딩 (`page.tsx:166-194`). 백엔드의 클러스터 구조와 독립적.

### FLAW #9: 에러 핸들링 부재

- 백엔드: World Bank API 실패 시 빈 리스트 반환. 에러 상태를 프론트엔드에 전달하지 않음.
- 프론트엔드: 빈 데이터와 실제 에러를 구분 못함.
- 캐시 파일 깨지면? 서버 시작 실패.

### FLAW #10: 테스트 제로

테스트 파일이 단 하나도 없다. `pytest`, `jest` 어떤 것도 없다.

---

## 5. 왜 이대로 하면 망하는가

### 현재 상태 = "돌아가지 않는 시스템"

1. **서버를 켜도 크래시**: 메서드명 불일치로 500 에러
2. **크래시를 고쳐도 빈 화면**: 데이터 스키마 불일치로 UI에 아무것도 안 나옴
3. **빈 화면을 고쳐도 절반은 빈 데이터**: 아카이브된 인디케이터 코드 사용
4. **분석 기능은 완성했지만 연결 안 됨**: analytics.py 197줄이 dead code

### 근본 원인: **API 계약(Contract)이 정의되지 않았다**

프론트엔드와 백엔드가 **합의된 데이터 스키마 없이** 각자 개발됐다. 결과:
- 백엔드 개발자(Claude)가 만든 키: `renewable_energy`
- 프론트엔드 개발자(Claude)가 기대한 키: `renewable_energy_share`
- 같은 AI가 만들었는데도 일치하지 않는다

이것은 "더 열심히 코딩하면 해결되는 문제"가 아니다. **설계 단계에서 계약(interface)을 먼저 정의하고, 양쪽이 그것을 준수해야 하는 문제**다.

### 복잡도 관리 실패

- 50+ 인디케이터를 한번에 구현하려다 검증 불가능
- "장대한 비전"(PRD)과 "증분적 실행"(Sprint) 사이의 갭이 너무 큼
- 1개 인디케이터로 풀스택 검증 → 확장 의 순서여야 했음

---

## 6. 올바른 재구축 전략

### Phase 0: API 계약 정의 (가장 먼저)

```typescript
// shared/types.ts — 프론트엔드와 백엔드가 공유하는 계약

interface CountryProfileResponse {
  iso3: string;
  name: string;
  data: Record<ClusterName, ClusterData>;
}

interface ClusterData {
  [indicatorKey: string]: {
    current: number | null;
    history: Record<string, number>;   // year -> value
    growth_5y: number | null;
  };
}

type ClusterName =
  | "energy_transition"
  | "agricultural_resilience"
  | "urban_health"
  | "economic_risk";
```

이 스키마가 합의되기 전까지 한 줄의 코드도 쓰지 않는다.

### Phase 1: 최소 작동 버전 (1 클러스터, 3 인디케이터)

1. 백엔드: `energy_transition` 클러스터에서 3개 인디케이터만 → 위 스키마대로 반환
2. 프론트엔드: 해당 3개 인디케이터를 카드 + 차트로 렌더링
3. **E2E 검증**: 서버 시작 → API 호출 → 화면에 숫자 표시 확인

### Phase 2: 전체 클러스터 확장

- Phase 1이 동작하는 것을 확인한 후, 나머지 3개 클러스터 추가
- 인디케이터 키를 프론트-백에서 동일하게 유지

### Phase 3: 분석 기능 연결

- `analytics.py`의 함수들을 실제 엔드포인트에 연결
- correlation, green growth, forecast 엔드포인트 추가

### Phase 4: 인프라 정리

- `.gitignore` 추가 (cache, node_modules, venv, .next)
- 환경변수 분리 (`.env.local`)
- 테스트 작성
- 중복 설정 파일 제거

---

## 7. 현재 코드에서 살릴 수 있는 것

| 파일 | 판정 | 이유 |
|------|------|------|
| `deep_un.py` | **살림** (80%) | ETL 파이프라인 자체는 잘 작동함. 메서드명 정리 + 아카이브 코드 제거 필요 |
| `analytics.py` | **살림** (100%) | 코드 품질 좋음. 엔드포인트에 연결만 하면 됨 |
| `main.py` | **재작성** | 메서드명 불일치, analytics 미연결, 응답 스키마 미정의 |
| `page.tsx` | **대폭 수정** | UI 컴포넌트는 살리되, 데이터 키와 타입을 백엔드 계약에 맞춤 |
| `globals.css` | **살림** (100%) | 디자인 시스템 잘 되어 있음 |
| `tailwind.config.ts` | **살림** (100%) | 문제 없음 |
| `PRD.md` | **비전 문서로 보존** | 현실과 다르지만 방향성 참고용 |
| `backend_mission.md` | **아카이브** | Phase 1 완료됨. 히스토리 보존용 |

---

## 8. 즉시 해야 할 것 (Quick Wins)

1. **루트 `.gitignore` 생성**: `node_modules/`, `.next/`, `venv/`, `data/*.json`, `.DS_Store`
2. **중복 파일 삭제**: `next.config.ts`, `postcss.config.mjs`
3. **`main.py` 메서드명 수정**: `get_all_country_summaries` → `build_master_snapshot`, `get_country_full_profile` → `get_country_cluster_profile`
4. **아카이브된 인디케이터 제거**: `co2_per_capita` (`EN.ATM.CO2E.PC`) 삭제
5. **`deep_un.py`에 프론트엔드 스키마 맞춤 메서드 추가**: `{ current, history, growth_5y }` 구조로 반환하는 래퍼 메서드

---

## 9. 핵심 교훈

> **"돌아가는 걸 먼저 만들고, 그 다음에 확장하라."**

50개 인디케이터를 한번에 구현하느라 1개도 제대로 동작하지 않는 상태가 되었다. 다음번에는:

1. API 스키마를 먼저 합의한다 (TypeScript interface 또는 OpenAPI spec)
2. 1개 인디케이터로 풀스택(DB → API → UI) 검증한다
3. 검증된 파이프라인을 복제해서 확장한다
4. 매 확장마다 E2E 테스트로 회귀 방지한다

---

*이 문서는 2026-02-07 기준 프로젝트 상태를 반영합니다.*
