# API Contract v1.0

> 이 문서는 백엔드(Claude Code)와 프론트엔드(Antigravity)의 **공식 계약서**입니다.
> 양쪽 모두 이 스키마를 준수해야 합니다. 변경 시 양쪽 합의 필수.

---

## Base URL

```
Development: http://localhost:8000
```

---

## Endpoints

### 1. `GET /api/v2/country/{iso3}`

국가별 전체 프로필. 4개 클러스터의 모든 인디케이터 데이터.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `iso3` | path (string) | ISO 3166-1 alpha-3 국가 코드 (예: `KOR`, `USA`) |

**Response: `CountryProfileResponse`**

```json
{
  "iso3": "KOR",
  "name": "Korea, Rep.",
  "data": {
    "energy_transition": {
      "co2_emissions": {
        "current": 11.58,
        "history": { "1990": 5.76, "1995": 8.34, "2000": 9.48, "2005": 9.73, "2010": 11.46, "2015": 11.62, "2020": 10.58, "2023": 11.58 },
        "growth_5y": -0.0012
      },
      "renewable_energy": {
        "current": 2.51,
        "history": { "1990": 1.02, "1995": 1.14, "2000": 1.08, "2005": 1.24, "2010": 1.52, "2015": 2.14, "2020": 2.33, "2023": 2.51 },
        "growth_5y": 0.032
      }
    },
    "agricultural_resilience": { ... },
    "urban_health": { ... },
    "economic_risk": { ... }
  }
}
```

---

### 2. `GET /api/v1/data/master`

모든 국가의 최신 지표 스냅샷. 메인 테이블/그리드용.

**Response: `MasterDataResponse`**

```json
[
  {
    "iso3": "KOR",
    "country": "Korea, Rep.",
    "co2_emissions": 11.58,
    "renewable_energy": 2.51,
    "gdp_per_capita": 32422.15,
    ...
  },
  ...
]
```

---

### 3. `GET /api/v2/analytics/correlation/{x_indicator}/{y_indicator}`

두 인디케이터 간 Pearson 상관분석 + 산점도 데이터.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `x_indicator` | path (string) | X축 인디케이터 키 (예: `co2_emissions`) |
| `y_indicator` | path (string) | Y축 인디케이터 키 (예: `gdp_per_capita`) |

**Response: `CorrelationResponse`**

```json
{
  "x_indicator": "co2_emissions",
  "y_indicator": "gdp_per_capita",
  "pearson_r": 0.3215,
  "p_value": 0.000012,
  "n_samples": 187,
  "scatter": [
    { "iso3": "KOR", "name": "Korea, Rep.", "x": 11.58, "y": 32422.15 },
    { "iso3": "USA", "name": "United States", "x": 14.24, "y": 63544.00 },
    ...
  ]
}
```

---

### 4. `GET /api/v2/analytics/green-growth`

GDP 성장 + CO2 감소를 동시에 달성한 "그린 성장" 국가 랭킹.

**Response: `GreenGrowthResponse`**

```json
{
  "rankings": [
    {
      "rank": 1,
      "iso3": "EST",
      "country": "Estonia",
      "gdp_growth_5y": 4.52,
      "co2_growth_5y": -3.21,
      "decoupling_score": 7.73
    },
    ...
  ],
  "total_green_countries": 42,
  "total_analyzed": 187
}
```

---

### 5. `GET /api/v2/analytics/forecast/{iso3}/{indicator}`

특정 국가/인디케이터의 2030년 선형 회귀 예측.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `iso3` | path (string) | 국가 코드 |
| `indicator` | path (string) | 인디케이터 키 (예: `renewable_energy`) |

**Response: `ForecastResponse`**

```json
{
  "iso3": "KOR",
  "indicator": "renewable_energy",
  "target_year": 2030,
  "predicted_value": 3.84,
  "slope_per_year": 0.0521,
  "r_squared": 0.9124,
  "p_value": 0.000001,
  "trend_points": [
    { "year": 1990, "actual": 1.02, "trend": 0.95 },
    { "year": 2000, "actual": 1.08, "trend": 1.47 },
    { "year": 2010, "actual": 1.52, "trend": 1.99 },
    { "year": 2020, "actual": 2.33, "trend": 2.51 },
    { "year": 2023, "actual": 2.51, "trend": 2.67 },
    { "year": 2030, "actual": null, "trend": 3.84 }
  ]
}
```

---

### 6. `GET /api/v2/meta/countries`

사용 가능한 전체 국가 목록. 프론트엔드 드롭다운용.

**Response:**

```json
[
  { "iso3": "KOR", "name": "Korea, Rep." },
  { "iso3": "USA", "name": "United States" },
  ...
]
```

---

### 7. `GET /api/v2/meta/indicators`

사용 가능한 전체 인디케이터 목록. 클러스터별 그룹핑 포함.

**Response:**

```json
{
  "energy_transition": {
    "description": "Is this country actually decarbonizing, or just greenwashing?",
    "indicators": ["co2_emissions", "renewable_energy", "fossil_fuel_energy_pct", "access_electricity", ...]
  },
  "agricultural_resilience": { ... },
  "urban_health": { ... },
  "economic_risk": { ... }
}
```

---

## TypeScript Interfaces

프론트엔드에서 사용할 타입 정의:

