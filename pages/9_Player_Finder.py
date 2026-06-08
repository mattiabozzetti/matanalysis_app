from __future__ import annotations

import html
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from src.competition_utils import filter_big_five
from src.data_loader import available_seasons, load_players_enriched
from src.metric_catalog import ROLE_BUCKETS
from src.ui import inject_css, pct_color

st.set_page_config(page_title="Player Finder", page_icon="🔎", layout="wide")
inject_css()

st.markdown(
    """
<style>
.finder-hero {
    border:1px solid rgba(95,255,224,0.20);
    background: radial-gradient(circle at top left, rgba(95,255,224,0.13), transparent 34%),
                linear-gradient(115deg, rgba(16,22,43,0.92), rgba(33,21,60,0.72));
    border-radius:26px;
    padding:30px 32px;
    margin:0.8rem 0 1.5rem 0;
    box-shadow:0 18px 62px rgba(0,0,0,0.30), inset 0 0 26px rgba(95,255,224,0.04);
}
.finder-kicker {color:#5FFFE0;font-size:0.82rem;font-weight:950;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:10px;}
.finder-title {color:#F8FBFF;font-size:3rem;line-height:1;font-weight:950;letter-spacing:-0.04em;text-shadow:0 0 18px rgba(95,255,224,0.18);margin-bottom:12px;}
.finder-subtitle {color:#B7CAE8;font-size:1.02rem;line-height:1.55;max-width:1120px;font-weight:650;}
.finder-pill-row {display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.finder-pill {
    display:inline-flex;align-items:center;min-height:28px;padding:0 11px;border-radius:999px;
    border:1px solid rgba(95,255,224,0.24);background:rgba(95,255,224,0.08);
    color:#DDE8FF;font-size:0.76rem;font-weight:850;
}
.finder-section-title {color:#F6F7FB;font-size:1.55rem;font-weight:950;letter-spacing:-0.03em;margin:1.4rem 0 0.85rem 0;}
.finder-target-card {
    border:1px solid rgba(95,255,224,0.18);
    background:rgba(16,22,43,0.78);
    border-radius:22px;
    padding:18px 20px;
    margin-bottom:14px;
    box-shadow:0 14px 44px rgba(0,0,0,0.22);
}
.finder-target-name {color:#5FFFE0;font-size:1.18rem;font-weight:950;letter-spacing:-0.02em;}
.finder-target-meta {color:#AFC3E8;font-size:0.86rem;font-weight:700;margin-top:5px;line-height:1.45;}
.finder-family-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:0.8rem 0 1.2rem 0;}
.finder-family-card {
    border:1px solid rgba(95,255,224,0.16);
    background:rgba(16,22,43,0.72);
    border-radius:18px;
    padding:14px 15px;
    min-height:118px;
}
.finder-family-title {color:#5FFFE0;font-size:0.9rem;font-weight:950;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:7px;}
.finder-family-meta {color:#B7CAE8;font-size:0.78rem;font-weight:750;line-height:1.38;}
.finder-card {
    border:1px solid rgba(95,255,224,0.15);
    background:rgba(16,22,43,0.80);
    border-radius:22px;
    padding:16px 18px;
    margin-bottom:12px;
    box-shadow:0 14px 44px rgba(0,0,0,0.20);
}
.finder-card-top {display:grid;grid-template-columns:46px minmax(0,1fr) 95px 100px;gap:14px;align-items:center;}
.finder-rank {color:#B7CAE8;font-weight:950;text-align:center;font-size:1.1rem;}
.finder-name {color:#F6F7FB;font-size:1.15rem;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.finder-meta {color:#8EA2C6;font-size:0.82rem;font-weight:750;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.finder-score-pill {
    display:inline-flex;align-items:center;justify-content:center;min-width:76px;height:34px;border-radius:999px;
    border:1px solid rgba(95,255,224,0.35);background:rgba(95,255,224,0.10);
    color:#5FFFE0;font-weight:950;font-size:0.90rem;
}
.finder-detail-grid {display:grid;grid-template-columns:repeat(3, minmax(0,1fr));gap:7px;margin-top:12px;}
.finder-chip {
    display:flex;align-items:center;justify-content:space-between;gap:8px;
    background:rgba(10,16,36,0.58);border:1px solid rgba(255,255,255,0.06);
    border-radius:12px;padding:7px 9px;color:#B7CAE8;font-size:0.76rem;font-weight:750;
}
.finder-chip strong {color:#F6F7FB;font-weight:950;}
.finder-chip-pass {border-color:rgba(95,255,224,0.22);background:rgba(95,255,224,0.06);}
.finder-chip-fail {border-color:rgba(255,79,109,0.22);background:rgba(255,79,109,0.055);}
.finder-warning {
    display:inline-flex;align-items:center;padding:5px 9px;border-radius:999px;
    border:1px solid rgba(255,230,109,0.28);background:rgba(255,230,109,0.08);
    color:#FFE66D;font-size:0.72rem;font-weight:900;margin-right:6px;margin-top:8px;
}
.finder-table-wrap {
    width:100%;overflow-x:auto;border:1px solid rgba(95,255,224,0.18);border-radius:18px;
    background:rgba(10,16,36,0.78);box-shadow:0 14px 44px rgba(0,0,0,0.22);margin:0.8rem 0 1.2rem 0;
}
.finder-table {width:100%;border-collapse:collapse;color:#F6F7FB;font-size:0.84rem;min-width:980px;}
.finder-table th {
    background:#10162B;color:#AFC3E8;text-align:left;padding:11px 10px;
    font-size:0.72rem;font-weight:950;letter-spacing:0.06em;text-transform:uppercase;
    border-bottom:1px solid rgba(95,255,224,0.18);
}
.finder-table td {padding:9px 10px;border-bottom:1px solid rgba(255,255,255,0.055);background:rgba(16,22,43,0.72);}
.finder-table tr:nth-child(even) td {background:rgba(12,18,38,0.78);}
.finder-table .num {text-align:right;font-variant-numeric:tabular-nums;font-weight:850;}
@media (max-width:1200px) {
    .finder-family-grid {grid-template-columns:1fr;}
    .finder-card-top {grid-template-columns:34px minmax(0,1fr) 82px 82px;}
    .finder-detail-grid {grid-template-columns:1fr;}
}
</style>
""",
    unsafe_allow_html=True,
)

