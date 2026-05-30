from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
GK_PROCESSED = PROCESSED_DIR / "gk_enriched.csv.gz"
GK_CLUSTERED = PROCESSED_DIR / "gk_enriched_with_clusters.csv.gz"


@st.cache_data(show_spinner="Carico i dati portieri...")
def load_gk_enriched() -> pd.DataFrame:
    if GK_CLUSTERED.exists():
        df = pd.read_csv(GK_CLUSTERED, compression="gzip", low_memory=False)
    elif not GK_PROCESSED.exists():
        raise FileNotFoundError(
            "Missing data/processed/gk_enriched.csv.gz. "
            "Commit the processed goalkeeper file before deploying the GK module."
        )
    if not GK_CLUSTERED.exists():
        df = pd.read_csv(GK_PROCESSED, compression="gzip", low_memory=False)
    df = _coerce_numeric(df)
    return df[df["team_context_available"].fillna(True).astype(bool)].reset_index(drop=True)


def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    protected = {
        "Season",
        "Player",
        "Team",
        "Nationality",
        "League",
        "Nation",
        "Team_key",
        "Season_key",
        "Season_fallback_key",
        "_team_merge_direct",
        "_team_merge_fallback",
        "GK role",
    }
    for col in df.columns:
        if col in protected:
            continue
        original = df[col]
        converted = pd.to_numeric(original, errors="coerce")
        if converted.notna().sum() > 0 or original.notna().sum() == 0:
            df[col] = converted
    return df


def available_gk_seasons(df: pd.DataFrame) -> list[str]:
    return sorted(df["Season"].dropna().astype(str).unique().tolist(), reverse=True)


def available_gk_leagues(df: pd.DataFrame) -> list[str]:
    return sorted(df["League"].dropna().astype(str).unique().tolist())
