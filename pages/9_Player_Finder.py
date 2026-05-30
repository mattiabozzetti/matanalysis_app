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
.finder-subtitle {color:#B7CAE8;font-size:1.02rem;line-height:1.55;max-width:1100px;font-weight:650;}
.finder-pill-row {display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.finder-pill {
    display:inline-flex;align-items:center;min-height:28px;padding:0 11px;border-radius:999px;
    border:1px solid rgba(95,255,224,0.24);background:rgba(95,255,224,0.08);
    color:#DDE8FF;font-size:0.76rem;font-weight:850;
}
.finder-section-title {color:#F6F7FB;font-size:1.55rem;font-weight:950;letter-spacing:-0.03em;margin:1.4rem 0 0.85rem 0;}
.finder-preset-card {
    border:1px solid rgba(95,255,224,0.18);
    background:rgba(16,22,43,0.78);
    border-radius:22px;
    padding:18px 20px;
    margin-bottom:14px;
    box-shadow:0 14px 44px rgba(0,0,0,0.22);
}
.finder-preset-name {color:#5FFFE0;font-size:1.20rem;font-weight:950;letter-spacing:-0.02em;}
.finder-preset-meta {color:#AFC3E8;font-size:0.86rem;font-weight:700;margin-top:4px;}
.finder-criteria-grid {display:grid;grid-template-columns:1.35fr 0.60fr 0.55fr 0.55fr;gap:10px;align-items:center;}
.finder-criteria-head {
    color:#AFC3E8;font-size:0.72rem;font-weight:950;letter-spacing:0.08em;text-transform:uppercase;
    border-bottom:1px solid rgba(95,255,224,0.16);padding:8px 0;
}
.finder-criteria-row {display:contents;}
.finder-criteria-row > div {
    border-bottom:1px solid rgba(255,255,255,0.06);
    padding:9px 0;
    color:#DDE8FF;
    font-size:0.84rem;
    font-weight:800;
}
.finder-card {
    border:1px solid rgba(95,255,224,0.15);
    background:rgba(16,22,43,0.80);
    border-radius:22px;
    padding:16px 18px;
    margin-bottom:12px;
    box-shadow:0 14px 44px rgba(0,0,0,0.20);
}
.finder-card-top {display:grid;grid-template-columns:46px minmax(0,1fr) 110px;gap:14px;align-items:center;}
.finder-rank {color:#B7CAE8;font-weight:950;text-align:center;font-size:1.1rem;}
.finder-name {color:#F6F7FB;font-size:1.15rem;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.finder-meta {color:#8EA2C6;font-size:0.82rem;font-weight:750;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.finder-match-pill {
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
.finder-small-table-wrap {
    width:100%;overflow-x:auto;border:1px solid rgba(95,255,224,0.18);border-radius:18px;
    background:rgba(10,16,36,0.78);box-shadow:0 14px 44px rgba(0,0,0,0.22);margin:0.8rem 0 1.2rem 0;
}
.finder-small-table {width:100%;border-collapse:collapse;color:#F6F7FB;font-size:0.84rem;}
.finder-small-table th {
    background:#10162B;color:#AFC3E8;text-align:left;padding:11px 10px;
    font-size:0.72rem;font-weight:950;letter-spacing:0.06em;text-transform:uppercase;
    border-bottom:1px solid rgba(95,255,224,0.18);
}
.finder-small-table td {padding:9px 10px;border-bottom:1px solid rgba(255,255,255,0.055);background:rgba(16,22,43,0.72);}
.finder-small-table tr:nth-child(even) td {background:rgba(12,18,38,0.78);}
.finder-small-table .num {text-align:right;font-variant-numeric:tabular-nums;font-weight:850;}
@media (max-width:1100px) {
    .finder-card-top {grid-template-columns:34px minmax(0,1fr) 86px;}
    .finder-detail-grid {grid-template-columns:1fr;}
}
</style>
""",
    unsafe_allow_html=True,
)

CRITERIA_BY_ROLE: dict[str, list[dict[str, Any]]] = {
    "CB": [
        {"metric": "Defensive challenges", "direction": "min", "q": 0.55},
        {"metric": "Interceptions", "direction": "min", "q": 0.55},
        {"metric": "Air challenges", "direction": "min", "q": 0.50},
        {"metric": "Progressive passes", "direction": "min", "q": 0.50},
        {"metric": "Passes", "direction": "min", "q": 0.45},
        {"metric": "Lost balls", "direction": "max", "q": 0.75},
    ],
    "FB": [
        {"metric": "Progressive passes", "direction": "min", "q": 0.55},
        {"metric": "Final third entries", "direction": "min", "q": 0.55},
        {"metric": "Crosses", "direction": "min", "q": 0.50},
        {"metric": "Dribbles", "direction": "min", "q": 0.50},
        {"metric": "Defensive challenges", "direction": "min", "q": 0.50},
        {"metric": "Lost balls", "direction": "max", "q": 0.75},
    ],
    "MF": [
        {"metric": "Passes", "direction": "min", "q": 0.55},
        {"metric": "Progressive passes", "direction": "min", "q": 0.55},
        {"metric": "Passes forward to the final third", "direction": "min", "q": 0.55},
        {"metric": "Ball recoveries", "direction": "min", "q": 0.50, "fallback": "Loose ball recoveries"},
        {"metric": "Key passes", "direction": "min", "q": 0.45},
        {"metric": "Lost balls", "direction": "max", "q": 0.75},
    ],
    "AM": [
        {"metric": "xA", "direction": "min", "q": 0.55},
        {"metric": "Key passes", "direction": "min", "q": 0.55},
        {"metric": "Passes for a shot", "direction": "min", "q": 0.55},
        {"metric": "Open passes received in the final third", "direction": "min", "q": 0.55},
        {"metric": "Actions in opponent's box", "direction": "min", "q": 0.50},
        {"metric": "Lost balls", "direction": "max", "q": 0.75},
    ],
    "W": [
        {"metric": "Dribbles", "direction": "min", "q": 0.55},
        {"metric": "Dribbling in the final third", "direction": "min", "q": 0.55},
        {"metric": "Crosses", "direction": "min", "q": 0.50},
        {"metric": "Actions in opponent's box", "direction": "min", "q": 0.55},
        {"metric": "Shots", "direction": "min", "q": 0.50},
        {"metric": "Lost balls", "direction": "max", "q": 0.75},
    ],
    "FW": [
        {"metric": "xG (expected goals)", "direction": "min", "q": 0.55},
        {"metric": "Shots", "direction": "min", "q": 0.55},
        {"metric": "Shots from the penalty area", "direction": "min", "q": 0.55},
        {"metric": "Actions in opponent's box", "direction": "min", "q": 0.55},
        {"metric": "Open passes received in the opponent's box", "direction": "min", "q": 0.50},
        {"metric": "Lost balls", "direction": "max", "q": 0.75},
    ],
}


def txt(value, fallback="—") -> str:
    if pd.isna(value):
        return fallback
    return str(value)


def fmt_num(value, decimals=2) -> str:
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return str(value)


def fmt_int(value) -> str:
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):,.0f}".replace(",", ".")
    except Exception:
        return str(value)


def competition_label(row: pd.Series) -> str:
    league = txt(row.get("League"), "")
    nation = txt(row.get("Nation"), "")
    return f"{league} · {nation}" if nation and nation != "—" else league


def all_competitions(data: pd.DataFrame) -> list[str]:
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
    else:
        labels = sorted(data["League"].dropna().astype(str).unique().tolist())
    return labels


def comp_filter(data: pd.DataFrame, label: str) -> pd.Series:
    if " · " in label and "Nation" in data.columns:
        league, nation = label.split(" · ", 1)
        return data["League"].astype(str).eq(league) & data["Nation"].astype(str).eq(nation)
    return data["League"].astype(str).eq(label)


def effective_metric_name(data: pd.DataFrame, criterion: dict[str, Any]) -> str | None:
    metric = criterion["metric"]
    fallback = criterion.get("fallback")
    if metric in data.columns:
        return metric
    if fallback and fallback in data.columns:
        return fallback
    return None


def build_default_threshold(data: pd.DataFrame, metric: str, direction: str, q: float) -> float:
    values = pd.to_numeric(data[metric], errors="coerce").dropna()
    if values.empty:
        return 0.0
    if direction == "max":
        return float(values.quantile(q))
    return float(values.quantile(q))


def pass_criterion(value: Any, threshold: float, direction: str) -> bool:
    if pd.isna(value):
        return False
    try:
        value = float(value)
    except Exception:
        return False
    if direction == "max":
        return value <= threshold
    return value >= threshold


def style_label(row: pd.Series) -> str:
    return txt(
        row.get("style_cluster_short_label"),
        txt(row.get("style_cluster_name"), txt(row.get("style_cluster_id"), "Unclustered")),
    )


def render_small_table(df: pd.DataFrame) -> str:
    parts = ['<div class="finder-small-table-wrap"><table class="finder-small-table">']
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
                out = f"{float(value):.2f}"
            else:
                out = str(value)
            cls = "num" if isinstance(value, (int, float, np.integer, np.floating)) and not pd.isna(value) else ""
            parts.append(f'<td class="{cls}">{html.escape(out)}</td>')
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def render_cards(df: pd.DataFrame, criteria: list[dict[str, Any]], title: str, limit: int = 12) -> None:
    st.markdown(f'<div class="finder-section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("Nessun giocatore in questa sezione.")
        return

    for rank, (_, row) in enumerate(df.head(limit).iterrows(), start=1):
        matched = int(row.get("criteria_matched", 0))
        total = int(row.get("criteria_total", 0))
        color = pct_color((matched / max(total, 1)) * 100)
        meta = (
            f"{fmt_int(row.get('Age'))} yrs · {txt(row.get('Position'))} · "
            f"{txt(row.get('Team'))} · {txt(row.get('League'))} · {style_label(row)}"
        )
        chips = []
        for criterion in criteria[:8]:
            metric = criterion["metric"]
            value = row.get(metric, np.nan)
            threshold = criterion["threshold"]
            direction = criterion["direction"]
            passed = pass_criterion(value, threshold, direction)
            sign = "≥" if direction == "min" else "≤"
            chips.append(
                f'<div class="finder-chip {"finder-chip-pass" if passed else "finder-chip-fail"}">'
                f'<span>{html.escape(metric)}</span>'
                f'<strong>{fmt_num(value)} {sign} {fmt_num(threshold)}</strong>'
                f'</div>'
            )

        st.markdown(
            f"""
<div class="finder-card">
  <div class="finder-card-top">
    <div class="finder-rank">{rank}</div>
    <div>
      <div class="finder-name">{html.escape(txt(row.get("Player")))}</div>
      <div class="finder-meta">{html.escape(meta)}</div>
    </div>
    <div><span class="finder-match-pill" style="color:{color};border-color:{color}80;">{matched}/{total}</span></div>
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
  <div class="finder-kicker">Qualitative scouting filter</div>
  <div class="finder-title">Player Finder</div>
  <div class="finder-subtitle">
    Costruisci shortlist con filtri qualitativi su metriche raw, ruolo e archetipi di stile.
    Non è un modello decisionale: serve a ridurre il database e trovare profili da guardare meglio.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Finder filters")
    seasons = available_seasons(df)
    season = st.selectbox("Season", seasons, index=0)
    season_df = df[df["Season"].astype(str).eq(str(season))].copy()

    role_options = [r for r in ["CB", "FB", "MF", "AM", "W", "FW"] if r in ROLE_BUCKETS]
    role = st.selectbox("Target role", role_options, index=role_options.index("FW") if "FW" in role_options else 0)

    scope = st.selectbox("Candidate scope", ["All leagues", "Big Five", "Single competition", "Custom competitions"], index=0)
    comps = all_competitions(season_df)
    selected_comp = None
    custom_comps = []
    if scope == "Single competition":
        selected_comp = st.selectbox("Competition", comps)
    elif scope == "Custom competitions":
        custom_comps = st.multiselect("Custom competitions", comps, default=[])

    min_minutes = st.number_input("Minimum minutes", min_value=0, max_value=4000, value=900, step=100)
    age_min, age_max = st.columns(2)
    with age_min:
        min_age = st.number_input("Min age", min_value=14, max_value=45, value=16, step=1, key="finder_min_age")
    with age_max:
        max_age = st.number_input("Max age", min_value=14, max_value=45, value=30, step=1, key="finder_max_age")

    st.markdown("---")
    st.markdown("### Archetype preset")
    role_df_for_arch = season_df[season_df["Role bucket"].astype(str).eq(role)].copy()
    archetypes = (
        role_df_for_arch[["style_cluster_id", "style_cluster_name"]]
        .dropna()
        .drop_duplicates()
        .sort_values("style_cluster_name")
    )
    archetype_labels = ["All archetypes"] + [
        f"{row.style_cluster_name} · {row.style_cluster_id}" for _, row in archetypes.iterrows()
    ]
    archetype_choice = st.selectbox("Style archetype", archetype_labels, index=0)

pool = season_df[season_df["Role bucket"].astype(str).eq(role)].copy()
pool = pool[pd.to_numeric(pool["Minutes played"], errors="coerce").fillna(0) >= int(min_minutes)]
pool = pool[pd.to_numeric(pool["Age"], errors="coerce").between(min_age, max_age, inclusive="both")]

if scope == "Big Five":
    pool = filter_big_five(pool)
elif scope == "Single competition" and selected_comp:
    pool = pool[comp_filter(pool, selected_comp)]
elif scope == "Custom competitions" and custom_comps:
    mask = pd.Series(False, index=pool.index)
    for comp in custom_comps:
        mask = mask | comp_filter(pool, comp)
    pool = pool[mask]

selected_cluster_id = None
selected_cluster_name = "All archetypes"
if archetype_choice != "All archetypes":
    selected_cluster_id = archetype_choice.rsplit(" · ", 1)[-1]
    selected_cluster_name = archetype_choice.rsplit(" · ", 1)[0]
    pool = pool[pool["style_cluster_id"].astype(str).eq(selected_cluster_id)]

st.markdown(
    f"""
<div class="finder-preset-card">
  <div class="finder-preset-name">{html.escape(selected_cluster_name)}</div>
  <div class="finder-preset-meta">
    Role {html.escape(role)} · season {html.escape(str(season))} · candidate pool n={len(pool)}
  </div>
</div>
""",
    unsafe_allow_html=True,
)

criteria_config = CRITERIA_BY_ROLE.get(role, [])
usable_criteria: list[dict[str, Any]] = []
base_threshold_pool = season_df[season_df["Role bucket"].astype(str).eq(role)].copy()
base_threshold_pool = base_threshold_pool[pd.to_numeric(base_threshold_pool["Minutes played"], errors="coerce").fillna(0) >= int(min_minutes)]

st.markdown('<div class="finder-section-title">Raw metric criteria</div>', unsafe_allow_html=True)
st.caption("Attiva/disattiva i criteri. Le soglie sono raw e modificabili: servono come filtro qualitativo, non come ranking assoluto.")

criteria_cols = st.columns([1.15, 0.45, 0.65, 0.45])
criteria_cols[0].markdown('<div class="finder-criteria-head">Metric</div>', unsafe_allow_html=True)
criteria_cols[1].markdown('<div class="finder-criteria-head">Rule</div>', unsafe_allow_html=True)
criteria_cols[2].markdown('<div class="finder-criteria-head">Threshold</div>', unsafe_allow_html=True)
criteria_cols[3].markdown('<div class="finder-criteria-head">Active</div>', unsafe_allow_html=True)

for criterion in criteria_config:
    metric = effective_metric_name(base_threshold_pool, criterion)
    if metric is None:
        continue
    direction = criterion["direction"]
    default_threshold = build_default_threshold(base_threshold_pool, metric, direction, float(criterion.get("q", 0.5)))
    sign = "≥" if direction == "min" else "≤"
    key_base = f"finder_{role}_{metric}_{direction}".replace(" ", "_").replace("%", "pct").replace("'", "")
    c1, c2, c3, c4 = st.columns([1.15, 0.45, 0.65, 0.45])
    with c1:
        st.markdown(f"**{metric}**")
    with c2:
        st.markdown(f"`{sign}`")
    with c3:
        step = 0.01 if abs(default_threshold) < 3 else 0.10
        threshold = st.number_input(
            "threshold",
            value=float(round(default_threshold, 2)),
            step=step,
            label_visibility="collapsed",
            key=f"{key_base}_threshold",
        )
    with c4:
        active = st.checkbox("active", value=True, label_visibility="collapsed", key=f"{key_base}_active")
    if active:
        usable_criteria.append({"metric": metric, "direction": direction, "threshold": float(threshold)})

if len(usable_criteria) == 0:
    st.warning("Attiva almeno un criterio.")
    st.stop()

scored = pool.copy()
for criterion in usable_criteria:
    metric = criterion["metric"]
    scored[f"pass__{metric}"] = scored[metric].apply(lambda v, c=criterion: pass_criterion(v, c["threshold"], c["direction"]))

pass_cols = [f"pass__{c['metric']}" for c in usable_criteria]
scored["criteria_matched"] = scored[pass_cols].sum(axis=1)
scored["criteria_total"] = len(usable_criteria)

sort_options = ["Criteria matched", *[c["metric"] for c in usable_criteria if c["direction"] == "min"], "Age ascending", "Minutes"]
sort_by = st.selectbox("Sort shortlist by", sort_options, index=0)
if sort_by == "Criteria matched":
    scored = scored.sort_values(["criteria_matched", "Minutes played"], ascending=[False, False])
elif sort_by == "Age ascending":
    scored = scored.sort_values(["criteria_matched", "Age"], ascending=[False, True])
elif sort_by == "Minutes":
    scored = scored.sort_values(["criteria_matched", "Minutes played"], ascending=[False, False])
else:
    scored = scored.sort_values(["criteria_matched", sort_by], ascending=[False, False])

strict = scored[scored["criteria_matched"].eq(len(usable_criteria))].copy()
near = scored[(scored["criteria_matched"] >= max(1, len(usable_criteria) - 1)) & ~scored.index.isin(strict.index)].copy()
wildcards = scored[
    (pd.to_numeric(scored["Age"], errors="coerce") <= 23)
    & (scored["criteria_matched"] >= max(1, len(usable_criteria) - 2))
    & ~scored.index.isin(strict.index)
    & ~scored.index.isin(near.index)
].copy()

summary_cols = st.columns(4)
summary_cols[0].metric("Candidate pool", len(pool))
summary_cols[1].metric("Strict matches", len(strict))
summary_cols[2].metric("Near matches", len(near))
summary_cols[3].metric("Wildcards U23", len(wildcards))

render_cards(strict, usable_criteria, "Strict matches", limit=14)
render_cards(near, usable_criteria, "Near matches", limit=10)
render_cards(wildcards, usable_criteria, "Wildcard profiles", limit=8)

with st.expander("Full shortlisted table"):
    show_cols = [
        c for c in [
            "Player",
            "Age",
            "Position",
            "Team",
            "League",
            "style_cluster_name",
            "Minutes played",
            "criteria_matched",
            "criteria_total",
            *[c["metric"] for c in usable_criteria],
        ]
        if c in scored.columns
    ]
    st.markdown(render_small_table(scored.head(120)[show_cols]), unsafe_allow_html=True)
