from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
TEAM_LEAGUE_BASE = PROCESSED_DIR / "team_league_base.csv.gz"

FLAG_MAP = {
    "Argentina": "🇦🇷",
    "Australia": "🇦🇺",
    "Austria": "🇦🇹",
    "Belgium": "🇧🇪",
    "Brasil": "🇧🇷",
    "Brazil": "🇧🇷",
    "Bulgaria": "🇧🇬",
    "Chile": "🇨🇱",
    "China": "🇨🇳",
    "Colombia": "🇨🇴",
    "Croatia": "🇭🇷",
    "Czech Republic": "🇨🇿",
    "Denmark": "🇩🇰",
    "Egypt": "🇪🇬",
    "England": "🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
    "Finland": "🇫🇮",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Greece": "🇬🇷",
    "Iran": "🇮🇷",
    "Israel": "🇮🇱",
    "Italy": "🇮🇹",
    "Japan": "🇯🇵",
    "Mexico": "🇲🇽",
    "Montenegro": "🇲🇪",
    "Morocco": "🇲🇦",
    "Netherlands": "🇳🇱",
    "Portugal": "🇵🇹",
    "Qatar": "🇶🇦",
    "Romania": "🇷🇴",
    "Russia": "🇷🇺",
    "Saudi Arabia": "🇸🇦",
    "Scotland": "🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f",
    "Serbia": "🇷🇸",
    "South Africa": "🇿🇦",
    "South Korea": "🇰🇷",
    "Spain": "🇪🇸",
    "Sweden": "🇸🇪",
    "Switzerland": "🇨🇭",
    "Tunisia": "🇹🇳",
    "Turkey": "🇹🇷",
    "UAE": "🇦🇪",
    "USA": "🇺🇸",
    "Uruguay": "🇺🇾",
}

BIG_FIVE = {
    ("Premier League", "England"),
    ("Serie A", "Italy"),
    ("La Liga", "Spain"),
    ("Bundesliga", "Germany"),
    ("Ligue 1", "France"),
}


def flag_for_nation(nation: str) -> str:
    return FLAG_MAP.get(str(nation), "🏳️")


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    num = pd.to_numeric(num, errors="coerce")
    den = pd.to_numeric(den, errors="coerce")
    return np.where(den.abs() > 1e-9, num / den, np.nan)


@st.cache_data(show_spinner="Carico League Style Lab...")
def load_team_league_base() -> pd.DataFrame:
    if not TEAM_LEAGUE_BASE.exists():
        raise FileNotFoundError(
            "Missing data/processed/team_league_base.csv.gz. "
            "Add the processed Team Dataset file generated for League Style Lab."
        )
    df = pd.read_csv(TEAM_LEAGUE_BASE, compression="gzip", low_memory=False)
    protected = {"Season", "League", "Nation", "Team", "Competition"}
    for col in df.columns:
        if col not in protected:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "Competition" not in df.columns:
        df["Competition"] = df["League"].astype(str) + " · " + df["Nation"].astype(str)
    return df


def available_seasons(df: pd.DataFrame) -> list[str]:
    return sorted(df["Season"].dropna().astype(str).unique().tolist(), reverse=True)


def available_competitions(df: pd.DataFrame, season: str | None = None) -> list[str]:
    tmp = df.copy()
    if season is not None:
        tmp = tmp[tmp["Season"].astype(str).eq(str(season))]
    return sorted(tmp["Competition"].dropna().astype(str).unique().tolist())


def apply_possession_adjustment(raw: pd.Series, possession: pd.Series, adjustment: str, k: float = 8.0, gamma: float = 0.35) -> pd.Series:
    raw = pd.to_numeric(raw, errors="coerce")
    if adjustment == "none":
        return raw
    possession = pd.to_numeric(possession, errors="coerce")
    s = 2 / (1 + np.exp(-k * (possession - 0.50))) - 1
    if adjustment == "on_ball":
        return raw * (1 - gamma * s)
    if adjustment == "off_ball":
        return raw * (1 + gamma * s)
    return raw


