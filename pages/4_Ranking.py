from __future__ import annotations

import html
import math
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import available_leagues, available_seasons, load_players_enriched
from src.export_utils import render_export_png_button
from src.metric_catalog import BIG_FIVE_LEAGUES, CARD_GROUPS, ROLE_BUCKETS
from src.scoring import (
    all_group_scores,
    build_reference_df,
    format_metric_value,
    metric_series,
    percentile_rank,
    role_overall,
)
from src.ui import inject_css, pct_color

st.set_page_config(page_title="Ranking", page_icon="🏆", layout="wide")
inject_css()

st.markdown('<div class="fm-title">RANKING</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fm-subtitle">Top 5 per metrica · raw o possession-adjusted · campionato singolo, Big Five o tutte le leghe</div>',
    unsafe_allow_html=True,
)

export_left, export_right = st.columns([5.5, 1.2])
with export_left:
    st.write("")
with export_right:
    render_export_png_button("ranking")

df = load_players_enriched()


def safe_text(value: Any, fallback: str = "—") -> str:
    if pd.isna(value):
        return fallback
    return str(value)


def fmt_intish(value: Any, suffix: str = "") -> str:
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):,.0f}{suffix}".replace(",", ".")
    except Exception:
        return f"{value}{suffix}"


def metric_label(metric: dict[str, Any] | str) -> str:
    if isinstance(metric, str):
        return metric
    return metric.get("label") or metric.get("column") or metric.get("derived") or "Metric"


def metric_key(metric: dict[str, Any] | str) -> str:
    if isinstance(metric, str):
        return metric
    return metric.get("derived") or metric.get("column") or metric.get("label") or "metric"


def metric_format(metric: dict[str, Any] | str) -> str:
    if isinstance(metric, str):
        return "0.00"
    return metric.get("fmt", "0.00")


def metric_higher_is_better(metric: dict[str, Any] | str) -> bool:
    if isinstance(metric, str):
        return True
    return bool(metric.get("higher_is_better", True))