```typescript
// === Core Types ===

interface IndicatorData {
  current: number | null;
  history: Record<string, number>;   // "1990" -> 5.76
  growth_5y: number | null;          // 5년 CAGR (소수, 예: 0.032 = 3.2%)
}

interface ClusterGroup {
  [indicatorKey: string]: IndicatorData;
}

interface CountryProfileResponse {
  iso3: string;
  name: string;
  data: {
    energy_transition: ClusterGroup;
    agricultural_resilience: ClusterGroup;
    urban_health: ClusterGroup;
    economic_risk: ClusterGroup;
  };
}

// === Master Data ===

interface MasterCountryRow {
  iso3: string;
  country: string;
  [indicatorKey: string]: string | number | null;
}

type MasterDataResponse = MasterCountryRow[];

// === Analytics ===

interface ScatterPoint {
  iso3: string;
  name: string;
  x: number;
  y: number;
}

interface CorrelationResponse {
  x_indicator: string;
  y_indicator: string;
  pearson_r: number | null;
  p_value: number | null;
  n_samples: number;
  scatter: ScatterPoint[];
}

interface GreenGrowthEntry {
  rank: number;
  iso3: string;
  country: string;
  gdp_growth_5y: number;
  co2_growth_5y: number;
  decoupling_score: number;
}

interface GreenGrowthResponse {
  rankings: GreenGrowthEntry[];
  total_green_countries: number;
  total_analyzed: number;
}

interface TrendPoint {
  year: number;
  actual: number | null;
  trend: number;
}

interface ForecastResponse {
  iso3: string;
  indicator: string;
  target_year: number;
  predicted_value: number | null;
  slope_per_year: number;
  r_squared: number;
  p_value: number;
  trend_points: TrendPoint[];
}

// === Meta ===

interface CountryMeta {
  iso3: string;
  name: string;
}

interface IndicatorsMeta {
  [clusterName: string]: {
    description: string;
    indicators: string[];
  };
}
```

---

## Indicator Keys (백엔드-프론트엔드 공통)

아래 키 이름은 **백엔드 응답의 JSON 키**이자 **프론트엔드가 참조하는 키**입니다.

### Energy Transition
| Key | Description | Unit |
|-----|-------------|------|
| `co2_emissions` | CO2 emissions (GHG, per capita) | t/cap |
| `renewable_energy` | Renewable energy share | % |
| `fossil_fuel_energy_pct` | Fossil fuel energy consumption | % |
| `access_electricity` | Access to electricity | % |
| `electric_power_kwh` | Electric power consumption | kWh/cap |
| `energy_use_per_capita` | Energy use per capita | kg oil eq |
| `alt_nuclear_energy_pct` | Alternative & nuclear energy | % |
| `co2_from_transport_pct` | CO2 from transport | % |
| `co2_from_manufacturing_pct` | CO2 from manufacturing | % |
| `co2_from_electricity_pct` | CO2 from electricity/heat | % |
| `energy_intensity` | Energy intensity of GDP | MJ/$ |
| `elec_from_coal_pct` | Electricity from coal | % |
| `elec_from_gas_pct` | Electricity from natural gas | % |
| `elec_from_oil_pct` | Electricity from oil | % |
| `elec_from_hydro_pct` | Electricity from hydroelectric | % |
| `elec_from_nuclear_pct` | Electricity from nuclear | % |

### Agricultural Resilience
| Key | Description | Unit |
|-----|-------------|------|
| `cereal_yield` | Cereal yield | kg/ha |
| `agricultural_land_pct` | Agricultural land | % |
| `arable_land_pct` | Arable land | % |
| `fertilizer_consumption` | Fertilizer consumption | kg/ha |
| `food_production_index` | Food production index | index |
| `crop_production_index` | Crop production index | index |
| `livestock_production_index` | Livestock production index | index |
| `methane_agriculture_pct` | Methane from agriculture | % |
| `n2o_agriculture_pct` | N2O from agriculture | % |
| `freshwater_withdrawal_agri` | Freshwater withdrawal (agri) | % |
| `freshwater_per_capita` | Freshwater per capita | m3/cap |
| `agriculture_value_added_pct` | Agriculture value added | % GDP |
| `employment_agriculture_pct` | Employment in agriculture | % |
| `forest_area_pct` | Forest area | % |

### Urban Health
| Key | Description | Unit |
|-----|-------------|------|
| `pm25_exposure` | PM2.5 air pollution exposure | ug/m3 |
| `pm25_pop_exposed_pct` | Population exposed to PM2.5 | % |
| `urban_population_pct` | Urban population | % |
| `urban_population_growth` | Urban population growth | % |
| `sanitation_safe_pct` | Safely managed sanitation | % |
| `water_safe_pct` | Safely managed water | % |
| `sanitation_basic_pct` | Basic sanitation access | % |
| `water_basic_pct` | Basic water access | % |
| `mortality_under5` | Under-5 mortality rate | per 1000 |
| `life_expectancy` | Life expectancy at birth | years |
| `health_expenditure_pct_gdp` | Health expenditure | % GDP |
| `population_density` | Population density | ppl/km2 |
| `population_total` | Total population | people |

### Economic Risk
| Key | Description | Unit |
|-----|-------------|------|
| `gdp_per_capita` | GDP per capita | USD |
| `gdp_growth` | GDP growth | % |
| `inflation` | Consumer price inflation | % |
| `fdi_net_inflows_pct` | Foreign direct investment | % GDP |
| `natural_resource_rents_pct` | Natural resource rents | % GDP |
| `oil_rents_pct` | Oil rents | % GDP |
| `coal_rents_pct` | Coal rents | % GDP |
| `mineral_rents_pct` | Mineral rents | % GDP |
| `gas_rents_pct` | Natural gas rents | % GDP |
| `forest_rents_pct` | Forest rents | % GDP |
| `trade_pct_gdp` | Trade | % GDP |
| `external_debt_pct_gni` | External debt stocks | % GNI |
| `gross_capital_formation_pct` | Gross capital formation | % GDP |
| `current_account_balance_pct` | Current account balance | % GDP |