def enrich_team_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Ratios/shares describe style better than raw volume for several league traits.
    df["Long pass share"] = _safe_div(df.get("Long passes"), df.get("Passes"))
    df["Super long pass share"] = _safe_div(df.get("Super long passes"), df.get("Passes"))
    df["Forward pass share"] = _safe_div(df.get("Passes forward"), df.get("Passes"))
    df["Progressive pass share"] = _safe_div(df.get("Progressive passes"), df.get("Passes"))
    df["Passes into box share"] = _safe_div(df.get("Passes into the penalty box"), df.get("Passes"))
    df["Cross share"] = _safe_div(df.get("Crosses"), df.get("Passes"))
    df["Goal kick long share"] = _safe_div(df.get("Goal kicks long (40+ m)"), df.get("Goal kicks"))
    df["Goal kick short-medium share"] = _safe_div(
        df.get("Goal kicks short (<15 m)", pd.Series(np.nan, index=df.index)).fillna(0)
        + df.get("Goal kicks medium (15-40 m)", pd.Series(np.nan, index=df.index)).fillna(0),
        df.get("Goal kicks"),
    )
    df["Shots in box proxy"] = df.get("Actions in opponent's box")
    df["xG per shot derived"] = _safe_div(df.get("xG/team derived"), df.get("Shots"))
    df["Threat xG+xA"] = df.get("xG+xA/team derived")
    df["High regain share 5s"] = _safe_div(df.get("Ball recoveries after losses within 5 seconds"), df.get("Ball recoveries"))
    df["High regain share 10s"] = _safe_div(df.get("Ball recoveries after losses within 10 seconds"), df.get("Ball recoveries"))
    df["Technical security inverted losses"] = -pd.to_numeric(df.get("Lost balls"), errors="coerce")
    df["Technical security inverted bad control"] = -pd.to_numeric(df.get("Bad ball control"), errors="coerce")
    df["Technical security inverted own half losses"] = -pd.to_numeric(df.get("Lost balls in own half"), errors="coerce")
    return df


