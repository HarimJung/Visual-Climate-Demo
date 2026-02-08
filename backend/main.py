"""
Visual Climate Engine — FastAPI Server
API Contract: docs/api-contract.md
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from src.collectors.deep_un import DeepUNCollector
from src.logic.analytics import calculate_correlation, detect_green_growth, forecast_trend

collector = DeepUNCollector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await collector.load_all()
    yield


app = FastAPI(title="Visual Climate Engine", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── v1 backward compatibility ──────────────────────────────────────

@app.get("/api/v1/data/master")
async def get_master_data():
    """Master snapshot of all countries/indicators (table view)."""
    return collector.build_master_snapshot()


# ── v2 core endpoints ──────────────────────────────────────────────

@app.get("/api/v2/country/{iso3}")
async def get_country_profile(iso3: str):
    """Full country profile across all 4 clusters (api-contract compliant)."""
    return collector.get_country_profile_v2(iso3.upper())


# ── v2 analytics ───────────────────────────────────────────────────

@app.get("/api/v2/analytics/correlation/{x_indicator}/{y_indicator}")
async def get_correlation(x_indicator: str, y_indicator: str):
    """Pearson correlation + scatter data for two indicators."""
    x_latest = collector.get_latest_values(x_indicator)
    y_latest = collector.get_latest_values(y_indicator)

    if x_latest.empty or y_latest.empty:
        return {"x_indicator": x_indicator, "y_indicator": y_indicator,
                "pearson_r": None, "p_value": None, "n_samples": 0, "scatter": []}

    result = calculate_correlation(x_latest, y_latest)

    # Enrich scatter points with country names
    for point in result.get("scatter", []):
        point["name"] = collector.get_country_name(point["iso3"])

    result["x_indicator"] = x_indicator
    result["y_indicator"] = y_indicator
    return result


@app.get("/api/v2/analytics/green-growth")
async def get_green_growth():
    """Countries decoupling GDP growth from CO2 emissions."""
    co2_growth = collector.get_latest_values("co2_emissions_growth_5y")
    gdp_growth = collector.get_latest_values("gdp_growth_growth_5y")

    rankings = detect_green_growth(co2_growth, gdp_growth, collector._country_names)

    total_analyzed = len(co2_growth.dropna().index.intersection(gdp_growth.dropna().index))
    return {
        "rankings": rankings,
        "total_green_countries": len(rankings),
        "total_analyzed": total_analyzed,
    }


@app.get("/api/v2/analytics/forecast/{iso3}/{indicator}")
async def get_forecast(iso3: str, indicator: str):
    """Linear regression trend forecast to 2030."""
    iso3 = iso3.upper()
    series = collector.get_country_series(iso3, indicator)

    if series.empty:
        return {"iso3": iso3, "indicator": indicator,
                "target_year": 2030, "predicted_value": None,
                "error": f"No data for {indicator} in {iso3}"}

    result = forecast_trend(series, target_year=2030)
    result["iso3"] = iso3
    result["indicator"] = indicator
    return result


# ── v2 meta endpoints ─────────────────────────────────────────────

@app.get("/api/v2/meta/countries")
async def get_countries():
    """List of all countries with data."""
    return collector.get_countries_meta()


@app.get("/api/v2/meta/indicators")
async def get_indicators():
    """Indicator list grouped by cluster."""
    return collector.get_indicators_meta()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
