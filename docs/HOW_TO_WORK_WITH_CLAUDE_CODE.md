# Claude Code 200% 활용 가이드

> 클로드 코드에게 일 시키는 법. 구린 결과물 안 나오게 하는 법.

---

## 0. 핵심 원리: Claude Code는 "명령형 AI"가 아니다

Claude Code는 채팅 AI가 아닙니다. **프로젝트 컨텍스트를 읽고 작업하는 엔지니어**입니다.

| 잘못된 사용법 | 올바른 사용법 |
|---|---|
| "대시보드 만들어줘" | "이 API 스키마에 맞는 FastAPI 엔드포인트를 만들어줘" |
| "프론트엔드 연결해" | "`/api/v2/country/{iso3}`가 반환하는 JSON을 `page.tsx`에서 fetch해서 렌더링해줘" |
| "전부 다 고쳐" | "BUG #1 (메서드명 불일치)부터 고쳐줘. 고치고 curl로 확인해줘" |

**구체적일수록 정확하고, 모호할수록 엉뚱한 결과가 나옵니다.**

---

## 1. 프로젝트 세팅: CLAUDE.md가 "두뇌"다

Claude Code는 세션을 시작할 때 `CLAUDE.md`를 읽습니다. 여기에 적힌 것이 곧 Claude Code의 행동 규칙입니다.

### 현재 CLAUDE.md에 추가해야 할 것

```markdown
## Project Context
- 이 프로젝트는 Visual Climate Engine이다.
- 백엔드: Python/FastAPI (Claude Code 담당)
- 프론트엔드: Next.js/React (Antigravity 담당)
- API 계약: docs/api-contract.md 참조
- 작업 전 반드시 tasks/todo.md를 확인하고 업데이트한다.
```

이걸 적어두면 매번 설명할 필요 없이 Claude Code가 맥락을 파악합니다.

---

## 2. 작업 요청하는 법 (프롬프트 템플릿)

### 템플릿 A: 새 기능 개발

```
[목표] /api/v2/analytics/green-growth 엔드포인트를 만들어줘.

[스펙]
- analytics.py의 detect_green_growth()를 사용
- 응답 형식: { rankings: [...], metadata: { total_countries: N } }
- CO2 growth는 co2_emissions_growth_5y, GDP growth는 gdp_growth_growth_5y 사용

[제약]
- main.py에 추가
- 기존 엔드포인트 건드리지 마
- 완성 후 curl로 테스트해서 결과 보여줘

[검증]
- curl localhost:8000/api/v2/analytics/green-growth 실행
- 응답에 최소 5개 국가가 있어야 함
```

### 템플릿 B: 버그 수정

```
[버그] main.py:31에서 collector.get_all_country_summaries() 호출하는데,
deep_un.py에는 이 메서드가 없음. build_master_snapshot()이 맞음.

[수정] 메서드명을 올바른 것으로 교체해줘.

[검증] 서버 시작 후 curl localhost:8000/api/v1/data/master 호출해서
200 응답 + JSON 데이터 나오는 것 확인해줘.
```

### 템플릿 C: 계획 수립 요청

```
[상황] 프론트엔드와 백엔드의 데이터 스키마가 불일치한다.
docs/PROJECT_AUDIT.md의 BUG #2, #3 참고.

[요청] 이 불일치를 해결하는 계획을 세워줘.
- 백엔드 응답 스키마를 어떻게 바꿀지
- 어떤 파일을 수정해야 하는지
- 수정 순서는 어떻게 할지

계획만 세우고, 코드는 아직 쓰지 마. 내가 승인하면 그때 실행해.
```

### 템플릿 D: 문서/스키마 작성

```
[요청] 프론트엔드팀(Antigravity)과 공유할 API 스키마 문서를 만들어줘.

[포함할 것]
- 모든 엔드포인트 목록 (URL, Method, 파라미터)
- 각 엔드포인트의 응답 JSON 예시
- TypeScript interface 정의

[파일] docs/api-contract.md로 저장
```

---

## 3. 프론트/백 분리 작업하는 법

### 구조

```
너 (사용자)
 ├── Claude Code 세션: 백엔드 작업
 └── Antigravity 세션: 프론트엔드 작업
```

### 작업 순서

```
Step 1: Claude Code에게 API 스키마 문서 생성 요청
         → docs/api-contract.md 생성됨

Step 2: Antigravity에게 "docs/api-contract.md를 읽고
         이 스키마에 맞춰서 프론트엔드를 만들어줘" 라고 요청

Step 3: Claude Code에게 "docs/api-contract.md에 맞춰서
         백엔드 엔드포인트를 구현해줘" 라고 요청

Step 4: 양쪽 다 완성되면, 서버 둘 다 켜고 E2E 테스트
```

### 핵심: "계약서"가 두 팀을 연결한다

```
┌─────────────┐     docs/api-contract.md     ┌─────────────┐
│  Claude Code │ ◄──────────────────────────► │ Antigravity  │
│  (Backend)   │    "이 스키마를 기준으로"       │ (Frontend)   │
└─────────────┘     "각자 개발한다"             └─────────────┘
```

Antigravity한테 이렇게 말하면 됩니다:

> "docs/api-contract.md 파일을 읽어.
> 백엔드 API가 이 형식으로 데이터를 보내줄 거야.
> 이 스키마에 맞춰서 프론트엔드를 만들어줘.
> 백엔드가 아직 안 돼있으면 mock 데이터로 먼저 개발해."

---