OVERVIEW_METRICS: list[dict[str, Any]] = [
    {"label": "Goals", "column": "Goals", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "xG + xA", "derived": "xG + xA", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Goals + Assists", "derived": "Goals + Assists", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Key passes", "column": "Key passes", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Progressive passes", "column": "Progressive passes", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Dribbles successful", "column": "Dribbles successful", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Defensive challenges", "column": "Defensive challenges", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Pass accuracy %", "column": "Passes accurate, %", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
]


def get_metrics_for_family(family: str) -> list[dict[str, Any]]:
    if family == "Overview":
        return OVERVIEW_METRICS
    return list(CARD_GROUPS.get(family, {}).get("metrics", []))


def make_scope_pool(data: pd.DataFrame, season: str, scope: str, league: str | None, min_minutes: int) -> pd.DataFrame:
    pool = data[data["Season"].astype(str).eq(str(season))].copy()
    pool = pool[pd.to_numeric(pool["Minutes played"], errors="coerce").fillna(0) >= min_minutes]
    if scope == "Single league" and league:
        pool = pool[pool["League"].astype(str).eq(str(league))]
    elif scope == "Big Five":
        pool = pool[pool["League"].isin(BIG_FIVE_LEAGUES)]
    elif scope == "All leagues":
        pass
    return pool.reset_index(drop=True)


def make_reference_for_pool(pool: pd.DataFrame, role_filter: str) -> pd.DataFrame:
    if role_filter == "All positions":
        return pool.copy()
    return pool[pool["Role bucket"].astype(str).eq(role_filter)].copy()


def rank_metric(pool: pd.DataFrame, reference_df: pd.DataFrame, metric: dict[str, Any], mode: str, top_n: int = 25) -> pd.DataFrame:
    values = metric_series(pool, metric, mode)
    ref_values = metric_series(reference_df, metric, mode)
    higher = metric_higher_is_better(metric)

    out = pool[["Player", "Team", "League", "Season", "Age", "Position", "Role bucket", "Nationality", "Minutes played"]].copy()
    out["_value"] = pd.to_numeric(values, errors="coerce")
    out = out.dropna(subset=["_value"])
    if out.empty:
        return out

    out["_pct"] = out["_value"].apply(lambda x: percentile_rank(x, ref_values, higher))
    out = out.sort_values("_value", ascending=not higher).head(top_n).reset_index(drop=True)
    out.insert(0, "Rank", np.arange(1, len(out) + 1))
    return out


def rank_overall(pool: pd.DataFrame, reference_df: pd.DataFrame, role_filter: str, mode: str, top_n: int = 25) -> pd.DataFrame:
    if role_filter == "All positions":
        return pd.DataFrame()

    records = []
    for idx, row in pool.iterrows():
        scores = all_group_scores(row, reference_df, mode)
        ov = role_overall(scores, role_filter)
        if not pd.isna(ov) and not math.isnan(ov):
            records.append(
                {
                    "Player": row.get("Player"),
                    "Team": row.get("Team"),
                    "League": row.get("League"),
                    "Season": row.get("Season"),
                    "Age": row.get("Age"),
                    "Position": row.get("Position"),
                    "Role bucket": row.get("Role bucket"),
                    "Nationality": row.get("Nationality"),
                    "Minutes played": row.get("Minutes played"),
                    "_value": ov,
                    "_pct": ov,
                }
            )

    out = pd.DataFrame.from_records(records)
    if out.empty:
        return out
    out = out.sort_values("_value", ascending=False).head(top_n).reset_index(drop=True)
    out.insert(0, "Rank", np.arange(1, len(out) + 1))
    return out


with st.sidebar:
    st.markdown("### Ranking filters")
    seasons = available_seasons(df)
    season = st.selectbox("Season", seasons, index=0)

    season_df = df[df["Season"].astype(str).eq(str(season))].copy()
    scope = st.selectbox("Competition scope", ["Single league", "Big Five", "All leagues"], index=1)

    selected_league = None
    if scope == "Single league":
        selected_league = st.selectbox("League", available_leagues(season_df), index=0)

    role_options = ["All positions", *list(ROLE_BUCKETS.keys())]
    role_filter = st.selectbox("Position group", role_options, index=0)

    family_options = ["Overview", *list(CARD_GROUPS.keys())]
    metric_family = st.selectbox("Metric family", family_options, index=0)

    mode = st.selectbox("Metric value", ["Raw", "Possession-adjusted"], index=1)

    st.markdown('<div class="control-label">Minimum minutes</div>', unsafe_allow_html=True)
    if "ranking_min_minutes_ref" not in st.session_state:
        st.session_state["ranking_min_minutes_ref"] = 900

    minus_col, value_col, plus_col = st.columns([0.9, 1.5, 0.9])
    with minus_col:
        if st.button("−", key="ranking_minutes_minus", use_container_width=True):
            st.session_state["ranking_min_minutes_ref"] = max(0, int(st.session_state["ranking_min_minutes_ref"]) - 100)
    with plus_col:
        if st.button("+", key="ranking_minutes_plus", use_container_width=True):
            st.session_state["ranking_min_minutes_ref"] = min(2500, int(st.session_state["ranking_min_minutes_ref"]) + 100)

    min_minutes = int(st.session_state["ranking_min_minutes_ref"])
    with value_col:
        st.markdown(f'<div class="minute-stepper-value">{min_minutes}</div>', unsafe_allow_html=True)

pool = make_scope_pool(df, str(season), scope, selected_league, min_minutes)
if role_filter != "All positions":
    pool = pool[pool["Role bucket"].astype(str).eq(role_filter)].copy()
reference_df = make_reference_for_pool(make_scope_pool(df, str(season), scope, selected_league, min_minutes), role_filter)

if pool.empty or reference_df.empty:
    st.warning("Nessun giocatore disponibile con questi filtri.")
    st.stop()

scope_label = selected_league if scope == "Single league" else scope
role_label = role_filter
st.markdown(
    f"""
    <div class="ranking-hero">
      <div class="ranking-kicker">Ranking overview</div>
      <div class="ranking-title">{html.escape(metric_family)} Rankings</div>
      <div class="ranking-subtitle">{html.escape(scope_label)} · {html.escape(str(season))} · {html.escape(role_label)} · min {min_minutes} minutes · {html.escape(mode)}</div>
      <div class="ranking-pill-row">
        <span class="ranking-pill">Pool n = {len(pool)}</span>
        <span class="ranking-pill">Reference n = {len(reference_df)}</span>
        <span class="ranking-pill">Top 5 visible</span>
        <span class="ranking-pill">Expand for top 25</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if len(reference_df) < 20:
    st.warning(
        f"Reference group piccolo: {len(reference_df)} giocatori. I percentili potrebbero essere instabili."
    )


def render_ranking_panel(title: str, table: pd.DataFrame, fmt: str, color: str = "#5FFFE0") -> None:
    safe_title = html.escape(title)
    panel_html = (
        f'<div class="ranking-panel" style="border-color:{color}38;">'
        f'<div class="ranking-panel-header">'
        f'<div class="ranking-panel-title" style="color:{color};">{safe_title}</div>'
        f'<div class="ranking-panel-context">Top 5</div>'
        f'</div>'
    )

    if table.empty:
        panel_html += '<div class="ranking-empty">No data available for this metric.</div>'
    else:
        for _, row in table.head(5).iterrows():
            value = format_metric_value(row["_value"], fmt) if fmt != "overall" else f'{row["_value"]:.0f}'
            pct = row.get("_pct", np.nan)
            pct_txt = "—" if pd.isna(pct) or math.isnan(float(pct)) else f"{float(pct):.0f}"
            pct_col = pct_color(float(pct)) if not pd.isna(pct) else "#8EA2C6"
            meta = (
                f"{fmt_intish(row.get('Age'))}, {safe_text(row.get('Position'))}, "
                f"{safe_text(row.get('Team'))} · {safe_text(row.get('League'))}"
            )
            panel_html += (
                '<div class="ranking-row">'
                f'<div class="ranking-rank">{int(row["Rank"])}</div>'
                '<div class="ranking-player">'
                f'<div class="ranking-player-name">{html.escape(safe_text(row.get("Player")))}</div>'
                f'<div class="ranking-player-meta">{html.escape(meta)}</div>'
                '</div>'
                '<div class="ranking-value">'
                f'{html.escape(value)}'
                f'<div class="ranking-pct" style="color:{pct_col};">{pct_txt}</div>'
                '</div>'
                '</div>'
            )

    panel_html += "</div>"
    st.markdown(panel_html, unsafe_allow_html=True)

    if not table.empty:
        with st.expander(f"EXPAND · {title}"):
            show = table.copy()
            show["Value"] = show["_value"].apply(lambda v: f"{v:.0f}" if fmt == "overall" else format_metric_value(v, fmt))
            show["Percentile"] = show["_pct"].apply(lambda v: "—" if pd.isna(v) else f"{v:.0f}")
            cols = ["Rank", "Player", "Team", "League", "Age", "Position", "Minutes played", "Value", "Percentile"]
            st.dataframe(show[cols], use_container_width=True, hide_index=True)


metrics_to_render = get_metrics_for_family(metric_family)

ranking_items: list[tuple[str, pd.DataFrame, str, str]] = []
if role_filter != "All positions" and metric_family == "Overview":
    ranking_items.append(("Overall role fit", rank_overall(pool, reference_df, role_filter, mode), "overall", "#5FFFE0"))

for metric in metrics_to_render:
    key = metric_key(metric)
    if key not in pool.columns and key not in reference_df.columns:
        continue
    ranking_items.append(
        (
            metric_label(metric),
            rank_metric(pool, reference_df, metric, mode),
            metric_format(metric),
            "#5FFFE0",
        )
    )

if not ranking_items:
    st.info("Nessuna metrica disponibile per questi filtri.")
else:
    panel_cols = st.columns(2)
    for idx, (title, table, fmt, color) in enumerate(ranking_items):
        # Use family color where possible
        if metric_family in CARD_GROUPS:
            color = CARD_GROUPS[metric_family].get("color", color)
        with panel_cols[idx % 2]:
            render_ranking_panel(title, table, fmt, color)
