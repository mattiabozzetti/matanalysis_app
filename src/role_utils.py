from __future__ import annotations

import pandas as pd

# Tactical role taxonomy for scouting.
# LDM/RDM are treated as FB because, in this source, they often encode wide
# defensive midfielders / wing-backs / quinti rather than central midfielders.
ROLE_BUCKETS: dict[str, list[str]] = {
    "CB": ["CB", "LCB", "RCB"],
    "FB": ["LB", "RB", "LWB", "RWB", "LDM", "RDM"],
    "MF": ["CDM", "LCDM", "RCDM", "CM", "LCM", "RCM"],
    "AM": ["CAM", "LCAM", "RCAM"],
    "W": ["LAM", "RAM", "LM", "RM", "LW", "RW"],
    "FW": ["CF", "LCF", "RCF", "ST", "SS"],
}

ROLE_LABELS: dict[str, str] = {
    "CB": "CENTRE BACK",
    "FB": "FULL BACK",
    "MF": "MIDFIELDER",
    "AM": "ATTACKING MID",
    "W": "WINGER",
    "FW": "FORWARD",
}

POSITION_TO_BUCKET: dict[str, str] = {
    position: bucket
    for bucket, positions in ROLE_BUCKETS.items()
    for position in positions
}


def role_bucket_for_position(position: object) -> str:
    if pd.isna(position):
        return "Other"
    return POSITION_TO_BUCKET.get(str(position).strip(), "Other")


def add_role_bucket(df: pd.DataFrame, position_col: str = "Position") -> pd.DataFrame:
    out = df.copy()
    if position_col not in out.columns:
        out["Role bucket"] = "Other"
        return out
    out["Role bucket"] = out[position_col].apply(role_bucket_for_position)
    return out


def role_label(role_bucket: object) -> str:
    if pd.isna(role_bucket):
        return "UNKNOWN"
    return ROLE_LABELS.get(str(role_bucket), str(role_bucket).upper())
