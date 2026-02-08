"""
UN Data Lake — Production ETL pipeline.

Fetches 50+ World Bank indicators organized by 4 policy clusters,
spanning 1990-2023 across 200+ countries.  Parallel async fetching
with local JSON cache to avoid redundant API calls.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import requests

# ──────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────

WB_BASE_URL = "https://api.worldbank.org/v2"
DATE_RANGE = "1990:2023"
PER_PAGE = 20000
CACHE_MAX_AGE_HOURS = int(os.getenv("WB_CACHE_HOURS", "24"))

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_CACHE_FILE = _CACHE_DIR / "world_bank_cache.json"

_executor = ThreadPoolExecutor(max_workers=12)

# World Bank aggregate / region codes — not real countries
WB_AGGREGATE_CODES = {
    "WLD", "EAS", "ECS", "LCN", "MEA", "NAC", "SAS", "SSF",
    "EAP", "ECA", "LAC", "MNA", "SSA", "HIC", "LIC", "LMC",
    "LMY", "MIC", "UMC", "ARB", "CEB", "CSS", "EAR", "EMU",
    "FCS", "HPC", "IBD", "IBT", "IDA", "IDB", "IDX", "INX",
    "LDC", "LTE", "OED", "OSS", "PRE", "PSS", "PST", "SST",
    "TEA", "TEC", "TLA", "TMN", "TSA", "TSS", "AFE", "AFW",
}

# ──────────────────────────────────────────────────────────────────────
# POLICY CLUSTERS — organized by actual UN officer needs
# ──────────────────────────────────────────────────────────────────────

CLUSTERS: dict[str, dict] = {
    # ── 1. Energy Transition ──────────────────────────────────────────
    "energy_transition": {
        "description": "Is this country actually decarbonizing, or just greenwashing?",
        "indicators": {
            "co2_emissions":              "EN.GHG.CO2.PC.CE.AR5",
            "renewable_energy":           "EG.FEC.RNEW.ZS",
            "fossil_fuel_energy_pct":     "EG.USE.COMM.FO.ZS",
            "access_electricity":         "EG.ELC.ACCS.ZS",
            "electric_power_kwh":         "EG.USE.ELEC.KH.PC",
            "energy_use_per_capita":      "EG.USE.PCAP.KG.OE",
            "alt_nuclear_energy_pct":     "EG.USE.COMM.CL.ZS",
            "co2_from_transport_pct":     "EN.CO2.TRAN.ZS",
            "co2_from_manufacturing_pct": "EN.CO2.MANF.ZS",
            "co2_from_electricity_pct":   "EN.CO2.ETOT.ZS",
            "energy_intensity":           "EG.EGY.PRIM.PP.KD",
            "elec_from_coal_pct":         "EG.ELC.COAL.ZS",
            "elec_from_gas_pct":          "EG.ELC.NGAS.ZS",
            "elec_from_oil_pct":          "EG.ELC.PETR.ZS",
            "elec_from_hydro_pct":        "EG.ELC.HYRO.ZS",
            "elec_from_nuclear_pct":      "EG.ELC.NUCL.ZS",
        },
    },
    # ── 2. Agricultural Resilience ────────────────────────────────────
    "agricultural_resilience": {
        "description": "Will food security collapse under +2°C warming?",
        "indicators": {
            "cereal_yield":                "AG.YLD.CREL.KG",
            "agricultural_land_pct":       "AG.LND.AGRI.ZS",
            "arable_land_pct":             "AG.LND.ARBL.ZS",
            "fertilizer_consumption":      "AG.CON.FERT.ZS",
            "food_production_index":       "AG.PRD.FOOD.XD",
            "crop_production_index":       "AG.PRD.CROP.XD",
            "livestock_production_index":  "AG.PRD.LVSK.XD",
            "methane_agriculture_pct":     "EN.ATM.METH.AG.ZS",
            "n2o_agriculture_pct":         "EN.ATM.NOXE.AG.ZS",
            "freshwater_withdrawal_agri":  "ER.H2O.FWAG.ZS",
            "freshwater_per_capita":       "ER.H2O.INTR.PC",
            "agriculture_value_added_pct": "NV.AGR.TOTL.ZS",
            "employment_agriculture_pct":  "SL.AGR.EMPL.ZS",
            "forest_area_pct":             "AG.LND.FRST.ZS",
        },
    },
    # ── 3. Urban Health ───────────────────────────────────────────────
    "urban_health": {
        "description": "Are cities becoming death traps due to pollution and heat?",
        "indicators": {
            "pm25_exposure":              "EN.ATM.PM25.MC.M3",
            "pm25_pop_exposed_pct":       "EN.ATM.PM25.MC.ZS",
            "urban_population_pct":       "SP.URB.TOTL.IN.ZS",
            "urban_population_growth":    "SP.URB.GROW",
            "sanitation_safe_pct":        "SH.STA.SMSS.ZS",
            "water_safe_pct":             "SH.H2O.SMDW.ZS",
            "sanitation_basic_pct":       "SH.STA.BASS.ZS",
            "water_basic_pct":            "SH.H2O.BASW.ZS",
            "mortality_under5":           "SH.DYN.MORT",
            "life_expectancy":            "SP.DYN.LE00.IN",
            "health_expenditure_pct_gdp": "SH.XPD.CHEX.GD.ZS",
            "population_density":         "EN.POP.DNST",
            "population_total":           "SP.POP.TOTL",
        },
    },
    # ── 4. Economic Risk ──────────────────────────────────────────────
    "economic_risk": {
        "description": "Is the economy too dependent on extracting resources?",
        "indicators": {
            "gdp_per_capita":             "NY.GDP.PCAP.CD",
            "gdp_growth":                 "NY.GDP.MKTP.KD.ZG",
            "inflation":                  "FP.CPI.TOTL.ZG",
            "fdi_net_inflows_pct":        "BX.KLT.DINV.WD.GD.ZS",
            "natural_resource_rents_pct": "NY.GDP.TOTL.RT.ZS",
            "oil_rents_pct":              "NY.GDP.PETR.RT.ZS",
            "coal_rents_pct":             "NY.GDP.COAL.RT.ZS",
            "mineral_rents_pct":          "NY.GDP.MINR.RT.ZS",
            "gas_rents_pct":              "NY.GDP.NGAS.RT.ZS",
            "forest_rents_pct":           "NY.GDP.FRST.RT.ZS",
            "trade_pct_gdp":              "NE.TRD.GNFS.ZS",
            "external_debt_pct_gni":      "DT.DOD.DECT.GN.ZS",
            "gross_capital_formation_pct": "NE.GDI.TOTL.ZS",
            "current_account_balance_pct": "BN.CAB.XOKA.GD.ZS",
        },
    },
}

# ── Flat INDICATORS dict (backward compatibility) ────────────────────
# Every indicator from every cluster, keyed by its short name.
INDICATORS: dict[str, str] = {}
for _cluster_def in CLUSTERS.values():
    INDICATORS.update(_cluster_def["indicators"])

# Reverse lookup: indicator_name -> cluster_name
INDICATOR_TO_CLUSTER: dict[str, str] = {}
for _cname, _cdef in CLUSTERS.items():
    for _iname in _cdef["indicators"]:
        INDICATOR_TO_CLUSTER[_iname] = _cname


# ──────────────────────────────────────────────────────────────────────
# CACHE LAYER
# ──────────────────────────────────────────────────────────────────────

def _load_cache() -> Optional[dict]:
    """Load cached raw records from disk if fresh enough."""
    if not _CACHE_FILE.exists():
        return None
    try:
        raw = _CACHE_FILE.read_text(encoding="utf-8")
        cache = json.loads(raw)
        ts = cache.get("_meta", {}).get("timestamp", 0)
        age_hours = (time.time() - ts) / 3600
        if age_hours > CACHE_MAX_AGE_HOURS:
            print(f"[ETL] Cache expired ({age_hours:.1f}h old). Will re-fetch.")
            return None
        print(f"[ETL] Using cached data ({age_hours:.1f}h old, {len(cache) - 1} indicators).")
        return cache
    except Exception as exc:
        print(f"[ETL] Cache read error: {exc}")
        return None


def _save_cache(data: dict[str, list[dict]]) -> None:
    """Persist raw API records to disk."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache = {"_meta": {"timestamp": time.time()}}
        cache.update(data)
        _CACHE_FILE.write_text(
            json.dumps(cache, separators=(",", ":")),
            encoding="utf-8",
        )
        size_mb = _CACHE_FILE.stat().st_size / (1024 * 1024)
        print(f"[ETL] Cache saved → {_CACHE_FILE} ({size_mb:.1f} MB)")
    except Exception as exc:
        print(f"[ETL] Cache write error: {exc}")