METRIC_SPECS: dict[str, dict[str, Any]] = {
    "Ball possession %": {"column": "Ball possession, %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Passes": {"column": "Passes", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Pass accuracy %": {"column": "Passes accurate, %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Actions successful %": {"column": "Actions successful, %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Long pass share": {"column": "Long pass share", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Super long pass share": {"column": "Super long pass share", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Forward pass share": {"column": "Forward pass share", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Goal kick long share": {"column": "Goal kick long share", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Progressive passes": {"column": "Progressive passes", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Progressive pass share": {"column": "Progressive pass share", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Progressive pass accuracy %": {"column": "Progressive passes accurate, %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Final third entries": {"column": "Final third entries", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Entries through pass": {"column": "Final third entries through pass", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Entries through carry": {"column": "Final third entries through carry", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Passes into box": {"column": "Passes into the penalty box", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Shots": {"column": "Shots", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Shots on target": {"column": "Shots on target", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Shots on target %": {"column": "Shots on target, %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Chances": {"column": "Chances", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Chances successful %": {"column": "Chances successful, %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Actions in box": {"column": "Actions in opponent's box", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "xG/team": {"column": "xG/team derived", "fmt": "0.00", "adjustment": "on_ball", "higher_is_better": True},
    "xA/team": {"column": "xA/team derived", "fmt": "0.00", "adjustment": "on_ball", "higher_is_better": True},
    "xG+xA/team": {"column": "xG+xA/team derived", "fmt": "0.00", "adjustment": "on_ball", "higher_is_better": True},
    "xG per shot": {"column": "xG per shot derived", "fmt": "0.00", "adjustment": "none", "higher_is_better": True},
    "Team pressing": {"column": "Team pressing", "fmt": "0.0", "adjustment": "off_ball", "higher_is_better": True},
    "Pressing success %": {"column": "Team pressing successful, %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Recoveries opp. half": {"column": "Ball recoveries in opponent's half", "fmt": "0.0", "adjustment": "off_ball", "higher_is_better": True},
    "Recoveries after loss 5s": {"column": "Ball recoveries after losses within 5 seconds", "fmt": "0.0", "adjustment": "off_ball", "higher_is_better": True},
    "Recoveries after loss 10s": {"column": "Ball recoveries after losses within 10 seconds", "fmt": "0.0", "adjustment": "off_ball", "higher_is_better": True},
    "Challenges": {"column": "Challenges", "fmt": "0.0", "adjustment": "off_ball", "higher_is_better": True},
    "Air challenges": {"column": "Air challenges", "fmt": "0.0", "adjustment": "off_ball", "higher_is_better": True},
    "Tackles": {"column": "Tackles", "fmt": "0.0", "adjustment": "off_ball", "higher_is_better": True},
    "Fouls": {"column": "Fouls", "fmt": "0.0", "adjustment": "off_ball", "higher_is_better": True},
    "Crosses": {"column": "Crosses", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Cross accuracy %": {"column": "Crosses accurate, %", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Cross share": {"column": "Cross share", "fmt": "%", "adjustment": "none", "higher_is_better": True},
    "Lost balls": {"column": "Lost balls", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Lost balls own half": {"column": "Lost balls in own half", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Individual losses": {"column": "Individual ball losses", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
    "Bad ball control": {"column": "Bad ball control", "fmt": "0.0", "adjustment": "on_ball", "higher_is_better": True},
}


INDEX_DEFINITIONS: dict[str, list[dict[str, Any]]] = {
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
    "Chance Threat": [
        {"metric": "Shots", "higher_is_better": True},
        {"metric": "Shots on target", "higher_is_better": True},
        {"metric": "Chances", "higher_is_better": True},
        {"metric": "Actions in box", "higher_is_better": True},
        {"metric": "xG/team", "higher_is_better": True},
        {"metric": "xG+xA/team", "higher_is_better": True},
    ],
    "Chance Quality": [
        {"metric": "Shots on target %", "higher_is_better": True},
        {"metric": "Chances successful %", "higher_is_better": True},
        {"metric": "xG per shot", "higher_is_better": True},
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


CARD_GROUPS = {
    "Build-up / Control": ["Ball possession %", "Passes", "Pass accuracy %", "Actions successful %"],
    "Directness": ["Long pass share", "Super long pass share", "Forward pass share", "Goal kick long share"],
    "Progression": ["Progressive passes", "Progressive pass accuracy %", "Final third entries", "Entries through pass", "Entries through carry", "Passes into box"],
    "Chance Creation": ["Shots", "Shots on target", "Shots on target %", "Chances", "Actions in box", "xG/team", "xA/team", "xG per shot"],
    "Pressing / Recovery": ["Team pressing", "Pressing success %", "Recoveries opp. half", "Recoveries after loss 5s", "Recoveries after loss 10s"],
    "Physicality / Duels": ["Challenges", "Air challenges", "Tackles", "Fouls"],
    "Width / Crossing": ["Crosses", "Cross share", "Cross accuracy %"],
    "Chaos / Risk": ["Lost balls", "Lost balls own half", "Individual losses", "Bad ball control"],
}


def metric_series(df: pd.DataFrame, metric_name: str, mode: str) -> pd.Series:
    spec = METRIC_SPECS[metric_name]
    col = spec["column"]
    if col not in df.columns:
        return pd.Series(np.nan, index=df.index)
    raw = pd.to_numeric(df[col], errors="coerce")
    if mode == "Possession-adjusted":
        return apply_possession_adjustment(raw, df.get("Ball possession, %", pd.Series(np.nan, index=df.index)), spec.get("adjustment", "none"))
    return raw


def _percentile(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    values = pd.to_numeric(values, errors="coerce")
    pct = values.rank(pct=True, method="average") * 100
    if not higher_is_better:
        pct = 100 - pct
    return pct.clip(0, 100)


def _format_value(value: float, fmt: str) -> str:
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
    return _format_value(value, METRIC_SPECS.get(metric_name, {}).get("fmt", "0.00"))


def aggregate_league_profiles(
    df: pd.DataFrame,
    *,
    season: str,
    mode: str = "Raw",
    aggregation: str = "Median team profile",
    min_teams: int = 6,
) -> pd.DataFrame:
    data = enrich_team_features(df)
    data = data[data["Season"].astype(str).eq(str(season))].copy()
    if data.empty:
        return pd.DataFrame()

    agg_func = "median" if aggregation == "Median team profile" else "mean"
    group_cols = ["Season", "League", "Nation", "Competition"]

    # Add adjusted/selected metric columns at team level.
    for metric_name in METRIC_SPECS:
        data[f"__{metric_name}"] = metric_series(data, metric_name, mode)

    agg_dict = {f"__{m}": agg_func for m in METRIC_SPECS}
    agg_dict.update({"Team": "nunique"})
    if "Players in player dataset" in data.columns:
        agg_dict["Players in player dataset"] = "sum"

    league = data.groupby(group_cols, dropna=False).agg(agg_dict).reset_index()
    league = league.rename(columns={"Team": "Teams", "Players in player dataset": "Players"})

    for metric_name in METRIC_SPECS:
        league[metric_name] = league[f"__{metric_name}"]
        league.drop(columns=[f"__{metric_name}"], inplace=True)

    if "Players" not in league.columns:
        league["Players"] = np.nan

    # Reliability.
    league["Reliability"] = np.select(
        [league["Teams"] >= 14, league["Teams"] >= 8, league["Teams"] >= min_teams],
        ["High", "Moderate", "Low"],
        default="Very low",
    )

    # Metric percentiles among leagues.
    for metric_name, spec in METRIC_SPECS.items():
        league[f"{metric_name} percentile"] = _percentile(league[metric_name], spec.get("higher_is_better", True))

    # Style indices: mean of component percentiles.
    for index_name, components in INDEX_DEFINITIONS.items():
        comp_pcts = []
        for component in components:
            metric_name = component["metric"]
            if metric_name not in league.columns:
                continue
            comp_pcts.append(_percentile(league[metric_name], component.get("higher_is_better", True)))
        if comp_pcts:
            league[index_name] = pd.concat(comp_pcts, axis=1).mean(axis=1, skipna=True)
        else:
            league[index_name] = np.nan

    league["Flag"] = league["Nation"].map(flag_for_nation)
    league = league[league["Teams"] >= min_teams].copy()
    return league.sort_values(["League", "Nation"]).reset_index(drop=True)


def league_display_columns() -> list[str]:
    return [
        "Flag",
        "Competition",
        "Teams",
        "Players",
        "Reliability",
        "Directness",
        "Control",
        "Progression",
        "Chance Threat",
        "Pressing / Regain",
        "Physicality",
        "Chaos / Risk",
        "Technical Security",
    ]


def scatter_variable_options() -> list[str]:
    return list(INDEX_DEFINITIONS.keys()) + list(METRIC_SPECS.keys())
