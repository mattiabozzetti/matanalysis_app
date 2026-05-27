"""
Preprocessing and merge rules v1 for the Streamlit football scouting app.

Purpose
-------
This module prepares the outfield Players Dataset and Team Dataset so that
player-level statistics can be enriched with team context, especially team
possession, league and nation.

Rules confirmed during design
-----------------------------
1. The Saudi Al-Arabi SC is disambiguated as: "Al-Arabi SC Saudi".
   - In the Team Dataset, only rows with Nation == "Saudi Arabia" or a Saudi league
     get this suffix.
   - In the Players Dataset, Al-Arabi SC is currently treated as the Saudi team and
     is therefore assigned the same normalized key.
2. Calendar-year competitions are valid when the Team Dataset has a single-year
   season such as "2025". If a player row has a split season like "2025-2026" and
   the direct merge fails, the pipeline tries a fallback season key equal to the
   first year, i.e. "2025".
3. Meizhou Hakka and Changchun Yatai are excluded from the current app/pipeline.
"""

from __future__ import annotations

import re
from typing import Iterable

import numpy as np
import pandas as pd

EXCLUDED_TEAMS = {"Meizhou Hakka", "Changchun Yatai"}
SAUDI_AL_ARABI_KEY = "Al-Arabi SC Saudi"


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Convert common spreadsheet placeholders to missing values."""
    return df.replace({"-": np.nan, "": np.nan, "NA": np.nan, "N/A": np.nan})


def season_first_year(season: object) -> object:
    """Return the first year of a season string when available.

    Examples
    --------
    "2025-2026" -> "2025"
    "2025" -> "2025"
    "2024/25" -> "2024"
    "unknown" -> "unknown"
    """
    if pd.isna(season):
        return np.nan
    text = str(season).strip()
    match = re.match(r"^(\d{4})", text)
    return match.group(1) if match else text


def make_team_key(
    team: object,
    *,
    nation: object | None = None,
    league: object | None = None,
    is_player_table: bool = False,
) -> object:
    """Create a normalized team key for cross-dataset joins."""
    if pd.isna(team):
        return np.nan

    team_text = str(team).strip()

    # User-confirmed rule: player rows for Al-Arabi SC should target the Saudi team.
    if is_player_table and team_text == "Al-Arabi SC":
        return SAUDI_AL_ARABI_KEY

    nation_text = "" if nation is None or pd.isna(nation) else str(nation).strip()
    league_text = "" if league is None or pd.isna(league) else str(league).strip()

    if team_text == "Al-Arabi SC" and (
        nation_text == "Saudi Arabia" or "Saudi" in league_text
    ):
        return SAUDI_AL_ARABI_KEY

    return team_text


def prepare_players(players: pd.DataFrame) -> pd.DataFrame:
    """Clean player rows and add normalized keys."""
    players = clean_missing_values(players).copy()
    players = players.loc[~players["Team"].isin(EXCLUDED_TEAMS)].copy().reset_index(drop=True)
    players["Team_key"] = players["Team"].apply(lambda x: make_team_key(x, is_player_table=True))
    players["Season_key"] = players["Season"].astype(str).str.strip()
    players["Season_fallback_key"] = players["Season"].apply(season_first_year)
    return players


def prepare_teams(teams: pd.DataFrame) -> pd.DataFrame:
    """Clean team rows and add normalized keys."""
    teams = clean_missing_values(teams).copy().reset_index(drop=True)
    teams["Team_key"] = teams.apply(
        lambda r: make_team_key(r["Team"], nation=r.get("Nation"), league=r.get("League")),
        axis=1,
    )
    teams["Season_key"] = teams["Season"].astype(str).str.strip()
    teams["Season_fallback_key"] = teams["Season"].apply(season_first_year)
    return teams


def merge_players_with_team_context(
    players: pd.DataFrame,
    teams: pd.DataFrame,
    *,
    team_context_cols: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Merge players with team context using direct season join plus fallback.

    Direct join:
        players.Season_key + players.Team_key
        = teams.Season_key + teams.Team_key

    Fallback join for unmatched rows:
        players.Season_fallback_key + players.Team_key
        = teams.Season_key + teams.Team_key

    This supports calendar-year leagues where team seasons are stored as "2025".
    """
    players_prepared = prepare_players(players)
    teams_prepared = prepare_teams(teams)

    if team_context_cols is None:
        team_context_cols = ["Season_key", "Team_key", "League", "Nation", "Ball possession, %"]
    else:
        team_context_cols = list(dict.fromkeys(["Season_key", "Team_key", *team_context_cols]))

    team_context = teams_prepared[team_context_cols].drop_duplicates(["Season_key", "Team_key"])

    merged = players_prepared.merge(
        team_context,
        on=["Season_key", "Team_key"],
        how="left",
        suffixes=("", "_team"),
        indicator="_team_merge_direct",
    )

    unmatched_mask = merged["_team_merge_direct"].eq("left_only")
    if unmatched_mask.any():
        fallback_context = team_context.rename(columns={"Season_key": "Season_fallback_key"})
        fallback_cols = [c for c in fallback_context.columns if c not in {"Team_key"}]

        fallback = players_prepared.loc[unmatched_mask, players_prepared.columns].merge(
            fallback_context,
            on=["Season_fallback_key", "Team_key"],
            how="left",
            suffixes=("", "_team"),
            indicator="_team_merge_fallback",
        )

        fill_cols = [c for c in ["League", "Nation", "Ball possession, %"] if c in fallback.columns]
        for col in fill_cols:
            merged.loc[unmatched_mask, col] = fallback[col].to_numpy()
        merged.loc[unmatched_mask, "_team_merge_fallback"] = fallback["_team_merge_fallback"].to_numpy()
    else:
        merged["_team_merge_fallback"] = "not_needed"

    merged["team_context_available"] = merged["Ball possession, %"].notna()
    return merged


def merge_diagnostics(merged: pd.DataFrame) -> dict[str, object]:
    """Return a compact diagnostic summary after team-context merge."""
    missing = merged.loc[~merged["team_context_available"], ["Season", "Team"]].drop_duplicates()
    return {
        "n_rows": int(len(merged)),
        "n_missing_team_context_rows": int((~merged["team_context_available"]).sum()),
        "missing_team_context_pairs": missing.to_dict(orient="records"),
    }
