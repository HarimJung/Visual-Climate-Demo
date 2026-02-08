# Visual Climate Engine: Advanced UN Data Ecosystem (PRD v3.0)

## 1. 개요 (Overview)
본 프로젝트는 단순한 경제 지표를 넘어, UN 산하 기구들의 깊이 있는 기후 데이터 소스(FAO, IRENA, WHO 등)를 통합하여 실질적인 정책 결정과 현장 사업에 활용 가능한 **Visual Climate Engine**을 구축하는 것을 목표로 합니다.

## 2. 핵심 기능 및 데이터 소스 (Core Features & Data Sources)

### A. 금융 및 무역 (Finance & Trade)
*   **OECD**: 기후 변화 대응 예산(ODA), 탄소세 정책 지표 (SDMX)
*   **UNCTAD**: 녹색 산업 무역 지수, 탄소 국경세 영향 분석

### B. 농업, 식량 및 기후 (Agriculture & Food)
*   **FAOSTAT**: 농업 배출량, 작물 생산성 변화, 메탄 발생 데이터
*   **목적**: 식량 안보 대시보드 구축

### C. 산업 및 재생 에너지 (Industry & Energy)
*   **IRENA**: 재생에너지 설치 용량, 비용 트렌드, 에너지 전환 속도
*   **UNIDO**: 제조업 탄소 집약도, 산업 공정 효율

### D. 보건 및 인간 개발 (Health & Human Development)
*   **WHO**: 기후 관련 질병 확산(말라리아 등), 대기 오염 사망률
*   **UNDP**: 기후 리스크 반영 인간 개발 지수(PHDI)

## 3. 시스템 아키텍처 (System Architecture)

### Backend (Claude Code CLI 담당)
*   **언어/프레임워크**: Python (FastAPI 권장)
*   **멀티 에이전트 구조**:
    *   **Librarian Agent (Data Layer)**: 
        *   기구별 데이터 수집 (`src/collectors/deep_un.py`)
        *   데이터 충돌 해결 (목적별 선택 또는 앙상블)
        *   메타데이터 태깅 (출처, 갱신일, 신뢰도)
    *   **Analyst Agent (Inference Layer)**:
        *   Cross-Agency 분석 (예: 에너지 예산과 아동 보건 상관관계)
*   **기능**: SDMX, JSON 등 다양한 포맷 처리 및 통합 API 제공

### Frontend (Antigravity 담당)
*   **기술 스택**: Next.js, Tailwind CSS, Recharts/D3.js
*   **기능**: 
    *   실시간 데이터 시각화
    *   인터렉티브 대시보드
    *   정책 브리핑 자동 생성 뷰

## 4. 데이터 파이프라인 워크플로우
1.  **Deep Data Scraper**: API/SDMX 엔드포인트에서 데이터 수집
2.  **Semantic Schema Mapping**: 이종 데이터 병합 (예: FAO + IEA = National Total Emission)
3.  **Multi-Agent Collaboration**: 데이터와 텍스트(정책 문서) 결합
4.  **Zero-Hallucination Guardrail**: 데이터 상충 시 리포팅 (AI 임의 판단 배제)

---
**목표**: "지루함을 파괴하는 플랫폼". 30초 만에 데이터 결합 및 보고서 초안 완성.
