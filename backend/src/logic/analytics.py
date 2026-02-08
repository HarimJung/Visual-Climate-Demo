"""
Advanced analytics engine: correlation analysis, anomaly detection, trend forecasting.
Uses Scipy for statistics and NumPy/Pandas for vectorized operations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def calculate_correlation(
    x_series: pd.Series, y_series: pd.Series
) -> dict:
    """
    Compute Pearson correlation between two indicator series aligned by country.

    Args:
        x_series: pd.Series indexed by country ISO3
        y_series: pd.Series indexed by country ISO3

    Returns:
        dict with pearson_r, p_value, n_samples, and aligned scatter data points.
    """
    # Align on common countries with valid data
    combined = pd.DataFrame({"x": x_series, "y": y_series}).dropna()

    if len(combined) < 3:
        return {
            "pearson_r": None,
            "p_value": None,
            "n_samples": len(combined),
            "scatter": [],
            "error": "Insufficient data points (need >= 3).",
        }

    r, p = stats.pearsonr(combined["x"], combined["y"])

    scatter = [
        {"iso3": iso3, "x": float(row["x"]), "y": float(row["y"])}
        for iso3, row in combined.iterrows()
    ]

    return {
        "pearson_r": round(float(r), 4),
        "p_value": round(float(p), 6),
        "n_samples": len(combined),
        "scatter": scatter,
    }


def detect_green_growth(
    co2_growth: pd.Series,
    gdp_growth: pd.Series,
    country_names: dict[str, str],
    top_n: int = 10,
) -> list[dict]:
    """
    Identify countries that are decoupling economic growth from emissions:
    GDP growth is positive while CO2 growth is negative ("Green Growth" stars).

    Args:
        co2_growth: Series of 5-year CO2 CAGR indexed by iso3.
        gdp_growth: Series of 5-year GDP CAGR indexed by iso3.
        country_names: iso3 -> country name mapping.
        top_n: How many top performers to return.

    Returns:
        Sorted list of dicts with country info and decoupling score.
    """
    combined = pd.DataFrame({
        "co2_growth": co2_growth,
        "gdp_growth": gdp_growth,
    }).dropna()

    # Green growth = GDP rising AND CO2 falling
    green = combined[(combined["gdp_growth"] > 0) & (combined["co2_growth"] < 0)].copy()

    if green.empty:
        return []

    # Decoupling score: higher GDP growth + deeper CO2 decline = better
    green["decoupling_score"] = green["gdp_growth"] - green["co2_growth"]
    green.sort_values("decoupling_score", ascending=False, inplace=True)

    results = []
    for iso3, row in green.head(top_n).iterrows():
        results.append({
            "rank": len(results) + 1,
            "iso3": iso3,
            "country": country_names.get(iso3, iso3),
            "gdp_growth_5y": round(float(row["gdp_growth"]) * 100, 2),
            "co2_growth_5y": round(float(row["co2_growth"]) * 100, 2),
            "decoupling_score": round(float(row["decoupling_score"]) * 100, 2),
        })

    return results


def forecast_trend(
    series: pd.Series, target_year: int = 2030
) -> dict:
    """
    Simple linear regression on a time-series to project a future value.

    Args:
        series: pd.Series with integer year index and float values.
        target_year: Year to project to.

    Returns:
        dict with slope, intercept, r_squared, predicted value, and trend data.
    """
    clean = series.dropna()
    if len(clean) < 3:
        return {
            "predicted_value": None,
            "target_year": target_year,
            "error": "Insufficient data for trend analysis.",
        }

    x = clean.index.values.astype(float)
    y = clean.values.astype(float)

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    predicted = slope * target_year + intercept

    # Build trend line for the historical range + projection
    trend_points = []
    for yr in clean.index:
        trend_points.append({
            "year": int(yr),
            "actual": round(float(clean[yr]), 4),
            "trend": round(float(slope * yr + intercept), 4),
        })
    # Add projection point
    trend_points.append({
        "year": target_year,
        "actual": None,
        "trend": round(float(predicted), 4),
    })

    return {
        "target_year": target_year,
        "predicted_value": round(float(predicted), 4),
        "slope_per_year": round(float(slope), 6),
        "r_squared": round(float(r_value ** 2), 4),
        "p_value": round(float(p_value), 6),
        "trend_points": trend_points,
    }


def build_country_report(
    iso3: str,
    country_name: str,
    collector,
) -> dict:
    """
    Generate a full analytical report for a single country:
    time-series for each indicator + 2030 projections.
    """
    from src.collectors.deep_un import INDICATORS

    report = {
        "iso3": iso3,
        "country": country_name,
        "indicators": {},
    }

    for indicator in INDICATORS:
        series = collector.get_country_series(iso3, indicator)
        if series.empty:
            report["indicators"][indicator] = {"time_series": [], "forecast": None}
            continue

        ts_data = [
            {"year": int(yr), "value": round(float(val), 4)}
            for yr, val in series.items()
        ]

        fc = forecast_trend(series, target_year=2030)

        # Also include 5-year growth
        growth_series = collector.get_country_series(iso3, f"{indicator}_growth_5y")
        latest_growth = None
        if not growth_series.empty:
            latest_growth = round(float(growth_series.iloc[-1]) * 100, 2)

        report["indicators"][indicator] = {
            "time_series": ts_data,
            "latest_value": round(float(series.iloc[-1]), 4),
            "growth_5y_pct": latest_growth,
            "forecast": fc,
        }

    return report
