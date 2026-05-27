from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .metric_catalog import RADAR_AXES
from .scoring import infer_metric_spec, metric_series, percentile_rank


def role_similarity_features(role_bucket: str, profile: str = "Balanced") -> list[dict[str, Any]]:
    """Return concise role-specific similarity features.

    Features are based on the same role radar axes used by the Player Card.
    Unit of every feature is percentile 0-100.
    """
    axes = RADAR_AXES.get(role_bucket, [])
    features: list[dict[str, Any]] = []

    include_style = profile in {"Balanced", "Playing Style"}
    include_performance = profile in {"Balanced", "Performance"}

    for axis in axes:
        axis_name = axis.get("axis", "Axis")
        if include_style and axis.get("style"):
            features.append(
                {
                    "name": f"{axis_name} · Style",
                    "axis": axis_name,
                    "type": "style",
                    "metrics": axis.get("style", []),
                }
            )
        if include_performance and axis.get("performance"):
            features.append(
                {
                    "name": f"{axis_name} · Performance",
                    "axis": axis_name,
                    "type": "performance",
                    "metrics": axis.get("performance", []),
                }
            )

    return features


def _metric_percentile_series(
    df: pd.DataFrame,
    reference_df: pd.DataFrame,
    metric: str | dict[str, Any],
    mode: str,
) -> pd.Series:
    spec = infer_metric_spec(metric) if isinstance(metric, str) else metric
    values = metric_series(df, spec, mode)
    ref_values = metric_series(reference_df, spec, mode)
    higher = spec.get("higher_is_better", True)

    return values.apply(lambda value: percentile_rank(value, ref_values, higher))


def build_feature_matrix(
    df: pd.DataFrame,
    reference_df: pd.DataFrame,
    role_bucket: str,
    profile: str,
    mode: str,
) -> tuple[pd.DataFrame, list[str]]:
    """Build player x similarity-feature matrix in percentile units."""
    features = role_similarity_features(role_bucket, profile)
    matrix = pd.DataFrame(index=df.index)

    for feature in features:
        metric_scores = []
        for metric in feature["metrics"]:
            key = metric if isinstance(metric, str) else metric.get("column") or metric.get("derived")
            if key not in df.columns and key not in reference_df.columns:
                continue
            metric_scores.append(_metric_percentile_series(df, reference_df, metric, mode))

        if metric_scores:
            metric_df = pd.concat(metric_scores, axis=1)
            matrix[feature["name"]] = metric_df.mean(axis=1, skipna=True)

    # Remove features with no signal.
    matrix = matrix.dropna(axis=1, how="all")
    return matrix, matrix.columns.tolist()


def weighted_similarity_scores(
    selected_vector: pd.Series,
    candidate_matrix: pd.DataFrame,
    weights: pd.Series | None = None,
) -> pd.Series:
    """Similarity = 100 - weighted RMSE between percentile vectors."""
    if candidate_matrix.empty:
        return pd.Series(dtype=float)

    common_cols = candidate_matrix.columns.intersection(selected_vector.index)
    if len(common_cols) == 0:
        return pd.Series(np.nan, index=candidate_matrix.index)

    selected = selected_vector[common_cols].astype(float).fillna(50.0)
    candidates = candidate_matrix[common_cols].astype(float).fillna(50.0)

    if weights is None:
        w = pd.Series(1.0, index=common_cols)
    else:
        w = weights.reindex(common_cols).fillna(1.0).astype(float)

    denom = float(w.sum()) if float(w.sum()) > 0 else 1.0
    diff_sq = (candidates.subtract(selected, axis=1) ** 2).multiply(w, axis=1)
    rmse = np.sqrt(diff_sq.sum(axis=1) / denom)
    score = 100 - rmse
    return score.clip(lower=0, upper=100)


def league_profile_and_weights(
    reference_matrix: pd.DataFrame,
    reference_meta: pd.DataFrame,
    target_league: str,
    target_nation: str,
    intensity: float = 0.0,
) -> tuple[pd.Series, pd.Series, int]:
    """Return target league profile and feature weights.

    League profile = mean percentile vector of players in target competition.
    Weights increase for features where the target league differs from the overall
    reference profile. This lets similarity emphasize traits that characterize
    the target league.
    """
    if reference_matrix.empty:
        empty = pd.Series(dtype=float)
        return empty, empty, 0

    target_mask = (
        reference_meta["League"].astype(str).eq(str(target_league))
        & reference_meta["Nation"].astype(str).eq(str(target_nation))
    )

    target_matrix = reference_matrix.loc[target_mask.reindex(reference_matrix.index, fill_value=False)]
    if target_matrix.empty:
        profile = reference_matrix.mean(axis=0, skipna=True)
        weights = pd.Series(1.0, index=reference_matrix.columns)
        return profile, weights, 0

    target_profile = target_matrix.mean(axis=0, skipna=True)
    global_profile = reference_matrix.mean(axis=0, skipna=True)

    distinctiveness = (target_profile - global_profile).abs() / 50.0
    weights = (1.0 + float(intensity) * distinctiveness).clip(lower=0.70, upper=2.50)
    return target_profile, weights, int(len(target_matrix))


def fit_index_scores(
    candidate_matrix: pd.DataFrame,
    league_profile: pd.Series,
    weights: pd.Series | None = None,
) -> pd.Series:
    """Fit index = compatibility with target league characteristic profile."""
    if candidate_matrix.empty or league_profile.empty:
        return pd.Series(np.nan, index=candidate_matrix.index)

    common_cols = candidate_matrix.columns.intersection(league_profile.index)
    if len(common_cols) == 0:
        return pd.Series(np.nan, index=candidate_matrix.index)

    candidates = candidate_matrix[common_cols].astype(float).fillna(50.0)
    profile = league_profile[common_cols].astype(float).fillna(50.0)

    if weights is None:
        w = pd.Series(1.0, index=common_cols)
    else:
        w = weights.reindex(common_cols).fillna(1.0).astype(float)

    denom = float(w.sum()) if float(w.sum()) > 0 else 1.0
    diff_sq = (candidates.subtract(profile, axis=1) ** 2).multiply(w, axis=1)
    rmse = np.sqrt(diff_sq.sum(axis=1) / denom)
    score = 100 - rmse
    return score.clip(lower=0, upper=100)


def competition_label(row_or_series: pd.Series) -> str:
    league = str(row_or_series.get("League", "—"))
    nation = str(row_or_series.get("Nation", "—"))
    return f"{league} · {nation}"


def competition_options(df: pd.DataFrame) -> list[str]:
    if "League" not in df.columns or "Nation" not in df.columns:
        return sorted(df["League"].dropna().astype(str).unique().tolist())
    comps = (
        df[["League", "Nation"]]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .sort_values(["League", "Nation"])
    )
    return [f"{row.League} · {row.Nation}" for row in comps.itertuples(index=False)]


def split_competition_label(label: str) -> tuple[str, str]:
    if " · " in label:
        league, nation = label.split(" · ", 1)
        return league, nation
    return label, ""
