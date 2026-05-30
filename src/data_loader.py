from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from .role_utils import ROLE_BUCKETS, add_role_bucket

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
PLAYERS_RAW = RAW_DIR / "Players Dataset.xlsx"
TEAMS_RAW = RAW_DIR / "Team Dataset.xlsx"
GK_RAW = RAW_DIR / "GK Dataset.xlsx"
PLAYERS_PROCESSED = PROCESSED_DIR / "players_enriched.csv.gz"
PLAYERS_CLUSTERED = PROCESSED_DIR / "players_enriched_with_clusters.csv.gz"
CLUSTER_LABELS = PROCESSED_DIR / "style_cluster_labels.csv"


@st.cache_data(show_spinner="Carico i dati giocatori...")
def load_players_enriched() -> pd.DataFrame:
    """Load player data for the Streamlit app.

    In the deployed app we expect the lightweight processed file to exist.
    If it is missing locally, the function can still rebuild from raw Excel files
    when ``src.preprocessing`` and the raw files are available.
    """
    if PLAYERS_CLUSTERED.exists():
        df = pd.read_csv(PLAYERS_CLUSTERED, compression="gzip", low_memory=False)
    elif PLAYERS_PROCESSED.exists():
        df = pd.read_csv(PLAYERS_PROCESSED, compression="gzip", low_memory=False)
    else:
        try:
            from .preprocessing import merge_players_with_team_context
        except ModuleNotFoundError as exc:
            raise FileNotFoundError(
                "Missing data/processed/players_enriched.csv.gz. "
                "For deployment, commit the processed file. To rebuild locally, "
                "restore src/preprocessing.py and the raw Excel files in data/raw/."
            ) from exc

        if not PLAYERS_RAW.exists() or not TEAMS_RAW.exists():
            raise FileNotFoundError(
                "Missing processed data and raw Excel fallback files. Expected either "
                "data/processed/players_enriched.csv.gz or both raw Excel files in data/raw/."
            )
        players = pd.read_excel(PLAYERS_RAW, sheet_name="Main statistics")
        teams = pd.read_excel(TEAMS_RAW, sheet_name="Main statistics")
        df = merge_players_with_team_context(players, teams)

    df = _coerce_numeric(df)
    df = _add_derived_columns(df)
    df = _add_role_bucket(df)
    df = _apply_cluster_labels(df)
    return df


def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Safely infer numeric columns without pandas' deprecated errors='ignore'."""
    df = df.copy()
    protected = {
        "Season",
        "Player",
        "Team",
        "Position",
        "Nationality",
        "League",
        "Nation",
        "Team_key",
        "Season_key",
        "Season_fallback_key",
        "_team_merge_direct",
        "_team_merge_fallback",
    }

    for col in df.columns:
        if col in protected:
            continue

        original = df[col]
        converted = pd.to_numeric(original, errors="coerce")

        non_missing_original = original.notna().sum()
        non_missing_converted = converted.notna().sum()

        # Convert if at least one value is numeric, or if the column was empty anyway.
        if non_missing_converted > 0 or non_missing_original == 0:
            df[col] = converted

    return df


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Goals" in df and "Assists" in df:
        df["Goals + Assists"] = pd.to_numeric(df["Goals"], errors="coerce") + pd.to_numeric(df["Assists"], errors="coerce")
    if "xG (expected goals)" in df and "xA" in df:
        df["xG + xA"] = pd.to_numeric(df["xG (expected goals)"], errors="coerce") + pd.to_numeric(df["xA"], errors="coerce")
    return df


def _add_role_bucket(df: pd.DataFrame) -> pd.DataFrame:
    df = add_role_bucket(df)
    return df.loc[df["Position"].astype(str).ne("GK")].reset_index(drop=True)


def _apply_cluster_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Overwrite cluster ids with FM-like labels.

    Older builds may contain style_cluster_name_label columns due to a merge
    suffix. The card reads style_cluster_name/style_cluster_short_label, so we
    normalise the columns here at load time.
    """
    if "style_cluster_id" not in df.columns:
        return df

    out = df.copy()

    for base_col in ["style_cluster_name", "style_cluster_short_label", "style_cluster_description"]:
        label_col = f"{base_col}_label"
        if label_col in out.columns:
            if base_col not in out.columns:
                out[base_col] = out[label_col]
            else:
                out[base_col] = out[base_col].where(out[base_col].notna(), out[label_col])

    if CLUSTER_LABELS.exists():
        labels = pd.read_csv(CLUSTER_LABELS)
        keep = [c for c in ["style_cluster_id", "style_cluster_name", "style_cluster_short_label", "description"] if c in labels.columns]
        labels = labels[keep].drop_duplicates("style_cluster_id")
        if "description" in labels.columns:
            labels = labels.rename(columns={"description": "style_cluster_description"})

        out = out.drop(
            columns=["style_cluster_name", "style_cluster_short_label", "style_cluster_description"],
            errors="ignore",
        )
        out = out.merge(labels, on="style_cluster_id", how="left")

    out = out.drop(
        columns=["style_cluster_name_label", "style_cluster_short_label_label", "style_cluster_description_label"],
        errors="ignore",
    )

    return out


def available_seasons(df: pd.DataFrame) -> list[str]:
    return sorted(df["Season"].dropna().astype(str).unique().tolist(), reverse=True)


def available_leagues(df: pd.DataFrame) -> list[str]:
    return sorted(df["League"].dropna().astype(str).unique().tolist())