NEGATIVE_METRICS = {
    "Lost balls",
    "Lost balls in own half",
    "Lost balls after passes",
    "Individual ball losses",
    "Bad ball control",
    "Actions unsuccessful",
    "Challenges unsuccessful",
    "Dribbles unsuccessful",
    "Mistakes leading to goals",
    "Mistakes leading to chances",
    "xGPG (xG per goal)",
}


FAMILY_LIBRARY: dict[str, dict[str, list[dict[str, Any]]]] = {
    "CB": {
        "Defensive activity": [
            {"metric": "Defensive challenges", "direction": "min", "q": 0.55},
            {"metric": "Tackles", "direction": "min", "q": 0.50},
            {"metric": "Interceptions", "direction": "min", "q": 0.55},
            {"metric": "Ball recoveries", "direction": "min", "q": 0.50},
            {"metric": "Air challenges", "direction": "min", "q": 0.50},
        ],
        "Build-up": [
            {"metric": "Passes", "direction": "min", "q": 0.50},
            {"metric": "Progressive passes", "direction": "min", "q": 0.55},
            {"metric": "Passes forward to the final third", "direction": "min", "q": 0.55},
            {"metric": "Long passes", "direction": "min", "q": 0.50},
            {"metric": "Passes accurate, %", "direction": "min", "q": 0.40},
        ],
        "Security": [
            {"metric": "Lost balls", "direction": "max", "q": 0.75},
            {"metric": "Bad ball control", "direction": "max", "q": 0.75},
            {"metric": "Mistakes leading to chances", "direction": "max", "q": 0.80},
        ],
    },
    "FB": {
        "Wide progression": [
            {"metric": "Final third entries", "direction": "min", "q": 0.55},
            {"metric": "Final third entries through carry", "direction": "min", "q": 0.55},
            {"metric": "Progressive passes", "direction": "min", "q": 0.50},
            {"metric": "Carry", "direction": "min", "q": 0.50},
        ],
        "Wide creation": [
            {"metric": "Crosses", "direction": "min", "q": 0.50},
            {"metric": "Passes into the penalty box", "direction": "min", "q": 0.50},
            {"metric": "Key passes", "direction": "min", "q": 0.45},
        ],
        "Defensive work": [
            {"metric": "Defensive challenges", "direction": "min", "q": 0.50},
            {"metric": "Tackles", "direction": "min", "q": 0.50},
            {"metric": "Ball recoveries", "direction": "min", "q": 0.50},
        ],
        "Ball security": [
            {"metric": "Lost balls", "direction": "max", "q": 0.75},
            {"metric": "Bad ball control", "direction": "max", "q": 0.75},
        ],
    },
    "MF": {
        "Control": [
            {"metric": "Passes", "direction": "min", "q": 0.55},
            {"metric": "Short passes", "direction": "min", "q": 0.50},
            {"metric": "Open passes received in the central third", "direction": "min", "q": 0.50},
            {"metric": "Passes accurate, %", "direction": "min", "q": 0.35},
        ],
        "Progression": [
            {"metric": "Progressive passes", "direction": "min", "q": 0.55},
            {"metric": "Passes forward to the final third", "direction": "min", "q": 0.55},
            {"metric": "Final third entries", "direction": "min", "q": 0.50},
            {"metric": "Carry", "direction": "min", "q": 0.45},
        ],
        "Defensive range": [
            {"metric": "Ball recoveries", "direction": "min", "q": 0.50},
            {"metric": "Interceptions", "direction": "min", "q": 0.50},
            {"metric": "Defensive challenges", "direction": "min", "q": 0.50},
        ],
        "Creation": [
            {"metric": "Key passes", "direction": "min", "q": 0.45},
            {"metric": "Passes for a shot", "direction": "min", "q": 0.45},
            {"metric": "Chances created", "direction": "min", "q": 0.45},
            {"metric": "xA", "direction": "min", "q": 0.45},
        ],
        "Security": [
            {"metric": "Lost balls", "direction": "max", "q": 0.75},
            {"metric": "Bad ball control", "direction": "max", "q": 0.75},
        ],
    },
    "AM": {
        "Chance creation": [
            {"metric": "xA", "direction": "min", "q": 0.55},
            {"metric": "Key passes", "direction": "min", "q": 0.55},
            {"metric": "Passes for a shot", "direction": "min", "q": 0.55},
            {"metric": "Chances created", "direction": "min", "q": 0.55},
        ],
        "Between lines": [
            {"metric": "Open passes received in the final third", "direction": "min", "q": 0.55},
            {"metric": "Progressive passes", "direction": "min", "q": 0.45},
            {"metric": "Passes", "direction": "min", "q": 0.40},
        ],
        "Box threat": [
            {"metric": "Actions in opponent's box", "direction": "min", "q": 0.55},
            {"metric": "Open passes received in the opponent's box", "direction": "min", "q": 0.50},
            {"metric": "Shots", "direction": "min", "q": 0.50},
            {"metric": "xG (expected goals)", "direction": "min", "q": 0.45},
        ],
        "Dribbling progression": [
            {"metric": "Dribbles", "direction": "min", "q": 0.50},
            {"metric": "Dribbling in the final third", "direction": "min", "q": 0.50},
            {"metric": "Carry", "direction": "min", "q": 0.45},
        ],
        "Security": [
            {"metric": "Lost balls", "direction": "max", "q": 0.75},
            {"metric": "Bad ball control", "direction": "max", "q": 0.75},
        ],
    },
    "W": {
        "1v1 threat": [
            {"metric": "Dribbles", "direction": "min", "q": 0.55},
            {"metric": "Dribbling in the final third", "direction": "min", "q": 0.55},
            {"metric": "Dribbles successful, %", "direction": "min", "q": 0.35},
        ],
        "Box runs": [
            {"metric": "Actions in opponent's box", "direction": "min", "q": 0.55},
            {"metric": "Open passes received in the opponent's box", "direction": "min", "q": 0.50},
            {"metric": "Shots", "direction": "min", "q": 0.50},
            {"metric": "xG (expected goals)", "direction": "min", "q": 0.45},
        ],
        "Wide creation": [
            {"metric": "Crosses", "direction": "min", "q": 0.50},
            {"metric": "Passes into the penalty box", "direction": "min", "q": 0.50},
            {"metric": "Key passes", "direction": "min", "q": 0.50},
            {"metric": "Passes for a shot", "direction": "min", "q": 0.50},
        ],
        "Transition/carry": [
            {"metric": "Final third entries through carry", "direction": "min", "q": 0.55},
            {"metric": "Carry", "direction": "min", "q": 0.50},
            {"metric": "Progressive open passes", "direction": "min", "q": 0.45},
        ],
        "Security": [
            {"metric": "Lost balls", "direction": "max", "q": 0.75},
            {"metric": "Bad ball control", "direction": "max", "q": 0.75},
        ],
    },
    "FW": {
        "Area occupation": [
            {"metric": "Actions in opponent's box", "direction": "min", "q": 0.60},
            {"metric": "Open passes received in the opponent's box", "direction": "min", "q": 0.55},
            {"metric": "Shots from the penalty area", "direction": "min", "q": 0.60},
            {"metric": "xG (expected goals)", "direction": "min", "q": 0.60},
            {"metric": "xGPS (xG per shot)", "direction": "min", "q": 0.55},
        ],
        "Box threat": [
            {"metric": "Shots", "direction": "min", "q": 0.55},
            {"metric": "Shots on target", "direction": "min", "q": 0.55},
            {"metric": "Shots on target, %", "direction": "min", "q": 0.45},
            {"metric": "Goals", "direction": "min", "q": 0.55},
            {"metric": "xGC (xG conversion)", "direction": "min", "q": 0.45},
        ],
        "Contact & aerial": [
            {"metric": "Challenges", "direction": "min", "q": 0.50},
            {"metric": "Attacking challenges", "direction": "min", "q": 0.50},
            {"metric": "Attacking challenges won, %", "direction": "min", "q": 0.35},
            {"metric": "Air challenges", "direction": "min", "q": 0.50},
            {"metric": "Air challenges won, %", "direction": "min", "q": 0.35},
        ],
        "Transition threat": [
            {"metric": "Long open passes received", "direction": "min", "q": 0.50},
            {"metric": "Super long open passes received", "direction": "min", "q": 0.45},
            {"metric": "Carry", "direction": "min", "q": 0.45},
            {"metric": "Final third entries", "direction": "min", "q": 0.45},
            {"metric": "Final third entries through carry", "direction": "min", "q": 0.45},
        ],
        "Link-up survival": [
            {"metric": "Passes", "direction": "min", "q": 0.35},
            {"metric": "Passes accurate, %", "direction": "min", "q": 0.25},
            {"metric": "Short passes accurate, %", "direction": "min", "q": 0.25},
            {"metric": "Progressive passes accurate, %", "direction": "min", "q": 0.25},
            {"metric": "Passes for a shot", "direction": "min", "q": 0.35},
            {"metric": "xA", "direction": "min", "q": 0.30},
        ],
        "Ball security": [
            {"metric": "Lost balls", "direction": "max", "q": 0.75},
            {"metric": "Bad ball control", "direction": "max", "q": 0.75},
            {"metric": "Lost balls in own half", "direction": "max", "q": 0.70},
        ],
    },
}

