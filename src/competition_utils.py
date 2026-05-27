from __future__ import annotations

import pandas as pd

BIG_FIVE_COMPETITIONS = {
    ("Serie A", "Italy"),
    ("Premier League", "England"),
    ("La Liga", "Spain"),
    ("Bundesliga", "Germany"),
    ("Ligue 1", "France"),
}

BIG_FIVE_LEAGUE_LABELS = ["Serie A", "Premier League", "La Liga", "Bundesliga", "Ligue 1"]


def is_big_five_mask(df: pd.DataFrame) -> pd.Series:
    if "League" not in df.columns or "Nation" not in df.columns:
        return pd.Series(False, index=df.index)

    league = df["League"].astype(str).str.strip()
    nation = df["Nation"].astype(str).str.strip()

    mask = pd.Series(False, index=df.index)
    for league_name, nation_name in BIG_FIVE_COMPETITIONS:
        mask = mask | (league.eq(league_name) & nation.eq(nation_name))
    return mask


def filter_big_five(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[is_big_five_mask(df)].copy()
