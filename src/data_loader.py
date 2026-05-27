from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from .preprocessing import merge_players_with_team_context

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
PLAYERS_RAW = RAW_DIR / "Players Dataset.xlsx"
TEAMS_RAW = RAW_DIR / "Team Dataset.xlsx"
GK_RAW = RAW_DIR / "GK Dataset.xlsx"
PLAYERS_PROCESSED = PROCESSED_DIR / "players_enriched.csv.gz"


@st.cache_data(show_spinner="Carico i dati giocatori...")
def load_players_enriched() -> pd.DataFrame:
    """Load processed player data, with a raw Excel fallback.

    The app is designed for repository-based data loading. If the processed
    file exists, it is used. If not, the raw Excel files are read and merged.
    """
    if PLAYERS_PROCESSED.exists():
        df = pd.read_csv(PLAYERS_PROCESSED, compression="gzip", low_memory=False)
    else:
        players = pd.read_excel(PLAYERS_RAW, sheet_name="Main statistics")
        teams = pd.read_excel(TEAMS_RAW, sheet_name="Main statistics")
        df = merge_players_with_team_context(players, teams)

    df = _coerce_numeric(df)
    df = _add_derived_columns(df)
    df = _add_role_bucket(df)
    return df


def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
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
        if col not in protected:
            df[col] = pd.to_numeric(df[col], errors="ignore")
    return df


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Goals" in df and "Assists" in df:
        df["Goals + Assists"] = pd.to_numeric(df["Goals"], errors="coerce") + pd.to_numeric(df["Assists"], errors="coerce")
    if "xG (expected goals)" in df and "xA" in df:
        df["xG + xA"] = pd.to_numeric(df["xG (expected goals)"], errors="coerce") + pd.to_numeric(df["xA"], errors="coerce")
    return df


ROLE_BUCKETS = {
    "CB": ["CB", "LCB", "RCB"],
    "FB": ["LB", "RB", "LWB", "RWB"],
    "MF": ["CDM", "LDM", "RDM", "LCDM", "RCDM", "CM", "LCM", "RCM"],
    "AM/W": ["CAM", "LCAM", "RCAM", "LAM", "RAM", "LM", "RM", "LW", "RW"],
    "FW": ["CF", "LCF", "RCF", "ST", "SS"],
}


def _add_role_bucket(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    reverse = {pos: bucket for bucket, positions in ROLE_BUCKETS.items() for pos in positions}
    df["Role bucket"] = df["Position"].astype(str).map(reverse).fillna("Other")
    return df.loc[df["Position"].astype(str).ne("GK")].reset_index(drop=True)


def available_seasons(df: pd.DataFrame) -> list[str]:
    seasons = sorted(df["Season"].dropna().astype(str).unique().tolist(), reverse=True)
    return seasons


def available_leagues(df: pd.DataFrame) -> list[str]:
    return sorted(df["League"].dropna().astype(str).unique().tolist())