JUVE9_WEIGHTS = {
    "Area occupation": 25,
    "Box threat": 20,
    "Contact & aerial": 20,
    "Transition threat": 15,
    "Link-up survival": 15,
    "Ball security": 5,
}

ROLE_DEFAULT_WEIGHTS = {
    "CB": {"Defensive activity": 35, "Build-up": 30, "Security": 20},
    "FB": {"Wide progression": 25, "Wide creation": 20, "Defensive work": 25, "Ball security": 10},
    "MF": {"Control": 25, "Progression": 25, "Defensive range": 20, "Creation": 15, "Security": 10},
    "AM": {"Chance creation": 30, "Between lines": 20, "Box threat": 20, "Dribbling progression": 15, "Security": 10},
    "W": {"1v1 threat": 25, "Box runs": 20, "Wide creation": 20, "Transition/carry": 20, "Security": 10},
    "FW": JUVE9_WEIGHTS,
}


def txt(value: Any, fallback: str = "—") -> str:
    if pd.isna(value):
        return fallback
    value = str(value)
    if value in {"", "nan", "None"}:
        return fallback
    return value


def fmt_num(value: Any, decimals: int = 2) -> str:
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return str(value)


def fmt_int(value: Any) -> str:
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):,.0f}".replace(",", ".")
    except Exception:
        return str(value)


