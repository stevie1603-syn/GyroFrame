"""KPI calculation engine. Deterministic, no LLM."""

import pandas as pd
from typing import Any


FIXED_COST_CATEGORIES = {"Affitto & Ufficio", "Personale", "Utilities", "Banche & Finanza"}
VARIABLE_COST_CATEGORIES = {"Marketing", "Software & SaaS", "Fornitori", "Altro"}
REVENUE_CATEGORIES = {"Entrate"}


def compute_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """
    Compute KPIs from a categorized transactions DataFrame.
    Expects columns: date, amount, category.
    Positive amount = income, negative = expense.
    """
    if df.empty:
        return {}

    revenue = df[df["category"].isin(REVENUE_CATEGORIES)]["amount"].sum()
    expenses = df[~df["category"].isin(REVENUE_CATEGORIES)]["amount"].sum()

    fixed_costs = df[df["category"].isin(FIXED_COST_CATEGORIES)]["amount"].sum()
    variable_costs = df[df["category"].isin(VARIABLE_COST_CATEGORIES)]["amount"].sum()

    gross_margin = revenue + expenses  # expenses are negative
    burn_rate = abs(expenses)
    runway_months = None
    if burn_rate > 0:
        runway_months = round(revenue / burn_rate, 1) if revenue > 0 else 0

    by_category = (
        df.groupby("category")["amount"]
        .sum()
        .round(2)
        .to_dict()
    )

    return {
        "revenue": round(revenue, 2),
        "total_expenses": round(abs(expenses), 2),
        "fixed_costs": round(abs(fixed_costs), 2),
        "variable_costs": round(abs(variable_costs), 2),
        "gross_margin": round(gross_margin, 2),
        "burn_rate": round(burn_rate, 2),
        "runway_months": runway_months,
        "by_category": by_category,
        "transaction_count": len(df),
    }


def compute_monthly_kpis(df: pd.DataFrame) -> dict[str, dict]:
    """KPIs grouped by month (YYYY-MM)."""
    if "date" not in df.columns:
        return {}
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    result = {}
    for month, group in df.groupby("month"):
        result[month] = compute_kpis(group.drop(columns=["month"]))
    return result


def compute_mom_delta(monthly: dict[str, dict]) -> list[dict]:
    """Month-over-month deltas for burn_rate and revenue."""
    months = sorted(monthly.keys())
    deltas = []
    for i in range(1, len(months)):
        prev, curr = months[i - 1], months[i]
        p, c = monthly[prev], monthly[curr]

        def pct(a, b):
            if b == 0:
                return None
            return round((a - b) / abs(b) * 100, 1)

        deltas.append({
            "from": prev,
            "to": curr,
            "revenue_delta_pct": pct(c["revenue"], p["revenue"]),
            "burn_rate_delta_pct": pct(c["burn_rate"], p["burn_rate"]),
            "margin_delta_pct": pct(c["gross_margin"], p["gross_margin"]),
        })
    return deltas
