# Mission: Build the "UN Data Lake" Architecture

## Core Problem
The current implementation is a "toy" because it fetches shallow, disconnected data (Snapshot 2020, 7 indicators).
Real policy officers need **Deep, Context-Specific Intelligence** drawn from **multiple sources (10+ APIs)** and **long time-series (1990-2023)**.

## 1. Data Strategy: The "Cluster Approach"

### A. Define Policy Clusters (The "Why")
Instead of random indicators, we organize data by **Actual Policy Needs**:

1.  **Energy Transition Officer**:
    *   Needs: Renewable % (WB), Fossil Fuel Subsidies (IMF/WB), Grid Access (WB), Nuclear/Coal phase-out (IEA proxy).
    *   Goal: "Is this country actually decarbonizing, or just greenwashing?"

2.  **Agricultural Resilience Officer**:
    *   Needs: Cereal Yield (FAO), Methane from Livestock (FAO), Fertilizer Use (FAO), Water Stress (WB), Temperature Anomalies (Open-Meteo).
    *   Goal: "Will food security collapse under +2°C warming?"

3.  **Urban Health Officer**:
    *   Needs: PM2.5 Exposure (WHO/WB), Urban Population Growth (WB), Access to Sanitation (WB), Fossil Fuel Transport % (WB).
    *   Goal: "Are cities becoming death traps due to pollution and heat?"

4.  **Economic Risk Officer**:
    *   Needs: GDP Growth (WB), Inflation (WB), Foreign Direct Investment (WB), Natural Resource Rents (WB).
    *   Goal: "Is the economy too dependent on extracting resources?"

### B. Massive Data Ingestion (The "How")
- **Source**: World Bank API (Primary), Open-Meteo (Climate), FAO (via WB proxies if direct API is hard).
- **Volume**: Fetch **50+ Indicators** across **200+ Countries** for **30 Years (1990-2023)**.
- **Method**: Use `pandas` and `asyncio` to parallelize requests. **Cache everything locally** (`data/world_bank_cache.json`) to avoid re-fetching.

## 2. Implementation Steps

### Step 1: `src/collectors/deep_un.py` (The Heavy Lifter)
- **Rewrite to fetch BY CLUSTER**.
- Define `CLUSTERS` dictionary mapping policy areas to WB Indicator Codes.
- Implement `fetch_all_clusters()`: Parallel fetch of all 50+ indicators.
- **Data Structure**: Deep nested JSON or Long-Format DataFrame:
  ```json
  {
    "USA": {
      "energy": { "1990": { "renewables": 5.2 }, "1991": ... },
      "agriculture": { ... }
    }
  }
  ```

### Step 2: `src/logic/analytics.py` (The Inspector)
- **Trend Calculation**: Calculate 5-year and 10-year CAGRs (Compound Annual Growth Rate) for every indicator.
- **Correlation**: `calculate_correlation(cluster_a, cluster_b)` (e.g., Does "Fertilizer Use" correlate with "N2O Emissions"?).
- **Ranking**: "Top 10 Fastest Decarbonizers", "Top 10 Most Vulnerable Ag-Economies".

### Step 3: `main.py` (The Librarian)
- `GET /api/v2/cluster/{cluster_name}`: Returns processed, time-series data for a specific domain.
- `GET /api/v2/country/{iso3}/full_profile`: Returns the **entire** dataset for a country.

## Execution Order
1.  **Stop Server.**
2.  **Rewrite `deep_un.py`** to handle the "Cluster" logic and massive fetching.
3.  **Start Server** and wait for the initial "Data Lake Filling" (might take 30-60s).
4.  **Verify** the new endpoints return complex, nested data.

**Do it. No more toys.**