def all_competitions(data: pd.DataFrame) -> list[str]:
    if data.empty or "League" not in data.columns:
        return []
    if "Nation" in data.columns:
        labels = (
            data[["League", "Nation"]]
            .dropna()
            .drop_duplicates()
            .assign(label=lambda x: x["League"].astype(str) + " · " + x["Nation"].astype(str))
            ["label"]
            .sort_values()
            .tolist()
        )
        return labels
    return sorted(data["League"].dropna().astype(str).unique().tolist())


def comp_filter(data: pd.DataFrame, label: str) -> pd.Series:
    if "League" not in data.columns:
        return pd.Series(False, index=data.index)
    if " · " in label and "Nation" in data.columns:
        league, nation = label.split(" · ", 1)
        return data["League"].astype(str).eq(league) & data["Nation"].astype(str).eq(nation)
    return data["League"].astype(str).eq(label)


def numeric_metric_options(data: pd.DataFrame) -> list[str]:
    protected = {
        "Season", "Player", "Team", "Nationality", "Position", "Role bucket",
        "style_cluster_id", "style_cluster_role", "style_cluster_name",
        "style_cluster_short_label", "style_cluster_description", "League", "Nation",
        "Team_key", "Season_key", "Season_fallback_key", "_team_merge_direct",
        "_team_merge_fallback", "team_context_available",
    }
    options = []
    for col in data.columns:
        if col in protected:
            continue
        values = pd.to_numeric(data[col], errors="coerce")
        if values.notna().sum() >= 20:
            options.append(col)
    return sorted(options)


def available_metric_specs(role: str, selected_families: list[str], custom_metrics: list[str]) -> list[dict[str, Any]]:
    specs = []
    for family in selected_families:
        for spec in FAMILY_LIBRARY.get(role, {}).get(family, []):
            row = spec.copy()
            row["family"] = family
            specs.append(row)
    for metric in custom_metrics:
        specs.append(
            {
                "metric": metric,
                "direction": "max" if metric in NEGATIVE_METRICS else "min",
                "q": 0.75 if metric in NEGATIVE_METRICS else 0.50,
                "family": "Custom metrics",
            }
        )

    # Deduplicate by metric, keep first family assignment.
    seen = set()
    out = []
    for spec in specs:
        if spec["metric"] in seen:
            continue
        seen.add(spec["metric"])
        out.append(spec)
    return out


