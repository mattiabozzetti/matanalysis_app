from __future__ import annotations

import pandas as pd

ROLE_BUCKETS: dict[str, list[str]] = {
    "CB": ["CB", "LCB", "RCB"],
    "FB": ["LB", "RB", "LWB", "RWB"],
    "MF": ["CDM", "LDM", "RDM", "LCDM", "RCDM", "CM", "LCM", "RCM"],
    "AM": ["CAM", "LCAM", "RCAM"],
    "W": ["LAM", "RAM", "LM", "RM", "LW", "RW"],
    "FW": ["CF", "LCF", "RCF", "ST", "SS"],
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
