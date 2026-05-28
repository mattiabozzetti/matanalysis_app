from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from .league_style import (
    METRIC_SPECS as LEAGUE_METRIC_SPECS,
    apply_possession_adjustment,
    enrich_team_features,
    flag_for_nation,
    load_team_league_base,
    metric_series as league_metric_series,
)

BASE_METRICS: dict[str, dict[str, Any]] = {
    **LEAGUE_METRIC_SPECS,
    "Goals": {"column": "Goals", "fmt": "0.00", "adjustment": "on_ball", "higher_is_better": True},
    "Goals total": {"column": "Goals total derived", "fmt": "0.0", "adjustment": "none", "higher_is_better": True},
    "xG total": {"column": "xG total derived", "fmt": "0.0", "adjustment": "none", "higher_is_better": True},
    "xA total": {"column": "xA total derived", "fmt": "0.0", "adjustment": "none", "higher_is_better": True},
    "Goals - xG": {"column": "Goals - xG", "fmt": "0.00", "adjustment": "none", "higher_is_better": True},
    "Goals - xG total": {"column": "Goals - xG total derived", "fmt": "0.0", "adjustment": "none", "higher_is_better": True},
    "Goal overperformance %": {"column": "Goal overperformance %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Goal overperformance total %": {"column": "Goal overperformance total %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Goals per shot": {"column": "Goals per shot", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Actions in box success %": {"column": "Actions in opponent's box successful, %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
}

STYLE_INDEX_COMPONENTS: dict[str, list[dict[str, Any]]] = {
    "Directness": [
        {"metric": "Long pass share", "higher_is_better": True},
        {"metric": "Super long pass share", "higher_is_better": True},
        {"metric": "Forward pass share", "higher_is_better": True},
        {"metric": "Goal kick long share", "higher_is_better": True},
        {"metric": "Progressive pass share", "higher_is_better": True},
    ],
    "Control": [
        {"metric": "Ball possession %", "higher_is_better": True},
        {"metric": "Passes", "higher_is_better": True},
        {"metric": "Pass accuracy %", "higher_is_better": True},
        {"metric": "Actions successful %", "higher_is_better": True},
        {"metric": "Lost balls", "higher_is_better": False},
        {"metric": "Bad ball control", "higher_is_better": False},
    ],
    "Progression": [
        {"metric": "Progressive passes", "higher_is_better": True},
        {"metric": "Progressive pass accuracy %", "higher_is_better": True},
        {"metric": "Final third entries", "higher_is_better": True},
        {"metric": "Entries through pass", "higher_is_better": True},
        {"metric": "Entries through carry", "higher_is_better": True},
        {"metric": "Passes into box", "higher_is_better": True},
    ],
    "Pressing / Regain": [
        {"metric": "Team pressing", "higher_is_better": True},
        {"metric": "Pressing success %", "higher_is_better": True},
        {"metric": "Recoveries opp. half", "higher_is_better": True},
        {"metric": "Recoveries after loss 5s", "higher_is_better": True},
        {"metric": "Recoveries after loss 10s", "higher_is_better": True},
    ],
    "Physicality": [
        {"metric": "Challenges", "higher_is_better": True},
        {"metric": "Air challenges", "higher_is_better": True},
        {"metric": "Tackles", "higher_is_better": True},
        {"metric": "Fouls", "higher_is_better": True},
    ],
    "Width / Crossing": [
        {"metric": "Crosses", "higher_is_better": True},
        {"metric": "Cross share", "higher_is_better": True},
        {"metric": "Cross accuracy %", "higher_is_better": True},
        {"metric": "Passes into box", "higher_is_better": True},
    ],
    "Chaos / Risk": [
        {"metric": "Lost balls", "higher_is_better": True},
        {"metric": "Lost balls own half", "higher_is_better": True},
        {"metric": "Individual losses", "higher_is_better": True},
        {"metric": "Bad ball control", "higher_is_better": True},
        {"metric": "Challenges", "higher_is_better": True},
        {"metric": "Fouls", "higher_is_better": True},
    ],
    "Technical Security": [
        {"metric": "Pass accuracy %", "higher_is_better": True},
        {"metric": "Actions successful %", "higher_is_better": True},
        {"metric": "Lost balls", "higher_is_better": False},
        {"metric": "Lost balls own half", "higher_is_better": False},
        {"metric": "Bad ball control", "higher_is_better": False},
    ],
}

EXPECTED_COMPONENTS = [
    {"metric": "xG/team", "higher_is_better": True},
    {"metric": "xA/team", "higher_is_better": True},
    {"metric": "xG+xA/team", "higher_is_better": True},
    {"metric": "Shots", "higher_is_better": True},
    {"metric": "Shots on target", "higher_is_better": True},
    {"metric": "Chances", "higher_is_better": True},
    {"metric": "Actions in box", "higher_is_better": True},
    {"metric": "xG per shot", "higher_is_better": True},
]

EFFECTIVE_COMPONENTS = [
    {"metric": "Goals", "higher_is_better": True},
    {"metric": "Goals total", "higher_is_better": True},
    {"metric": "Goals - xG", "higher_is_better": True},
    {"metric": "Goals - xG total", "higher_is_better": True},
    {"metric": "Goal overperformance %", "higher_is_better": True},
    {"metric": "Goal overperformance total %", "higher_is_better": True},
    {"metric": "Goals per shot", "higher_is_better": True},
    {"metric": "Shots on target %", "higher_is_better": True},
    {"metric": "Chances successful %", "higher_is_better": True},
    {"metric": "Actions in box success %", "higher_is_better": True},
    {"metric": "Actions successful %", "higher_is_better": True},
]

CARD_GROUPS: dict[str, list[str]] = {
    "Style Profile": [
        "Directness",
        "Control",
        "Progression",
        "Pressing / Regain",
        "Physicality",
        "Width / Crossing",
        "Chaos / Risk",
        "Technical Security",
    ],
    "Expected Performance": [
        "xG/team",
        "xA/team",
        "xG+xA/team",
        "Shots",
        "Shots on target",
        "Chances",
        "Actions in box",
        "xG per shot",
    ],
    "Effective Performance": [
        "Goals",
        "Goals total",
        "xG total",
        "Goals - xG",
        "Goals - xG total",
        "Goal overperformance %",
        "Goal overperformance total %",
        "Goals per shot",
        "Shots on target %",
        "Chances successful %",
        "Actions in box success %",
        "Actions successful %",
    ],
    "Build-up / Control": [
        "Ball possession %",
        "Passes",
        "Pass accuracy %",
        "Long pass share",
        "Forward pass share",
        "Progressive passes",
    ],
    "Pressing / Duels": [
        "Team pressing",
        "Pressing success %",
        "Recoveries opp. half",
        "Recoveries after loss 5s",
        "Challenges",
        "Air challenges",
        "Tackles",
    ],
    "Risk / Security": [
        "Lost balls",
        "Lost balls own half",
        "Individual losses",
        "Bad ball control",
    ],
}


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    num = pd.to_numeric(num, errors="coerce")
    den = pd.to_numeric(den, errors="coerce")
    return np.where(den.abs() > 1e-9, num / den, np.nan)


def _percentile(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    values = pd.to_numeric(values, errors="coerce")
    pct = values.rank(pct=True, method="average") * 100
    if not higher_is_better:
        pct = 100 - pct
    return pct.clip(0, 100)


def _metric_series(df: pd.DataFrame, metric_name: str, mode: str) -> pd.Series:
    if metric_name in LEAGUE_METRIC_SPECS:
        return league_metric_series(df, metric_name, mode)
    spec = BASE_METRICS[metric_name]
    raw = pd.to_numeric(df.get(spec["column"], pd.Series(np.nan, index=df.index)), errors="coerce")
    if mode == "Possession-adjusted":
        return apply_possession_adjustment(
            raw,
            df.get("Ball possession, %", pd.Series(np.nan, index=df.index)),
            spec.get("adjustment", "none"),
        )
    return raw


def _format(value: float, fmt: str = "0.00") -> str:
    if pd.isna(value):
        return "—"
    if fmt == "%":
        return f"{float(value) * 100:.1f}%"
    if fmt == "0.0":
        return f"{float(value):.1f}"
    if fmt == "0.00":
        return f"{float(value):.2f}"
    return f"{float(value):.2f}"


def format_metric_value(metric_name: str, value: float) -> str:
    spec = BASE_METRICS.get(metric_name, {"fmt": "0.00"})
    if metric_name in STYLE_INDEX_COMPONENTS or metric_name in {"Expected Performance", "Effective Performance", "Performance Gap"}:
        return "—" if pd.isna(value) else f"{float(value):.0f}"
    return _format(value, spec.get("fmt", "0.00"))


def _coerce_team_numeric(df: pd.DataFrame) -> pd.DataFrame:
    protected = {"Season", "League", "Nation", "Team", "Competition"}
    for col in df.columns:
        if col not in protected:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _compute_total_goal_xg_from_players() -> pd.DataFrame:
    root = Path(__file__).resolve().parents[1]
    players_path = root / "data" / "processed" / "players_enriched.csv.gz"
    if not players_path.exists():
        return pd.DataFrame()

    players = pd.read_csv(players_path, compression="gzip", low_memory=False)
    required = {"Season", "League", "Nation", "Team", "Minutes played"}
    if not required.issubset(players.columns):
        return pd.DataFrame()

    for col in ["Minutes played", "xG (expected goals)", "xA", "Goals", "Shots"]:
        if col in players.columns:
            players[col] = pd.to_numeric(players[col], errors="coerce")

    group_keys = ["Season", "League", "Nation", "Team"]

    def total_from_per90(g: pd.DataFrame, col: str) -> float:
        if col not in g.columns:
            return np.nan
        return (pd.to_numeric(g[col], errors="coerce") * pd.to_numeric(g["Minutes played"], errors="coerce") / 90.0).sum(min_count=1)

    rows = []
    for keys, g in players.groupby(group_keys, dropna=False):
        rec = dict(zip(group_keys, keys))
        rec["Goals total derived"] = total_from_per90(g, "Goals")
        rec["xG total derived"] = total_from_per90(g, "xG (expected goals)")
        rec["xA total derived"] = total_from_per90(g, "xA")
        rec["Shots total derived"] = total_from_per90(g, "Shots")
        rows.append(rec)

    totals = pd.DataFrame(rows)
    if totals.empty:
        return totals

    totals["xG+xA total derived"] = totals["xG total derived"] + totals["xA total derived"]
    totals["Goals - xG total derived"] = totals["Goals total derived"] - totals["xG total derived"]
    totals["Goal overperformance total %"] = np.where(
        totals["xG total derived"].abs() > 1e-9,
        totals["Goals - xG total derived"] / totals["xG total derived"],
        np.nan,
    )
    return totals


def _ensure_total_goal_xg_columns(df: pd.DataFrame) -> pd.DataFrame:
    total_cols = [
        "Goals total derived",
        "xG total derived",
        "xA total derived",
        "Shots total derived",
        "xG+xA total derived",
        "Goals - xG total derived",
        "Goal overperformance total %",
    ]

    needs_totals = any(col not in df.columns for col in total_cols)
    if not needs_totals and "xG total derived" in df.columns:
        needs_totals = pd.to_numeric(df["xG total derived"], errors="coerce").isna().all()

    totals = _compute_total_goal_xg_from_players()
    if totals.empty:
        return df

    # Merge totals even if columns already exist, because older cached/committed
    # team_league_base files may not contain the total columns.
    group_keys = ["Season", "League", "Nation", "Team"]
    existing_cols = [c for c in total_cols if c in df.columns]
    base = df.drop(columns=existing_cols, errors="ignore")
    out = base.merge(totals, on=group_keys, how="left")

    # If a few teams cannot be matched, keep visible NaN instead of failing.
    return out


@st.cache_data(show_spinner="Carico Team Scouting...", ttl=0)
def load_team_scouting_base() -> pd.DataFrame:
    # Direct read avoids stale cache from src.league_style.load_team_league_base().
    root = Path(__file__).resolve().parents[1]
    team_path = root / "data" / "processed" / "team_league_base.csv.gz"
    if not team_path.exists():
        df = load_team_league_base()
    else:
        df = pd.read_csv(team_path, compression="gzip", low_memory=False)

    if "Competition" not in df.columns:
        df["Competition"] = df["League"].astype(str) + " · " + df["Nation"].astype(str)

    df = _coerce_team_numeric(df)
    df = _ensure_total_goal_xg_columns(df)
    df = _coerce_team_numeric(df)
    df = enrich_team_features(df)
    return df


def available_seasons(df: pd.DataFrame) -> list[str]:
    return sorted(df["Season"].dropna().astype(str).unique().tolist(), reverse=True)


def available_competitions(df: pd.DataFrame, season: str) -> list[str]:
    tmp = df[df["Season"].astype(str).eq(str(season))]
    return sorted(tmp["Competition"].dropna().astype(str).unique().tolist())


def build_team_profiles(
    df: pd.DataFrame,
    *,
    season: str,
    competition: str,
    mode: str,
) -> pd.DataFrame:
    data = df[
        df["Season"].astype(str).eq(str(season))
        & df["Competition"].astype(str).eq(str(competition))
    ].copy()

    if data.empty:
        return data

    # Derived effective metrics.
    data["Goals - xG"] = pd.to_numeric(data.get("Goals"), errors="coerce") - pd.to_numeric(data.get("xG/team derived"), errors="coerce")
    data["Goal overperformance %"] = _safe_div(data["Goals - xG"], data.get("xG/team derived"))
    data["Goals - xG total derived"] = pd.to_numeric(data.get("Goals - xG total derived"), errors="coerce")
    data["Goal overperformance total %"] = pd.to_numeric(data.get("Goal overperformance total %"), errors="coerce")
    data["Goals per shot"] = _safe_div(data.get("Goals"), data.get("Shots"))

    # Selected metric values and percentiles inside selected league.
    for metric_name in BASE_METRICS:
        values = _metric_series(data, metric_name, mode)
        data[metric_name] = values
        higher = BASE_METRICS[metric_name].get("higher_is_better", True)
        data[f"{metric_name} percentile"] = _percentile(values, higher)

    def component_score(components: list[dict[str, Any]]) -> pd.Series:
        pcts = []
        for component in components:
            metric = component["metric"]
            if metric not in data.columns:
                continue
            pcts.append(_percentile(data[metric], component.get("higher_is_better", True)))
        if not pcts:
            return pd.Series(np.nan, index=data.index)
        return pd.concat(pcts, axis=1).mean(axis=1, skipna=True)

    for index_name, components in STYLE_INDEX_COMPONENTS.items():
        data[index_name] = component_score(components)
        data[f"{index_name} percentile"] = data[index_name]

    data["Expected Performance"] = component_score(EXPECTED_COMPONENTS)
    data["Effective Performance"] = component_score(EFFECTIVE_COMPONENTS)
    data["Performance Gap"] = data["Effective Performance"] - data["Expected Performance"]
    data["Expected Performance percentile"] = data["Expected Performance"]
    data["Effective Performance percentile"] = data["Effective Performance"]
    data["Performance Gap percentile"] = _percentile(data["Performance Gap"], True)

    data["Flag"] = data["Nation"].map(flag_for_nation)
    return data.sort_values("Team").reset_index(drop=True)


def table_columns() -> list[str]:
    return [
        "Team",
        "Goals",
        "xG/team",
        "Goals - xG",
        "Goals total",
        "xG total",
        "Goals - xG total",
        "Expected Performance",
        "Effective Performance",
        "Performance Gap",
        "Directness",
        "Control",
        "Progression",
        "Pressing / Regain",
        "Physicality",
        "Chaos / Risk",
        "Technical Security",
    ]


def scatter_variable_options() -> list[str]:
    return [
        "Expected Performance",
        "Effective Performance",
        "Performance Gap",
        *STYLE_INDEX_COMPONENTS.keys(),
        *BASE_METRICS.keys(),
    ]
