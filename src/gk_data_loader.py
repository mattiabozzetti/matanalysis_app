from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
GK_PROCESSED = PROCESSED_DIR / "gk_enriched.csv.gz"
GK_CLUSTERED = PROCESSED_DIR / "gk_enriched_with_clusters.csv.gz"
GK_CLUSTER_LABELS = PROCESSED_DIR / "gk_style_cluster_labels.csv"


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
    df = _apply_gk_cluster_labels(df)
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


def _apply_gk_cluster_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Overwrite GK cluster ids with FM-like labels for GK Card."""
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

    if GK_CLUSTER_LABELS.exists():
        labels = pd.read_csv(GK_CLUSTER_LABELS)
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


def available_gk_seasons(df: pd.DataFrame) -> list[str]:
    return sorted(df["Season"].dropna().astype(str).unique().tolist(), reverse=True)


def available_gk_leagues(df: pd.DataFrame) -> list[str]:
    return sorted(df["League"].dropna().astype(str).unique().tolist())