def usable_specs(data: pd.DataFrame, specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for spec in specs:
        metric = spec["metric"]
        if metric in data.columns and pd.to_numeric(data[metric], errors="coerce").notna().sum() > 0:
            out.append(spec)
    return out


def empirical_percentile(values: pd.Series, x: pd.Series, inverse: bool = False) -> pd.Series:
    ref = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if len(ref) == 0:
        return pd.Series(np.nan, index=x.index)
    ref.sort()
    xv = pd.to_numeric(x, errors="coerce")
    ranks = np.searchsorted(ref, xv.to_numpy(dtype=float), side="right") / len(ref) * 100
    ranks = pd.Series(ranks, index=x.index)
    ranks[xv.isna()] = np.nan
    if inverse:
        ranks = 100 - ranks
    return ranks.clip(0, 100)


def threshold_from_reference(reference: pd.DataFrame, metric: str, direction: str, q: float) -> float:
    values = pd.to_numeric(reference[metric], errors="coerce").dropna()
    if values.empty:
        return 0.0
    return float(values.quantile(q))


def pass_criterion(value: Any, threshold: float, direction: str) -> bool:
    if pd.isna(value):
        return False
    try:
        value = float(value)
    except Exception:
        return False
    return value <= threshold if direction == "max" else value >= threshold


def style_label(row: pd.Series) -> str:
    return txt(row.get("style_cluster_short_label"), txt(row.get("style_cluster_name"), txt(row.get("style_cluster_id"), "Unclustered")))


def player_label(row: pd.Series) -> str:
    return f"{txt(row.get('Player'))} · {txt(row.get('Team'))} · {txt(row.get('Position'))} · {style_label(row)}"


def build_family_scores(
    candidates: pd.DataFrame,
    reference: pd.DataFrame,
    role: str,
    selected_families: list[str],
    custom_metrics: list[str],
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    scores = pd.DataFrame(index=candidates.index)
    family_metric_map: dict[str, list[str]] = {}

    for family in selected_families:
        fam_specs = usable_specs(reference, FAMILY_LIBRARY.get(role, {}).get(family, []))
        metric_score_cols = []
        for spec in fam_specs:
            metric = spec["metric"]
            inverse = spec["direction"] == "max" or metric in NEGATIVE_METRICS
            col = f"pct__{family}__{metric}"
            scores[col] = empirical_percentile(reference[metric], candidates[metric], inverse=inverse)
            metric_score_cols.append(col)
        if metric_score_cols:
            scores[family] = scores[metric_score_cols].mean(axis=1, skipna=True)
            family_metric_map[family] = [spec["metric"] for spec in fam_specs]

    if custom_metrics:
        metric_score_cols = []
        for metric in custom_metrics:
            if metric not in reference.columns:
                continue
            inverse = metric in NEGATIVE_METRICS
            col = f"pct__Custom metrics__{metric}"
            scores[col] = empirical_percentile(reference[metric], candidates[metric], inverse=inverse)
            metric_score_cols.append(col)
        if metric_score_cols:
            scores["Custom metrics"] = scores[metric_score_cols].mean(axis=1, skipna=True)
            family_metric_map["Custom metrics"] = custom_metrics

    return scores, family_metric_map


def compute_anchor_similarity(candidates: pd.DataFrame, reference: pd.DataFrame, anchor: pd.Series, metrics: list[str]) -> pd.Series:
    metrics = [m for m in metrics if m in candidates.columns and m in reference.columns and pd.notna(anchor.get(m, np.nan))]
    if len(metrics) < 2:
        return pd.Series(np.nan, index=candidates.index)

    ref = reference[metrics].apply(pd.to_numeric, errors="coerce")
    median = ref.median()
    iqr = (ref.quantile(0.75) - ref.quantile(0.25)).replace(0, np.nan)
    iqr = iqr.fillna(ref.std(ddof=0)).replace(0, np.nan).fillna(1.0)

    cand_z = (candidates[metrics].apply(pd.to_numeric, errors="coerce") - median) / iqr
    anchor_z = (pd.to_numeric(anchor[metrics], errors="coerce") - median) / iqr
    dist = np.sqrt(((cand_z - anchor_z) ** 2).mean(axis=1, skipna=True))
    sim = 100 * np.exp(-dist / 2.0)
    return pd.Series(sim, index=candidates.index).clip(0, 100)


def warnings_for_row(row: pd.Series, role: str) -> list[str]:
    warnings = []
    get = lambda c: float(row.get(c, np.nan)) if not pd.isna(row.get(c, np.nan)) else np.nan

    if role == "FW":
        area = get("Area occupation")
        contact = get("Contact & aerial")
        link = get("Link-up survival")
        transition = get("Transition threat")
        threat = get("Box threat")
        security = get("Ball security")

        if area >= 65 and contact >= 55 and link >= 35:
            warnings.append("Good fit: area + contact + enough link-up")
        if contact < 40 and link >= 60:
            warnings.append("Too clean / low contact")
        if area >= 65 and link < 30:
            warnings.append("Box presence but poor link-up")
        if transition >= 70 and area < 50:
            warnings.append("Transition striker, not box striker")
        if contact >= 70 and area >= 55 and link < 50:
            warnings.append("Mateta-like terminal")
        if link >= 70 and contact < 45:
            warnings.append("David-like support profile")
        if area >= 70 and contact >= 55 and threat >= 60:
            warnings.append("Vlahović-like box/duel profile")
        if security < 35:
            warnings.append("Ball-security risk")
    else:
        if row.get("Fit Score", 0) >= 75:
            warnings.append("Strong profile match")
        if row.get("Anchor Similarity", np.nan) >= 75:
            warnings.append("Very close to anchor")
        if row.get("criteria_matched", 0) < row.get("criteria_total", 1):
            warnings.append("Near match, check missing criteria")

    return warnings[:3]


def render_family_cards(weights: dict[str, float], family_metric_map: dict[str, list[str]]) -> None:
    parts = ['<div class="finder-family-grid">']
    for family, weight in weights.items():
        metrics = family_metric_map.get(family, [])
        if not metrics:
            continue
        parts.append(
            f"""
<div class="finder-family-card">
  <div class="finder-family-title">{html.escape(family)} · {float(weight):.0f}%</div>
  <div class="finder-family-meta">{html.escape(", ".join(metrics[:8]))}</div>
</div>
"""
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def render_table(df: pd.DataFrame) -> str:
    parts = ['<div class="finder-table-wrap"><table class="finder-table">']
    parts.append("<thead><tr>")
    for col in df.columns:
        parts.append(f"<th>{html.escape(str(col))}</th>")
    parts.append("</tr></thead><tbody>")
    for _, row in df.iterrows():
        parts.append("<tr>")
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                out = "—"
            elif isinstance(value, (float, np.floating)):
                out = f"{float(value):.1f}" if "Score" in col or "Similarity" in col or "matched" not in col else f"{float(value):.0f}"
            else:
                out = str(value)
            cls = "num" if isinstance(value, (int, float, np.integer, np.floating)) and not pd.isna(value) else ""
            parts.append(f'<td class="{cls}">{html.escape(out)}</td>')
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def render_cards(df: pd.DataFrame, title: str, metric_specs: list[dict[str, Any]], limit: int = 12) -> None:
    st.markdown(f'<div class="finder-section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("Nessun giocatore in questa sezione.")
        return

    for rank, (_, row) in enumerate(df.head(limit).iterrows(), start=1):
        score = float(row.get("Fit Score", np.nan))
        sim = row.get("Anchor Similarity", np.nan)
        color = pct_color(score) if not pd.isna(score) else "#8EA2C6"
        meta = (
            f"{fmt_int(row.get('Age'))} yrs · {txt(row.get('Position'))} · "
            f"{txt(row.get('Team'))} · {txt(row.get('League'))} · {style_label(row)}"
        )

        chips = []
        for spec in metric_specs[:9]:
            metric = spec["metric"]
            value = row.get(metric, np.nan)
            threshold = spec.get("threshold", np.nan)
            direction = spec.get("direction", "min")
            passed = pass_criterion(value, threshold, direction)
            sign = "≤" if direction == "max" else "≥"
            chips.append(
                f'<div class="finder-chip {"finder-chip-pass" if passed else "finder-chip-fail"}">'
                f'<span>{html.escape(metric)}</span>'
                f'<strong>{fmt_num(value)} {sign} {fmt_num(threshold)}</strong>'
                f'</div>'
            )

        warning_html = "".join([f'<span class="finder-warning">{html.escape(w)}</span>' for w in warnings_for_row(row, txt(row.get("Role bucket"), ""))])
        sim_text = fmt_num(sim, 0) if not pd.isna(sim) else "—"

        st.markdown(
            f"""
<div class="finder-card">
  <div class="finder-card-top">
    <div class="finder-rank">{rank}</div>
    <div>
      <div class="finder-name">{html.escape(txt(row.get("Player")))}</div>
      <div class="finder-meta">{html.escape(meta)}</div>
      <div>{warning_html}</div>
    </div>
    <div><span class="finder-score-pill" style="color:{color};border-color:{color}80;">{fmt_num(score, 0)}</span></div>
    <div><span class="finder-score-pill">SIM {sim_text}</span></div>
  </div>
  <div class="finder-detail-grid">
    {''.join(chips)}
  </div>
</div>
""",
            unsafe_allow_html=True,
        )


df = load_players_enriched()

st.markdown(
    """
<div class="finder-hero">
  <div class="finder-kicker">Profile-based scouting</div>
  <div class="finder-title">Player Finder</div>
  <div class="finder-subtitle">
    Costruisci un profilo bersaglio: scegli ruolo, campionati, cluster, giocatore-ancora,
    famiglie di metriche e filtri raw. L’obiettivo è trovare compatibilità funzionale, non “il migliore” in assoluto.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Search context")
    seasons = available_seasons(df)
    season = st.selectbox("Season", seasons, index=0)
    season_df = df[df["Season"].astype(str).eq(str(season))].copy()

    role_options = [r for r in ["CB", "FB", "MF", "AM", "W", "FW"] if r in ROLE_BUCKETS]
    role = st.selectbox("Target role", role_options, index=role_options.index("FW") if "FW" in role_options else 0)
    role_df = season_df[season_df["Role bucket"].astype(str).eq(role)].copy()

    scope = st.selectbox("Candidate scope", ["All leagues", "Big Five", "Single competition", "Custom competitions"], index=1 if role == "FW" else 0)
    comps = all_competitions(role_df)
    selected_comp = None
    custom_comps: list[str] = []
    if scope == "Single competition" and comps:
        selected_comp = st.selectbox("Competition", comps)
    elif scope == "Custom competitions" and comps:
        custom_comps = st.multiselect("Custom competitions", comps, default=[])

    min_minutes = st.number_input("Minimum minutes", min_value=0, max_value=4000, value=900, step=100)
    age_min, age_max = st.columns(2)
    with age_min:
        min_age = st.number_input("Min age", min_value=14, max_value=45, value=16, step=1, key="finder_min_age")
    with age_max:
        max_age = st.number_input("Max age", min_value=14, max_value=45, value=30, step=1, key="finder_max_age")

    st.markdown("---")
    st.markdown("### Start from player")
    anchor_enabled = st.checkbox("Use selected player as anchor", value=False)
    anchor_row = None
    anchor_label = "No anchor"
    anchor_candidates = role_df.copy()
    if not anchor_candidates.empty:
        anchor_candidates = anchor_candidates.sort_values(["Player", "Team"])
        labels = ["No anchor"] + [player_label(row) for _, row in anchor_candidates.iterrows()]
        anchor_choice = st.selectbox("Anchor player", labels, index=0, disabled=not anchor_enabled)
        if anchor_enabled and anchor_choice != "No anchor":
            anchor_pos = labels.index(anchor_choice) - 1
            anchor_row = anchor_candidates.iloc[anchor_pos]
            anchor_label = anchor_choice

    st.markdown("---")
    st.markdown("### Cluster filter")
    clusters = (
        role_df[["style_cluster_id", "style_cluster_name"]]
        .dropna()
        .drop_duplicates()
        .sort_values(["style_cluster_id"])
    )
    cluster_mode_options = ["All clusters", "Choose clusters"]
    if anchor_row is not None and pd.notna(anchor_row.get("style_cluster_id", np.nan)):
        cluster_mode_options.insert(1, "Same as anchor")
    cluster_mode = st.selectbox("Cluster mode", cluster_mode_options, index=0)
    chosen_clusters: list[str] = []
    if cluster_mode == "Same as anchor" and anchor_row is not None:
        chosen_clusters = [str(anchor_row.get("style_cluster_id"))]
    elif cluster_mode == "Choose clusters":
        cluster_labels = [f"{r.style_cluster_name} · {r.style_cluster_id}" for _, r in clusters.iterrows()]
        selected_cluster_labels = st.multiselect("Clusters", cluster_labels, default=[])
        chosen_clusters = [x.rsplit(" · ", 1)[-1] for x in selected_cluster_labels]

    st.markdown("---")
    st.markdown("### Metric families")
    template = st.selectbox(
        "Template",
        ["Juve 9 Fit" if role == "FW" else "Role-based broad fit", "Role-based broad fit", "Pure custom"],
        index=0,
    )
    families_available = list(FAMILY_LIBRARY.get(role, {}).keys())
    default_families = families_available if template != "Pure custom" else []
    selected_families = st.multiselect("Families", families_available, default=default_families)

    numeric_options = numeric_metric_options(role_df)
    custom_metrics = st.multiselect("Add custom metrics", numeric_options, default=[])

    reference_scope = st.selectbox("Percentile reference", ["Current filtered scope", "Role + season", "Big Five role + season"], index=0)
    score_blend = st.slider("Anchor similarity weight", min_value=0, max_value=60, value=25 if anchor_row is not None else 0, step=5, disabled=anchor_row is None)

# Candidate pool base filters.
candidate_pool = role_df.copy()
candidate_pool = candidate_pool[pd.to_numeric(candidate_pool["Minutes played"], errors="coerce").fillna(0) >= int(min_minutes)]
candidate_pool = candidate_pool[pd.to_numeric(candidate_pool["Age"], errors="coerce").between(min_age, max_age, inclusive="both")]

if scope == "Big Five":
    candidate_pool = filter_big_five(candidate_pool)
elif scope == "Single competition" and selected_comp:
    candidate_pool = candidate_pool[comp_filter(candidate_pool, selected_comp)]
elif scope == "Custom competitions" and custom_comps:
    mask = pd.Series(False, index=candidate_pool.index)
    for comp in custom_comps:
        mask = mask | comp_filter(candidate_pool, comp)
    candidate_pool = candidate_pool[mask]

if chosen_clusters:
    candidate_pool = candidate_pool[candidate_pool["style_cluster_id"].astype(str).isin(chosen_clusters)]

if anchor_row is not None:
    candidate_pool = candidate_pool[~(
        candidate_pool["Player"].astype(str).eq(str(anchor_row.get("Player")))
        & candidate_pool["Team"].astype(str).eq(str(anchor_row.get("Team")))
        & candidate_pool["Season"].astype(str).eq(str(anchor_row.get("Season")))
    )]

# Reference group for percentiles and thresholds.
if reference_scope == "Role + season":
    reference_df = role_df[pd.to_numeric(role_df["Minutes played"], errors="coerce").fillna(0) >= int(min_minutes)].copy()
elif reference_scope == "Big Five role + season":
    reference_df = filter_big_five(role_df)
    reference_df = reference_df[pd.to_numeric(reference_df["Minutes played"], errors="coerce").fillna(0) >= int(min_minutes)].copy()
else:
    reference_df = candidate_pool.copy()

if reference_df.empty:
    reference_df = role_df.copy()

metric_specs = usable_specs(reference_df, available_metric_specs(role, selected_families, custom_metrics))
if not metric_specs:
    st.warning("Seleziona almeno una famiglia o una metrica custom disponibile.")
    st.stop()

st.markdown(
    f"""
<div class="finder-target-card">
  <div class="finder-target-name">{html.escape(template)}</div>
  <div class="finder-target-meta">
    Role {html.escape(role)} · season {html.escape(str(season))} · candidate pool n={len(candidate_pool)} · reference n={len(reference_df)}
    <br>Anchor: {html.escape(anchor_label)}
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Editable family weights.
st.markdown('<div class="finder-section-title">Family weights</div>', unsafe_allow_html=True)
family_score_cols: list[str] = []
base_weights = JUVE9_WEIGHTS if (template == "Juve 9 Fit" and role == "FW") else ROLE_DEFAULT_WEIGHTS.get(role, {})
weight_values: dict[str, float] = {}

weight_columns = st.columns(3)
active_families = selected_families.copy()
if custom_metrics:
    active_families.append("Custom metrics")

for i, family in enumerate(active_families):
    default_weight = float(base_weights.get(family, 10 if family == "Custom metrics" else 15))
    with weight_columns[i % 3]:
        weight_values[family] = st.number_input(
            f"{family} weight",
            min_value=0.0,
            max_value=100.0,
            value=default_weight,
            step=5.0,
            key=f"finder_weight_{role}_{family}",
        )

total_weight = sum(weight_values.values())
if total_weight <= 0:
    st.warning("Inserisci almeno un peso maggiore di zero.")
    st.stop()
norm_weights = {k: v / total_weight * 100 for k, v in weight_values.items() if v > 0}

family_scores, family_metric_map = build_family_scores(candidate_pool, reference_df, role, selected_families, custom_metrics)
render_family_cards(norm_weights, family_metric_map)

# Editable hard filters.
st.markdown('<div class="finder-section-title">Must-have raw filters</div>', unsafe_allow_html=True)
st.caption("Scegli le metriche che devono funzionare come soglie minime/massime. Le soglie sono raw e calcolate dalla reference, ma modificabili.")

filter_mode = st.radio("Default hard filters", ["Core family metrics", "All selected metrics", "Manual only"], horizontal=True, index=0)
core_limit = 2
default_active = set()
if filter_mode == "Core family metrics":
    for family in selected_families:
        specs_for_family = [s for s in metric_specs if s.get("family") == family]
        default_active.update([s["metric"] for s in specs_for_family[:core_limit]])
elif filter_mode == "All selected metrics":
    default_active.update([s["metric"] for s in metric_specs])

active_filter_specs = []
with st.expander("Edit metric thresholds", expanded=True):
    for spec in metric_specs:
        metric = spec["metric"]
        direction = spec.get("direction", "min")
        q = float(spec.get("q", 0.5))
        raw_threshold = threshold_from_reference(reference_df, metric, direction, q)
        key_base = f"{role}_{metric}".replace(" ", "_").replace("%", "pct").replace("'", "").replace("/", "_").replace(",", "")
        c1, c2, c3, c4 = st.columns([1.4, 0.46, 0.72, 0.42])
        with c1:
            st.markdown(f"**{metric}**  \n<small>{html.escape(spec.get('family', 'Custom'))}</small>", unsafe_allow_html=True)
        with c2:
            rule = st.selectbox(
                "rule",
                ["min", "max"],
                index=1 if direction == "max" else 0,
                format_func=lambda x: "≤" if x == "max" else "≥",
                key=f"rule_{key_base}",
                label_visibility="collapsed",
            )
        with c3:
            threshold = st.number_input(
                "threshold",
                value=float(round(raw_threshold, 2)),
                step=0.05 if abs(raw_threshold) < 5 else 0.10,
                key=f"threshold_{key_base}",
                label_visibility="collapsed",
            )
        with c4:
            active = st.checkbox(
                "active",
                value=metric in default_active,
                key=f"active_{key_base}",
                label_visibility="collapsed",
            )
        if active:
            out_spec = spec.copy()
            out_spec["direction"] = rule
            out_spec["threshold"] = float(threshold)
            active_filter_specs.append(out_spec)

if candidate_pool.empty:
    st.warning("Nessun candidato nel pool dopo i filtri di contesto.")
    st.stop()

scored = candidate_pool.copy()

# Add family score columns.
for family in active_families:
    if family in family_scores.columns:
        scored[family] = family_scores[family]
    else:
        scored[family] = np.nan

# Fit score.
fit = pd.Series(0.0, index=scored.index)
used_weight = 0.0
for family, weight in norm_weights.items():
    if family in scored.columns:
        fit = fit + scored[family].fillna(0) * (weight / 100)
        used_weight += weight
scored["Family Fit"] = fit / max(used_weight / 100, 1e-9)

all_metric_names_for_anchor = sorted(set([s["metric"] for s in metric_specs]))
if anchor_row is not None:
    scored["Anchor Similarity"] = compute_anchor_similarity(scored, reference_df, anchor_row, all_metric_names_for_anchor)
else:
    scored["Anchor Similarity"] = np.nan

blend = float(score_blend) / 100.0 if anchor_row is not None else 0.0
if anchor_row is not None:
    scored["Fit Score"] = (1 - blend) * scored["Family Fit"].fillna(0) + blend * scored["Anchor Similarity"].fillna(scored["Family Fit"])
else:
    scored["Fit Score"] = scored["Family Fit"]

# Hard filter match counts.
for spec in active_filter_specs:
    metric = spec["metric"]
    scored[f"pass__{metric}"] = scored[metric].apply(lambda value, s=spec: pass_criterion(value, s["threshold"], s["direction"]))

pass_cols = [f"pass__{s['metric']}" for s in active_filter_specs]
if pass_cols:
    scored["criteria_matched"] = scored[pass_cols].sum(axis=1)
    scored["criteria_total"] = len(pass_cols)
else:
    scored["criteria_matched"] = 0
    scored["criteria_total"] = 0

sort_options = ["Fit Score", "Anchor Similarity", "Family Fit", "Criteria matched", *active_families]
sort_by = st.selectbox("Sort candidates by", sort_options, index=0)
if sort_by == "Criteria matched":
    scored = scored.sort_values(["criteria_matched", "Fit Score", "Minutes played"], ascending=[False, False, False])
else:
    scored = scored.sort_values([sort_by, "criteria_matched", "Minutes played"], ascending=[False, False, False])

if pass_cols:
    strict = scored[scored["criteria_matched"].eq(scored["criteria_total"])].copy()
    near = scored[
        (scored["criteria_matched"] >= max(1, scored["criteria_total"].iloc[0] - 1))
        & ~scored.index.isin(strict.index)
    ].copy()
else:
    strict = scored.head(25).copy()
    near = scored.iloc[25:60].copy()

wildcards = scored[
    (pd.to_numeric(scored["Age"], errors="coerce") <= 23)
    & ~scored.index.isin(strict.index)
    & ~scored.index.isin(near.index)
].copy()

summary_cols = st.columns(5)
summary_cols[0].metric("Candidate pool", len(candidate_pool))
summary_cols[1].metric("Strict matches", len(strict))
summary_cols[2].metric("Near matches", len(near))
summary_cols[3].metric("Wildcards U23", len(wildcards))
summary_cols[4].metric("Metrics active", len(active_filter_specs))

render_cards(strict, "Strict matches", active_filter_specs, limit=14)
render_cards(near, "Near matches", active_filter_specs, limit=10)
render_cards(wildcards, "Wildcard profiles", active_filter_specs, limit=8)

with st.expander("Full candidate table", expanded=False):
    show_cols = [
        c for c in [
            "Player", "Age", "Position", "Team", "League", "Nation",
            "style_cluster_name", "Minutes played", "Fit Score", "Family Fit",
            "Anchor Similarity", "criteria_matched", "criteria_total",
            *active_families,
            *[s["metric"] for s in active_filter_specs],
        ]
        if c in scored.columns
    ]
    table = scored.head(200)[show_cols].copy()
    st.markdown(render_table(table), unsafe_allow_html=True)

    csv = table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download shortlist CSV",
        data=csv,
        file_name=f"player_finder_{role}_{season}.csv",
        mime="text/csv",
    )
