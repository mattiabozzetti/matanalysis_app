from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .gk_metric_catalog import BIG_FIVE_LEAGUES, GK_CARD_GROUPS, GK_GROUP_WEIGHTS
from .competition_utils import filter_big_five


def sigmoid_possession_adjust_series(
    raw: pd.Series,
    possession: pd.Series,
    adjustment: str,
    k: float = 8.0,
    gamma: float = 0.35,
) -> pd.Series:
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


def metric_series(df: pd.DataFrame, metric: dict[str, Any] | str, mode: str = "Raw") -> pd.Series:
    if isinstance(metric, str):
        spec = {"column": metric, "adjustment": "none", "higher_is_better": True}
    else:
        spec = metric

    key = spec.get("derived") or spec.get("column")
    if key not in df.columns:
        return pd.Series(np.nan, index=df.index)

    raw = pd.to_numeric(df[key], errors="coerce")
    if mode == "Possession-adjusted":
        return sigmoid_possession_adjust_series(
            raw,
            df.get("Ball possession, %", pd.Series(np.nan, index=df.index)),
            spec.get("adjustment", "none"),
        )
    return raw


def percentile_rank(value: float, reference_values: pd.Series, higher_is_better: bool = True) -> float:
    values = pd.to_numeric(reference_values, errors="coerce").dropna()
    if pd.isna(value) or len(values) < 3:
        return float("nan")
    pct = float((values <= value).mean() * 100)
    if not higher_is_better:
        pct = 100 - pct
    return max(0.0, min(100.0, pct))


def build_gk_reference_df(
    df: pd.DataFrame,
    *,
    season: str,
    reference_scope: str,
    player_league: str | None,
    custom_leagues: list[str] | None,
    min_minutes: int,
) -> pd.DataFrame:
    ref = df[df["Season"].astype(str).eq(str(season))].copy()
    ref = ref[pd.to_numeric(ref["Minutes played"], errors="coerce").fillna(0) >= min_minutes]

    if reference_scope == "Player league" and player_league:
        ref = ref[ref["League"].astype(str).eq(str(player_league))]
    elif reference_scope == "Big Five":
        ref = filter_big_five(ref)
    elif reference_scope == "Custom leagues" and custom_leagues:
        ref = ref[ref["League"].isin(custom_leagues)]
    elif reference_scope == "All leagues":
        pass
    return ref


def metric_value_and_percentile(
    player_row: pd.Series,
    reference_df: pd.DataFrame,
    metric: dict[str, Any],
    mode: str,
) -> tuple[float, float]:
    player_df = player_row.to_frame().T
    value = metric_series(player_df, metric, mode).iloc[0]
    ref_values = metric_series(reference_df, metric, mode)
    pct = percentile_rank(value, ref_values, metric.get("higher_is_better", True))
    return float(value) if pd.notna(value) else float("nan"), pct


def group_score(player_row: pd.Series, reference_df: pd.DataFrame, group_name: str, mode: str) -> float:
    metrics = GK_CARD_GROUPS[group_name]["metrics"]
    pcts: list[float] = []
    for metric in metrics:
        if metric.get("score_include", True) is False:
            continue
        _, pct = metric_value_and_percentile(player_row, reference_df, metric, mode)
        if not math.isnan(pct):
            pcts.append(pct)
    return float(np.mean(pcts)) if pcts else float("nan")


def all_group_scores(player_row: pd.Series, reference_df: pd.DataFrame, mode: str) -> dict[str, float]:
    return {group: group_score(player_row, reference_df, group, mode) for group in GK_CARD_GROUPS}


def overall(group_scores: dict[str, float]) -> float:
    weighted_sum = 0.0
    weight_total = 0.0
    for group, weight in GK_GROUP_WEIGHTS.items():
        score = group_scores.get(group, float("nan"))
        if not math.isnan(score):
            weighted_sum += score * weight
            weight_total += weight
    return weighted_sum / weight_total if weight_total > 0 else float("nan")


def radar_axis_score(
    player_row: pd.Series,
    reference_df: pd.DataFrame,
    metrics: list[dict[str, Any]],
    mode: str,
) -> float:
    pcts: list[float] = []
    for metric in metrics:
        if metric.get("column") not in reference_df.columns and metric.get("column") not in player_row.index:
            continue
        player_value = metric_series(player_row.to_frame().T, metric, mode).iloc[0]
        ref_values = metric_series(reference_df, metric, mode)
        pct = percentile_rank(player_value, ref_values, metric.get("higher_is_better", True))
        if not math.isnan(pct):
            pcts.append(pct)
    return float(np.mean(pcts)) if pcts else float("nan")


def format_metric_value(value: float, fmt: str) -> str:
    if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if fmt == "%":
        return f"{value * 100:.0f}%"
    if fmt == "0.0":
        return f"{value:.1f}"
    if fmt == "int":
        return f"{value:.0f}"
    return f"{value:.2f}"