# ──────────────────────────────────────────────────────────────────────
# COLLECTOR
# ──────────────────────────────────────────────────────────────────────

class DeepUNCollector:
    """
    Production ETL collector.  Fetches 50+ World Bank indicators organized
    by policy cluster, transforms into structured Pandas DataFrames,
    and caches raw data locally.
    """

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "UNDataLake/2.0"})

        # indicator_name -> DataFrame(index=year, columns=iso3)
        self._dataframes: dict[str, pd.DataFrame] = {}
        # iso3 -> country_name
        self._country_names: dict[str, str] = {}
        self._loaded = False

    # ── EXTRACT ───────────────────────────────────────────────────────

    def _fetch_indicator_sync(self, indicator_code: str) -> list[dict]:
        """Fetch a single indicator for all countries, all years."""
        url = (
            f"{WB_BASE_URL}/country/all/indicator/{indicator_code}"
            f"?format=json&per_page={PER_PAGE}&date={DATE_RANGE}"
        )
        try:
            resp = self._session.get(url, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            if len(payload) > 1 and isinstance(payload[1], list):
                return payload[1]
        except Exception as exc:
            print(f"[ETL] ✗ {indicator_code}: {exc}")
        return []

    async def _fetch_indicator(self, name: str, code: str) -> tuple[str, list[dict]]:
        """Async wrapper — runs the blocking HTTP call in the thread pool."""
        loop = asyncio.get_running_loop()
        records = await loop.run_in_executor(
            _executor, self._fetch_indicator_sync, code,
        )
        if records:
            print(f"[ETL] ✓ {name} ({code}) — {len(records)} records")
        else:
            print(f"[ETL] ⚠ {name} ({code}) — 0 records")
        return name, records

    # ── TRANSFORM ─────────────────────────────────────────────────────

    @staticmethod
    def _records_to_dataframe(records: list[dict]) -> tuple[pd.DataFrame, dict[str, str]]:
        """
        Convert raw WB JSON records into a pivoted DataFrame.
        Returns (df[index=year, columns=iso3], {iso3: country_name}).
        """
        if not records:
            return pd.DataFrame(), {}

        rows: list[dict] = []
        names: dict[str, str] = {}
        for rec in records:
            iso3 = rec.get("countryiso3code", "")
            if not iso3 or iso3 in WB_AGGREGATE_CODES:
                continue
            year = rec.get("date")
            value = rec.get("value")
            if year is None:
                continue
            rows.append({"iso3": iso3, "year": int(year), "value": value})
            country_obj = rec.get("country", {})
            if iso3 not in names and isinstance(country_obj, dict):
                names[iso3] = country_obj.get("value", iso3)

        if not rows:
            return pd.DataFrame(), names

        df = pd.DataFrame(rows)
        pivot = df.pivot_table(
            index="year", columns="iso3", values="value", aggfunc="first",
        )
        pivot.sort_index(inplace=True)
        pivot = pivot.interpolate(method="linear", limit=3, axis=0)
        return pivot, names

    @staticmethod
    def _compute_growth_rate(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """Rolling N-year CAGR: (end/start)^(1/n) - 1."""
        if df.empty or len(df) < window:
            return pd.DataFrame()
        start = df.shift(window)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = df / start
            valid = (df > 0) & (start > 0)
            growth = np.where(valid, np.power(ratio, 1.0 / window) - 1, np.nan)
        return pd.DataFrame(growth, index=df.index, columns=df.columns)

    # ── LOAD ──────────────────────────────────────────────────────────

    async def load_all(self) -> None:
        """Fetch and process ALL cluster indicators in parallel.  Idempotent."""
        if self._loaded:
            return

        total = len(INDICATORS)
        print(f"[ETL] ═══ UN Data Lake: loading {total} indicators across "
              f"{len(CLUSTERS)} clusters (date range {DATE_RANGE}) ═══")

        # Try cache first
        cached = _load_cache()
        raw_data: dict[str, list[dict]] = {}

        if cached:
            # Hydrate from cache — any missing indicators will be fetched
            for name in INDICATORS:
                if name in cached:
                    raw_data[name] = cached[name]
            missing = [n for n in INDICATORS if n not in raw_data]
            if missing:
                print(f"[ETL] Cache hit for {len(raw_data)}/{total} indicators. "
                      f"Fetching {len(missing)} missing…")
                tasks = [
                    self._fetch_indicator(name, INDICATORS[name])
                    for name in missing
                ]
                results = await asyncio.gather(*tasks)
                for name, records in results:
                    raw_data[name] = records
                _save_cache(raw_data)
            else:
                print(f"[ETL] Full cache hit — {total} indicators.")
        else:
            # Fetch everything — go cluster by cluster for clear logging
            for cluster_name, cluster_def in CLUSTERS.items():
                indicators = cluster_def["indicators"]
                print(f"[ETL] ── Cluster: {cluster_name} ({len(indicators)} indicators) ──")
                tasks = [
                    self._fetch_indicator(name, code)
                    for name, code in indicators.items()
                ]
                results = await asyncio.gather(*tasks)
                for name, records in results:
                    raw_data[name] = records
            _save_cache(raw_data)

        # Transform raw records → DataFrames
        success_count = 0
        for name, records in raw_data.items():
            df, names = self._records_to_dataframe(records)
            self._dataframes[name] = df
            self._country_names.update(names)
            if not df.empty:
                success_count += 1

        # Pre-compute 5-year growth rates for every base indicator
        for name in list(INDICATORS.keys()):
            df = self._dataframes.get(name, pd.DataFrame())
            growth_key = f"{name}_growth_5y"
            self._dataframes[growth_key] = self._compute_growth_rate(df, window=5)

        self._loaded = True
        n_countries = len(self._country_names)
        max_years = max(
            (len(df) for df in self._dataframes.values() if not df.empty),
            default=0,
        )
        print(f"[ETL] ═══ Data Lake Ready: {success_count}/{total} indicators, "
              f"{n_countries} countries, {max_years} years ═══")

    def invalidate_cache(self) -> None:
        """Force reload on next access."""
        self._dataframes.clear()
        self._country_names.clear()
        self._loaded = False

    # ── PUBLIC DATA ACCESS ────────────────────────────────────────────

    def get_indicator_df(self, indicator: str) -> pd.DataFrame:
        return self._dataframes.get(indicator, pd.DataFrame())

    def get_all_indicator_names(self) -> list[str]:
        return list(INDICATORS.keys())

    def get_country_name(self, iso3: str) -> str:
        return self._country_names.get(iso3, iso3)

    def get_all_countries(self) -> list[str]:
        countries: set[str] = set()
        for df in self._dataframes.values():
            if not df.empty:
                countries.update(df.columns.tolist())
        return sorted(countries)

    def get_country_series(self, iso3: str, indicator: str) -> pd.Series:
        df = self.get_indicator_df(indicator)
        if df.empty or iso3 not in df.columns:
            return pd.Series(dtype=float)
        return df[iso3].dropna()

    def get_latest_values(self, indicator: str) -> pd.Series:
        df = self.get_indicator_df(indicator)
        if df.empty:
            return pd.Series(dtype=float)
        return df.apply(
            lambda col: col.dropna().iloc[-1] if not col.dropna().empty else np.nan,
        )

    def build_master_snapshot(self) -> list[dict]:
        """Unified latest-year snapshot for v1 compatibility."""
        countries = self.get_all_countries()
        rows = []
        for iso3 in countries:
            row = {"iso3": iso3, "country": self.get_country_name(iso3)}
            for indicator in INDICATORS:
                series = self.get_country_series(iso3, indicator)
                row[indicator] = float(series.iloc[-1]) if not series.empty else None
            rows.append(row)
        return rows

    # ── CLUSTER-LEVEL ACCESS ──────────────────────────────────────────

    def get_cluster_names(self) -> list[str]:
        return list(CLUSTERS.keys())

    def get_cluster_indicators(self, cluster: str) -> list[str]:
        cdef = CLUSTERS.get(cluster)
        if not cdef:
            return []
        return list(cdef["indicators"].keys())

    def get_cluster_data(self, cluster_name: str) -> dict:
        """
        Build deep nested structure for a cluster:
        { "ISO3": { "1990": { "indicator_a": val, ... }, "1991": ... }, ... }
        """
        cdef = CLUSTERS.get(cluster_name)
        if not cdef:
            return {}

        indicator_names = list(cdef["indicators"].keys())
        countries = self.get_all_countries()
        result: dict[str, dict] = {}

        for iso3 in countries:
            country_data: dict[str, dict] = {}
            has_any = False
            for ind_name in indicator_names:
                series = self.get_country_series(iso3, ind_name)
                for year, val in series.items():
                    yr_str = str(int(year))
                    if yr_str not in country_data:
                        country_data[yr_str] = {}
                    country_data[yr_str][ind_name] = round(float(val), 4)
                    has_any = True
            if has_any:
                result[iso3] = country_data

        return result

    def get_country_cluster_profile(self, iso3: str) -> dict:
        """
        Full profile for a country across ALL clusters (legacy format):
        { "energy_transition": { "1990": {...}, ... }, ... }
        """
        profile: dict[str, dict] = {}
        for cluster_name, cdef in CLUSTERS.items():
            cluster_data: dict[str, dict] = {}
            for ind_name in cdef["indicators"]:
                series = self.get_country_series(iso3, ind_name)
                for year, val in series.items():
                    yr_str = str(int(year))
                    if yr_str not in cluster_data:
                        cluster_data[yr_str] = {}
                    cluster_data[yr_str][ind_name] = round(float(val), 4)
            profile[cluster_name] = cluster_data
        return profile

    def get_country_profile_v2(self, iso3: str) -> dict:
        """
        API contract v1.0 compliant country profile.
        Returns:
        {
          "iso3": "KOR",
          "name": "Korea, Rep.",
          "data": {
            "energy_transition": {
              "co2_emissions": { "current": 11.58, "history": {"1990": 5.76, ...}, "growth_5y": -0.001 },
              ...
            }, ...
          }
        }
        """
        data: dict[str, dict] = {}
        for cluster_name, cdef in CLUSTERS.items():
            cluster_indicators: dict[str, dict] = {}
            for ind_name in cdef["indicators"]:
                series = self.get_country_series(iso3, ind_name)
                current = round(float(series.iloc[-1]), 4) if not series.empty else None
                history = {
                    str(int(yr)): round(float(val), 4)
                    for yr, val in series.items()
                }
                growth_series = self.get_country_series(iso3, f"{ind_name}_growth_5y")
                growth_5y = round(float(growth_series.iloc[-1]), 6) if not growth_series.empty else None
                cluster_indicators[ind_name] = {
                    "current": current,
                    "history": history,
                    "growth_5y": growth_5y,
                }
            data[cluster_name] = cluster_indicators
        return {
            "iso3": iso3,
            "name": self.get_country_name(iso3),
            "data": data,
        }

    def get_countries_meta(self) -> list[dict]:
        """Returns list of {iso3, name} for all countries with data."""
        countries = self.get_all_countries()
        return [
            {"iso3": c, "name": self.get_country_name(c)}
            for c in countries
        ]

    def get_indicators_meta(self) -> dict:
        """Returns cluster-grouped indicator metadata."""
        result = {}
        for cluster_name, cdef in CLUSTERS.items():
            result[cluster_name] = {
                "description": cdef["description"],
                "indicators": list(cdef["indicators"].keys()),
            }
        return result