## 4. todo.md 활용법

### 누가 작성하나?

**너 또는 Claude Code 둘 다 가능.** 두 가지 방법:

#### 방법 1: 네가 큰 그림을 적고, Claude Code가 세부 사항 채우기

```
너: "tasks/todo.md에 이번 스프린트 계획을 세워줘.
     목표는 백엔드 API를 api-contract.md에 맞게 재작성하는 것."

Claude Code: todo.md에 세부 체크리스트를 작성함
```

#### 방법 2: 네가 직접 todo.md에 적기

```markdown
# Todo - Sprint 2

## Backend (Claude Code)
- [ ] API 스키마 문서 작성 (docs/api-contract.md)
- [ ] main.py 메서드명 수정
- [ ] 프론트엔드 스키마에 맞는 응답 래퍼 추가
- [ ] analytics.py 엔드포인트 연결
- [ ] curl로 전체 엔드포인트 검증

## Frontend (Antigravity)
- [ ] api-contract.md 기반으로 타입 정의
- [ ] 데이터 키를 백엔드 키와 일치시키기
- [ ] mock 데이터로 개발 → 실제 API 연결
```

그리고 Claude Code에게:
```
"tasks/todo.md를 읽고, Backend 섹션의 첫 번째 항목부터 시작해줘."
```

---

## 5. 흔한 실수와 해결법

### 실수 1: "알아서 해줘"

```
나쁜 예: "백엔드 고쳐줘"
좋은 예: "docs/PROJECT_AUDIT.md의 BUG #1을 고쳐줘.
         main.py의 메서드 호출을 deep_un.py의 실제 메서드명과 일치시켜."
```

### 실수 2: 한번에 너무 많이 요청

```
나쁜 예: "50개 인디케이터 전부 구현하고 프론트도 연결해줘"
좋은 예: "energy_transition 클러스터의 renewable_energy 인디케이터 1개만
         먼저 구현해서 풀스택으로 동작하는 거 보여줘."
```

### 실수 3: 검증 요청 안 함

```
나쁜 예: "엔드포인트 만들어줘" (끝)
좋은 예: "엔드포인트 만들고, 서버 시작해서
         curl로 호출한 결과를 보여줘."
```

### 실수 4: 컨텍스트 안 줌

```
나쁜 예: "API 스키마 만들어줘"
좋은 예: "현재 deep_un.py의 CLUSTERS 구조를 기반으로,
         프론트엔드가 { current, history, growth_5y } 형태로
         받을 수 있는 API 스키마를 만들어줘."
```

---

## 6. 이 프로젝트에서 지금 당장 해야 할 것

### 너의 할 일 (순서대로)

```
1. Claude Code에게 요청:
   "docs/api-contract.md를 만들어줘.
    현재 deep_un.py의 CLUSTERS와 analytics.py의 함수들을 기반으로,
    프론트엔드가 사용할 모든 엔드포인트의 스키마를 정의해줘.
    TypeScript interface도 포함해줘."

2. api-contract.md를 네가 리뷰한다. 마음에 안 드는 부분을 수정 요청.

3. Claude Code에게 요청:
   "api-contract.md에 맞춰서 백엔드를 수정해줘.
    energy_transition 클러스터 1개만 먼저 해줘.
    완성 후 curl로 테스트 결과를 보여줘."

4. 1개 클러스터가 동작하면, Antigravity에게 요청:
   "docs/api-contract.md를 읽고, 이 스키마에 맞춰서
    프론트엔드를 리팩토링해줘.
    일단 energy_transition 탭만 먼저."

5. 프론트 + 백 둘 다 켜서 실제로 동작하는지 확인.

6. 동작하면:
   Claude Code: "나머지 3개 클러스터도 같은 패턴으로 확장해줘."
   Antigravity: "나머지 3개 탭도 같은 패턴으로 확장해줘."
```

---

## 7. 꿀팁

### Claude Code가 계획 모드로 들어가게 하는 법
```
"계획만 세워줘. 코드는 아직 쓰지 마."
"plan mode로 들어가서 어떻게 할지 보여줘."
```

### 이전 작업 참조시키는 법
```
"docs/PROJECT_AUDIT.md를 읽고, 거기서 말한 Phase 1을 실행해줘."
"tasks/lessons.md를 읽고, 같은 실수 하지 마."
```

### 작업 범위를 제한하는 법
```
"main.py만 수정해. 다른 파일은 건드리지 마."
"새 파일 만들지 말고, 기존 파일에서 해결해."
```

### 검증을 강제하는 법
```
"코드 수정 후 반드시 서버를 시작해서 테스트해줘."
"테스트가 통과하지 않으면 완료로 표시하지 마."
```

### 할 일 목록을 자동 관리시키는 법
```
"tasks/todo.md를 읽고, 완료된 항목은 체크하고,
 새로 발견된 작업이 있으면 추가해줘."
```

---

## 8. 요약: Claude Code에게 좋은 프롬프트 공식

```
[목표]  무엇을 달성하고 싶은지 (한 줄)
[맥락]  관련 파일이나 문서 (구체적 경로)
[스펙]  입력/출력 형식, 제약 조건
[검증]  어떻게 확인할 수 있는지
[범위]  수정할 파일, 건드리지 말 파일
```

이 5가지만 매번 적으면, 구린 결과물은 더 이상 안 나옵니다.

---

*이 가이드는 /Users/harimgemmajung/Documents/Claude/docs/ 에 저장되어 있습니다.*
