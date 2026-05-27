from __future__ import annotations

import html
import math
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from src.competition_utils import filter_big_five
from src.data_loader import available_leagues, available_seasons, load_players_enriched
from src.export_utils import render_export_png_button
from src.gk_data_loader import available_gk_leagues, available_gk_seasons, load_gk_enriched
from src.gk_metric_catalog import GK_CARD_GROUPS
from src.gk_scoring import (
    all_group_scores as all_gk_group_scores,
    format_metric_value as format_gk_metric_value,
    metric_series as gk_metric_series,
    overall as gk_overall,
    percentile_rank as gk_percentile_rank,
)
from src.metric_catalog import CARD_GROUPS, ROLE_BUCKETS
from src.scoring import (
    all_group_scores,
    format_metric_value,
    metric_series,
    percentile_rank,
    role_overall,
)
from src.ui import inject_css, pct_color

st.set_page_config(page_title="Ranking", page_icon="🏆", layout="wide")
inject_css()


st.markdown(
    """
    <style>
    /* RANKING PAGE RESTORE */
    .ranking-hero {
        margin: 1.2rem 0 1.4rem 0;
        padding: 26px 28px;
        border: 1px solid rgba(95,255,224,0.18);
        border-radius: 24px;
        background: radial-gradient(circle at top left, rgba(95,255,224,0.11), transparent 35%),
                    linear-gradient(110deg, rgba(16,22,43,0.86), rgba(33,21,60,0.68));
        box-shadow: 0 18px 62px rgba(0,0,0,0.30), inset 0 0 26px rgba(95,255,224,0.04);
    }
    .ranking-kicker {
        color: #AFC3E8;
        font-size: 0.86rem;
        font-weight: 900;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .ranking-title {
        color: #F8FBFF;
        font-size: 3rem;
        line-height: 1.0;
        font-weight: 950;
        letter-spacing: -0.03em;
        text-shadow: 0 0 18px rgba(95,255,224,0.18);
        margin-bottom: 10px;
    }
    .ranking-subtitle {
        color: #B7CAE8;
        font-size: 1rem;
        font-weight: 650;
    }
    .ranking-pill-row {
        margin-top: 14px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .ranking-pill {
        display: inline-flex;
        align-items: center;
        min-height: 28px;
        padding: 5px 10px;
        border-radius: 999px;
        background: rgba(95,255,224,0.10);
        color: #BFFFF4;
        border: 1px solid rgba(95,255,224,0.20);
        font-size: 0.74rem;
        font-weight: 850;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .ranking-panel {
        background: rgba(16, 22, 43, 0.84);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 16px 16px 10px 16px;
        margin-bottom: 18px;
        box-shadow: 0 14px 44px rgba(0,0,0,0.23);
    }
    .ranking-panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding-bottom: 10px;
        margin-bottom: 6px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .ranking-panel-title {
        color: #5FFFE0;
        font-size: 1.00rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .ranking-panel-context {
        color: #8EA2C6;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .ranking-row {
        display: grid;
        grid-template-columns: 38px minmax(0, 1fr) 70px;
        align-items: center;
        gap: 12px;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.055);
    }
    .ranking-row:last-child {border-bottom: 0;}
    .ranking-rank {
        color: #B7CAE8;
        font-size: 0.95rem;
        font-weight: 950;
        text-align: center;
    }
    .ranking-player {
        min-width: 0;
    }
    .ranking-player-name {
        color: #F6F7FB;
        font-size: 1.00rem;
        font-weight: 950;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .ranking-player-meta {
        color: #8EA2C6;
        font-size: 0.78rem;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 2px;
    }
    .ranking-value {
        color: #F6F7FB;
        font-size: 1.00rem;
        font-weight: 950;
        text-align: right;
        font-variant-numeric: tabular-nums;
    }
    .ranking-pct {
        display: inline-flex;
        margin-top: 4px;
        min-width: 34px;
        height: 22px;
        border-radius: 999px;
        align-items: center;
        justify-content: center;
        font-size: 0.74rem;
        font-weight: 950;
        background: rgba(95,255,224,0.10);
        border: 1px solid rgba(95,255,224,0.22);
    }
    .ranking-empty {
        color: #8EA2C6;
        font-size: 0.92rem;
        padding: 12px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown('<div class="fm-title">RANKING</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fm-subtitle">Top 5 per metrica · giocatori di movimento e portieri · raw o possession-adjusted</div>',
    unsafe_allow_html=True,
)

export_left, export_right = st.columns([5.5, 1.2])
with export_left:
    st.write("")
with export_right:
    render_export_png_button("ranking")


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


OUTFIELD_OVERVIEW_METRICS: list[dict[str, Any]] = [
    {"label": "Goals", "column": "Goals", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "xG + xA", "derived": "xG + xA", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Goals + Assists", "derived": "Goals + Assists", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Key passes", "column": "Key passes", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Progressive passes", "column": "Progressive passes", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Dribbles successful", "column": "Dribbles successful", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Defensive challenges", "column": "Defensive challenges", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Pass accuracy %", "column": "Passes accurate, %", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
]

GK_OVERVIEW_METRICS: list[dict[str, Any]] = [
    {"label": "Goals prevented", "column": "Goals prevented", "adjustment": "none", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Goals prevented %", "column": "Goals prevented, %", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
    {"label": "Shots saved %", "column": "Shots saved, %", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
    {"label": "xG per goal conceded", "column": "xG per goal conceded", "adjustment": "none", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Cross claim rate", "column": "Cross claim rate", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
    {"label": "Sweeping actions", "column": "Sweeping actions", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
    {"label": "Pass accuracy %", "column": "Passes accurate, %", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
    {"label": "Long pass accuracy %", "column": "Long passes accurate, %", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
]


def get_outfield_metrics_for_family(family: str) -> list[dict[str, Any]]:
    if family == "Overview":
        return OUTFIELD_OVERVIEW_METRICS
    return list(CARD_GROUPS.get(family, {}).get("metrics", []))


def get_gk_metrics_for_family(family: str) -> list[dict[str, Any]]:
    if family == "Overview":
        return GK_OVERVIEW_METRICS
    return list(GK_CARD_GROUPS.get(family, {}).get("metrics", []))


def make_scope_pool(data: pd.DataFrame, season: str, scope: str, league: str | None, min_minutes: int) -> pd.DataFrame:
    pool = data[data["Season"].astype(str).eq(str(season))].copy()
    pool = pool[pd.to_numeric(pool["Minutes played"], errors="coerce").fillna(0) >= min_minutes]
    if scope == "Single league" and league:
        pool = pool[pool["League"].astype(str).eq(str(league))]
    elif scope == "Big Five":
        pool = filter_big_five(pool)
    elif scope == "All leagues":
        pass
    return pool.reset_index(drop=True)


def make_outfield_reference(pool_all_positions: pd.DataFrame, role_filter: str) -> pd.DataFrame:
    if role_filter == "All positions":
        return pool_all_positions.copy()
    return pool_all_positions[pool_all_positions["Role bucket"].astype(str).eq(role_filter)].copy()


def rank_metric(
    pool: pd.DataFrame,
    reference_df: pd.DataFrame,
    metric: dict[str, Any],
    mode: str,
    *,
    is_gk: bool,
    top_n: int = 25,
) -> pd.DataFrame:
    series_fn = gk_metric_series if is_gk else metric_series
    pct_fn = gk_percentile_rank if is_gk else percentile_rank

    values = series_fn(pool, metric, mode)
    ref_values = series_fn(reference_df, metric, mode)
    higher = metric_higher_is_better(metric)

    base_cols = ["Player", "Team", "League", "Season", "Age", "Nationality", "Minutes played"]
    if not is_gk and "Position" in pool.columns:
        base_cols.extend(["Position", "Role bucket"])
    available_cols = [c for c in base_cols if c in pool.columns]

    out = pool[available_cols].copy()
    out["_value"] = pd.to_numeric(values, errors="coerce")
    out = out.dropna(subset=["_value"])
    if out.empty:
        return out

    out["_pct"] = out["_value"].apply(lambda x: pct_fn(x, ref_values, higher))
    out = out.sort_values("_value", ascending=not higher).head(top_n).reset_index(drop=True)
    out.insert(0, "Rank", np.arange(1, len(out) + 1))
    return out


def rank_outfield_overall(pool: pd.DataFrame, reference_df: pd.DataFrame, role_filter: str, mode: str, top_n: int = 25) -> pd.DataFrame:
    if role_filter == "All positions":
        return pd.DataFrame()

    records = []
    for _, row in pool.iterrows():
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


def rank_gk_overall(pool: pd.DataFrame, reference_df: pd.DataFrame, mode: str, top_n: int = 25) -> pd.DataFrame:
    records = []
    for _, row in pool.iterrows():
        scores = all_gk_group_scores(row, reference_df, mode)
        ov = gk_overall(scores)
        if not pd.isna(ov) and not math.isnan(ov):
            records.append(
                {
                    "Player": row.get("Player"),
                    "Team": row.get("Team"),
                    "League": row.get("League"),
                    "Season": row.get("Season"),
                    "Age": row.get("Age"),
                    "Position": "GK",
                    "Role bucket": "GK",
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
    dataset_type = st.selectbox("Player type", ["Outfield players", "Goalkeepers"], index=0)
    is_gk = dataset_type == "Goalkeepers"

    if is_gk:
        df = load_gk_enriched()
        seasons = available_gk_seasons(df)
    else:
        df = load_players_enriched()
        seasons = available_seasons(df)

    season = st.selectbox("Season", seasons, index=0)

    season_df = df[df["Season"].astype(str).eq(str(season))].copy()
    scope = st.selectbox("Competition scope", ["Single league", "Big Five", "All leagues"], index=1)

    selected_league = None
    if scope == "Single league":
        leagues = available_gk_leagues(season_df) if is_gk else available_leagues(season_df)
        selected_league = st.selectbox("League", leagues, index=0)

    if is_gk:
        role_filter = "GK"
        family_options = ["Overview", *list(GK_CARD_GROUPS.keys())]
        metric_family = st.selectbox("Metric family", family_options, index=0)
    else:
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

pool_all = make_scope_pool(df, str(season), scope, selected_league, min_minutes)

if is_gk:
    pool = pool_all.copy()
    reference_df = pool_all.copy()
else:
    pool = pool_all.copy()
    if role_filter != "All positions":
        pool = pool[pool["Role bucket"].astype(str).eq(role_filter)].copy()
    reference_df = make_outfield_reference(pool_all, role_filter)

if pool.empty or reference_df.empty:
    st.warning("Nessun giocatore disponibile con questi filtri.")
    st.stop()

scope_label = selected_league if scope == "Single league" else scope
role_label = "GK" if is_gk else role_filter
page_title = "Goalkeeper Rankings" if is_gk else f"{html.escape(metric_family)} Rankings"

st.markdown(
    f"""
    <div class="ranking-hero">
      <div class="ranking-kicker">{'Goalkeeper ranking overview' if is_gk else 'Ranking overview'}</div>
      <div class="ranking-title">{html.escape(metric_family)} Rankings</div>
      <div class="ranking-subtitle">{html.escape(scope_label)} · {html.escape(str(season))} · {html.escape(role_label)} · min {min_minutes} minutes · {html.escape(mode)}</div>
      <div class="ranking-pill-row">
        <span class="ranking-pill">{html.escape(dataset_type)}</span>
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


def render_ranking_panel(title: str, table: pd.DataFrame, fmt: str, color: str = "#5FFFE0", *, is_gk_panel: bool = False) -> None:
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
            if fmt == "overall":
                value = f'{row["_value"]:.0f}'
            else:
                value = format_gk_metric_value(row["_value"], fmt) if is_gk_panel else format_metric_value(row["_value"], fmt)

            pct = row.get("_pct", np.nan)
            pct_txt = "—" if pd.isna(pct) or math.isnan(float(pct)) else f"{float(pct):.0f}"
            pct_col = pct_color(float(pct)) if not pd.isna(pct) else "#8EA2C6"
            position = "GK" if is_gk_panel else safe_text(row.get("Position"))
            meta = (
                f"{fmt_intish(row.get('Age'))}, {position}, "
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
            if fmt == "overall":
                show["Value"] = show["_value"].apply(lambda v: f"{v:.0f}")
            else:
                show["Value"] = show["_value"].apply(
                    lambda v: format_gk_metric_value(v, fmt) if is_gk_panel else format_metric_value(v, fmt)
                )
            show["Percentile"] = show["_pct"].apply(lambda v: "—" if pd.isna(v) else f"{v:.0f}")
            if "Position" not in show.columns:
                show["Position"] = "GK"
            cols = ["Rank", "Player", "Team", "League", "Age", "Position", "Minutes played", "Value", "Percentile"]
            st.dataframe(show[cols], use_container_width=True, hide_index=True)


if is_gk:
    metrics_to_render = get_gk_metrics_for_family(metric_family)
else:
    metrics_to_render = get_outfield_metrics_for_family(metric_family)

ranking_items: list[tuple[str, pd.DataFrame, str, str]] = []

if is_gk and metric_family == "Overview":
    ranking_items.append(("GK Overall", rank_gk_overall(pool, reference_df, mode), "overall", "#5FFFE0"))
elif (not is_gk) and role_filter != "All positions" and metric_family == "Overview":
    ranking_items.append(("Overall role fit", rank_outfield_overall(pool, reference_df, role_filter, mode), "overall", "#5FFFE0"))

for metric in metrics_to_render:
    key = metric_key(metric)
    if key not in pool.columns and key not in reference_df.columns:
        continue
    ranking_items.append(
        (
            metric_label(metric),
            rank_metric(pool, reference_df, metric, mode, is_gk=is_gk),
            metric_format(metric),
            "#5FFFE0",
        )
    )

if not ranking_items:
    st.info("Nessuna metrica disponibile per questi filtri.")
else:
    panel_cols = st.columns(2)
    for idx, (title, table, fmt, color) in enumerate(ranking_items):
        if is_gk and metric_family in GK_CARD_GROUPS:
            color = GK_CARD_GROUPS[metric_family].get("color", color)
        elif (not is_gk) and metric_family in CARD_GROUPS:
            color = CARD_GROUPS[metric_family].get("color", color)
        with panel_cols[idx % 2]:
            render_ranking_panel(title, table, fmt, color, is_gk_panel=is_gk)
