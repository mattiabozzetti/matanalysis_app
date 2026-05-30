from __future__ import annotations

from pathlib import Path
import gzip
import shutil
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.preprocessing import merge_diagnostics, merge_players_with_team_context  # noqa: E402
from src.role_utils import add_role_bucket  # noqa: E402

RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

players = pd.read_excel(RAW / "Players Dataset.xlsx", sheet_name="Main statistics")
teams = pd.read_excel(RAW / "Team Dataset.xlsx", sheet_name="Main statistics")
merged = merge_players_with_team_context(players, teams)

# Derived columns used by the card catalog.
merged["Goals + Assists"] = pd.to_numeric(merged["Goals"], errors="coerce") + pd.to_numeric(merged["Assists"], errors="coerce")
merged["xG + xA"] = pd.to_numeric(merged["xG (expected goals)"], errors="coerce") + pd.to_numeric(merged["xA"], errors="coerce")

# Exclude GK in the first processed file for outfield card and assign the app role taxonomy.
merged = add_role_bucket(merged)
merged = merged[merged["Position"].astype(str).ne("GK")].reset_index(drop=True)

tmp_csv = OUT / "players_enriched.csv"
output_path = OUT / "players_enriched.csv.gz"
merged.to_csv(tmp_csv, index=False)
with tmp_csv.open("rb") as f_in, gzip.open(output_path, "wb") as f_out:
    shutil.copyfileobj(f_in, f_out)
tmp_csv.unlink(missing_ok=True)

print(f"Saved: {output_path}")
print(merge_diagnostics(merged))
