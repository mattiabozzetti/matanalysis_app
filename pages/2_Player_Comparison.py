from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import available_leagues, available_seasons, load_players_enriched
from src.gk_data_loader import available_gk_leagues, available_gk_seasons, load_gk_enriched
from src.gk_metric_catalog import (
    BIG_FIVE_LEAGUES as GK_BIG_FIVE_LEAGUES,
    GK_CARD_GROUPS,
    GK_RADAR_AXES,
)
from src.gk_scoring import (
    all_group_scores as all_gk_group_scores,
    build_gk_reference_df,
    format_metric_value as format_gk_metric_value,
    metric_value_and_percentile as gk_metric_value_and_percentile,
    overall as gk_overall,
    radar_axis_score as gk_radar_axis_score,
)
from src.metric_catalog import BIG_FIVE_LEAGUES, CARD_GROUPS, RADAR_AXES, ROLE_BUCKETS
from src.scoring import (
    all_group_scores,
    build_reference_df,
    format_metric_value,
    metric_value_and_percentile,
    radar_axis_score,
    role_overall,
)
from src.ui import inject_css, pct_color
from src.comparison_png_export import create_comparison_png

st.set_page_config(page_title="Player Comparison", page_icon="⚔️", layout="wide")
inject_css()

st.markdown('<div class="fm-title">PLAYER COMPARISON</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fm-subtitle">Confronto player-vs-player · outfield o GK · valori raw/PAdj · barre e score in percentile</div>',
    unsafe_allow_html=True,
)

player_type = st.selectbox("Comparison type", ["Outfield players", "Goalkeepers"], index=0)

IS_GK = player_type == "Goalkeepers"
if IS_GK:
    df = load_gk_enriched()
    GROUPS = GK_CARD_GROUPS
    RADAR = GK_RADAR_AXES
    big_five = GK_BIG_FIVE_LEAGUES
    type_label = "GK"
else:
    df = load_players_enriched()
    GROUPS = CARD_GROUPS
    RADAR = None
    big_five = BIG_FIVE_LEAGUES
    type_label = "OUTFIELD"


def _fmt_text(value, fallback="—") -> str:
    if pd.isna(value):
        return fallback
    return str(value)


def _fmt_intish(value, suffix="") -> str:
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):,.0f}{suffix}".replace(",", ".")
    except Exception:
        return f"{value}{suffix}"


def _available_seasons(data: pd.DataFrame) -> list[str]:
    return available_gk_seasons(data) if IS_GK else available_seasons(data)


def _available_leagues(data: pd.DataFrame) -> list[str]:
    return available_gk_leagues(data) if IS_GK else available_leagues(data)


def _player_pool(data: pd.DataFrame, season: str, league: str, team: str) -> pd.DataFrame:
    pool = data[data["Season"].astype(str).eq(str(season))].copy()
    if league != "All leagues":
        pool = pool[pool["League"].astype(str).eq(league)]
    if team != "All teams":
        pool = pool[pool["Team"].astype(str).eq(team)]
    return pool


def _player_selector(prefix: str, title: str, default_league: str | None = None) -> pd.Series:
    st.markdown(f'<div class="comparison-controls-title">{title}</div>', unsafe_allow_html=True)
    seasons = _available_seasons(df)
    c1, c2, c3, c4 = st.columns([1.0, 1.35, 1.35, 1.55])
    with c1:
        season = st.selectbox("Season", seasons, index=0, key=f"{prefix}_season", label_visibility="collapsed")

    season_df = df[df["Season"].astype(str).eq(str(season))].copy()
    leagues = ["All leagues", *_available_leagues(season_df)]
    league_index = 0
    if default_league and default_league in leagues:
        league_index = leagues.index(default_league)
    with c2:
        league = st.selectbox("League", leagues, index=league_index, key=f"{prefix}_league", label_visibility="collapsed")

    pool_for_teams = _player_pool(df, season, league, "All teams")
    teams = ["All teams", *sorted(pool_for_teams["Team"].dropna().astype(str).unique().tolist())]
    with c3:
        team = st.selectbox("Team", teams, index=0, key=f"{prefix}_team", label_visibility="collapsed")

    pool = _player_pool(df, season, league, team)
    if pool.empty:
        st.warning(f"Nessun giocatore disponibile per {title.lower()}.")
        st.stop()

    if IS_GK:
        label_series = pool["Player"].astype(str) + " · " + pool["Team"].astype(str)
    else:
        label_series = pool["Player"].astype(str) + " · " + pool["Team"].astype(str) + " · " + pool["Position"].astype(str)

    options = pool.assign(_label=label_series).sort_values(["Player", "Team"])
    with c4:
        selected_label = st.selectbox("Player", options["_label"].tolist(), key=f"{prefix}_player", label_visibility="collapsed")
    idx = options.loc[options["_label"].eq(selected_label)].index[0]
    return df.loc[idx]


comparison_player = _player_selector("cmp", "COMPARISON PLAYER")
st.markdown('<div style="height:10px;border-bottom:1px solid rgba(95,255,224,0.14);margin:0.7rem 0 0.9rem 0;"></div>', unsafe_allow_html=True)
selected_player = _player_selector("sel", "SELECTED PLAYER", default_league=_fmt_text(comparison_player.get("League")))

context_cols = st.columns([1.1, 1.0, 1.1, 1.15, 1.15])

if IS_GK:
    compare_role = "GK"
    with context_cols[0]:
        st.markdown('<div class="control-label">Compare as role</div><div class="minute-stepper-value">GK only</div>', unsafe_allow_html=True)
else:
    role_keys = list(ROLE_BUCKETS.keys())
    default_role = selected_player.get("Role bucket", "AM")
    default_role_index = role_keys.index(default_role) if default_role in role_keys else 0
    with context_cols[0]:
        compare_role = st.selectbox("Compare as role", role_keys, index=default_role_index)

with context_cols[1]:
    mode = st.selectbox("Metric value", ["Raw", "Possession-adjusted"], index=1)
with context_cols[2]:
    reference_scope = st.selectbox("Reference scope", ["Player league", "Big Five", "All leagues", "Custom leagues"], index=0)

custom_leagues: list[str] = []
with context_cols[3]:
    if reference_scope == "Custom leagues":
        all_leagues = _available_leagues(df)
        custom_leagues = st.multiselect(
            "Custom leagues",
            all_leagues,
            default=[l for l in big_five if l in all_leagues],
        )
    else:
        st.markdown('<div class="control-label">Custom leagues</div><div class="minute-stepper-value">—</div>', unsafe_allow_html=True)

with context_cols[4]:
    st.markdown('<div class="control-label">Min ref minutes</div>', unsafe_allow_html=True)
    session_key = "gk_comp_min_minutes_ref" if IS_GK else "comparison_min_minutes_ref"
    if session_key not in st.session_state:
        st.session_state[session_key] = 900
    b1, bv, b2 = st.columns([0.8, 1.2, 0.8])
    with b1:
        if st.button("−", key=f"{session_key}_minus", use_container_width=True):
            st.session_state[session_key] = max(0, int(st.session_state[session_key]) - 100)
    with b2:
        if st.button("+", key=f"{session_key}_plus", use_container_width=True):
            st.session_state[session_key] = min(2500, int(st.session_state[session_key]) + 100)
    min_minutes = int(st.session_state[session_key])
    with bv:
        st.markdown(f'<div class="minute-stepper-value">{min_minutes}</div>', unsafe_allow_html=True)


def _build_ref(player_row: pd.Series) -> pd.DataFrame:
    player_league = str(player_row.get("League")) if pd.notna(player_row.get("League")) else None
    if IS_GK:
        return build_gk_reference_df(
            df,
            season=str(player_row.get("Season")),
            reference_scope=reference_scope,
            player_league=player_league,
            custom_leagues=custom_leagues,
            min_minutes=min_minutes,
        )
    return build_reference_df(
        df,
        season=str(player_row.get("Season")),
        role_bucket=compare_role,
        reference_scope=reference_scope,
        player_league=player_league,
        custom_leagues=custom_leagues,
        min_minutes=min_minutes,
    )


sel_ref = _build_ref(selected_player)
cmp_ref = _build_ref(comparison_player)

if IS_GK:
    sel_scores = all_gk_group_scores(selected_player, sel_ref, mode)
    cmp_scores = all_gk_group_scores(comparison_player, cmp_ref, mode)
    sel_overall = gk_overall(sel_scores)
    cmp_overall = gk_overall(cmp_scores)
else:
    sel_scores = all_group_scores(selected_player, sel_ref, mode)
    cmp_scores = all_group_scores(comparison_player, cmp_ref, mode)
    sel_overall = role_overall(sel_scores, compare_role)
    cmp_overall = role_overall(cmp_scores, compare_role)


def _overall_txt(value: float) -> str:
    return "—" if pd.isna(value) or math.isnan(value) else f"{value:.0f}"


def _meta(player_row: pd.Series) -> str:
    age = _fmt_intish(player_row.get("Age"), "y")
    minutes = _fmt_intish(player_row.get("Minutes played"), " min")
    position = "GK" if IS_GK else _fmt_text(player_row.get("Position"))
    return (
        f"{_fmt_text(player_row.get('Season'))} · {minutes} · {age}<br>"
        f"{_fmt_text(player_row.get('Team'))} · {_fmt_text(player_row.get('League'))} · {position}"
    )


st.markdown(
    f"""
    <div class="comparison-hero">
      <div class="comparison-player-left">
        <div class="comparison-name">{_fmt_text(selected_player.get('Player'))}</div>
        <div class="comparison-meta">{_meta(selected_player)}</div>
        <div class="comparison-overall-line">Overall <span class="comparison-overall-pill" style="color:{pct_color(sel_overall)};">{_overall_txt(sel_overall)}</span></div>
      </div>
      <div class="comparison-vs">VS</div>
      <div class="comparison-player-right">
        <div class="comparison-name">{_fmt_text(comparison_player.get('Player'))}</div>
        <div class="comparison-meta">{_meta(comparison_player)}</div>
        <div class="comparison-overall-line">Overall <span class="comparison-overall-pill" style="color:{pct_color(cmp_overall)};">{_overall_txt(cmp_overall)}</span></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

scope_label = reference_scope if reference_scope != "Custom leagues" else "Custom"
st.markdown(
    f'<div class="comparison-context">Percentile vs {compare_role} · {scope_label} · {mode} · min {min_minutes} minutes</div>',
    unsafe_allow_html=True,
)

small_refs = []
if len(sel_ref) < 20:
    small_refs.append(f"selected reference n={len(sel_ref)}")
if len(cmp_ref) < 20:
    small_refs.append(f"comparison reference n={len(cmp_ref)}")
if small_refs:
    st.warning("Reference group piccolo: " + " · ".join(small_refs) + ". I percentili potrebbero essere instabili.")



def _bar_width(pct: float) -> float:
    if pd.isna(pct) or math.isnan(pct):
        return 0
    return max(0, min(100, float(pct)))


def _pct_txt(pct: float) -> str:
    return "—" if pd.isna(pct) or math.isnan(pct) else f"{pct:.0f}"


def _score_txt(score: float) -> str:
    return "—" if pd.isna(score) or math.isnan(score) else f"{score:.0f}"


def comparison_metric_row(label: str, sel_value: str, sel_pct: float, cmp_value: str, cmp_pct: float) -> str:
    sel_color = pct_color(sel_pct)
    cmp_color = pct_color(cmp_pct)
    return f"""
    <div class="comparison-row">
      <div class="comparison-value-left">{sel_value}</div>
      <div class="comparison-pct-left" style="color:{sel_color};">{_pct_txt(sel_pct)}</div>
      <div class="comparison-bar-left"><div class="comparison-fill-left" style="width:{_bar_width(sel_pct):.0f}%;background:{sel_color};color:{sel_color};"></div></div>
      <div class="comparison-metric-label">{label}</div>
      <div class="comparison-bar-right"><div class="comparison-fill-right" style="width:{_bar_width(cmp_pct):.0f}%;background:{cmp_color};color:{cmp_color};"></div></div>
      <div class="comparison-pct-right" style="color:{cmp_color};">{_pct_txt(cmp_pct)}</div>
      <div class="comparison-value-right">{cmp_value}</div>
    </div>
    """


def _metric_vp(player_row: pd.Series, ref: pd.DataFrame, metric: dict, mode: str):
    if IS_GK:
        return gk_metric_value_and_percentile(player_row, ref, metric, mode)
    return metric_value_and_percentile(player_row, df, ref, metric, mode)


def _format_value(value: float, fmt: str) -> str:
    return format_gk_metric_value(value, fmt) if IS_GK else format_metric_value(value, fmt)


def _build_export_groups() -> list[dict]:
    export_groups: list[dict] = []
    for group_name, group in GROUPS.items():
        rows = []
        for metric in group.get("metrics", []):
            sel_value, sel_pct = _metric_vp(selected_player, sel_ref, metric, mode)
            cmp_value, cmp_pct = _metric_vp(comparison_player, cmp_ref, metric, mode)
            rows.append(
                {
                    "label": metric.get("label", metric.get("column", "Metric")),
                    "sel_value": _format_value(sel_value, metric.get("fmt", "0.00")),
                    "sel_pct": sel_pct,
                    "cmp_value": _format_value(cmp_value, metric.get("fmt", "0.00")),
                    "cmp_pct": cmp_pct,
                }
            )
        export_groups.append(
            {
                "name": group_name,
                "icon": group.get("icon", "•"),
                "color": group.get("color", "#5FFFE0"),
                "sel_score": sel_scores.get(group_name, float("nan")),
                "cmp_score": cmp_scores.get(group_name, float("nan")),
                "rows": rows,
            }
        )
    return export_groups


export_png = create_comparison_png(
    selected_player=selected_player,
    comparison_player=comparison_player,
    selected_overall=sel_overall,
    comparison_overall=cmp_overall,
    compare_role=compare_role,
    reference_scope=reference_scope,
    mode=mode,
    min_minutes=min_minutes,
    is_gk=IS_GK,
    groups=_build_export_groups(),
)
export_filename = f"comparison_{_fmt_text(selected_player.get('Player')).replace(' ', '_')}_vs_{_fmt_text(comparison_player.get('Player')).replace(' ', '_')}.png"

dl_left, dl_right = st.columns([5.5, 1.35])
with dl_left:
    st.write("")
with dl_right:
    st.download_button(
        "⬇ Export clean PNG",
        data=export_png,
        file_name=export_filename,
        mime="image/png",
        use_container_width=True,
    )


st.markdown("### Metric families")
panel_cols = st.columns(2)

for idx, (group_name, group) in enumerate(GROUPS.items()):
    group_color = group.get("color", "#5FFFE0")
    sel_score = sel_scores.get(group_name, float("nan"))
    cmp_score = cmp_scores.get(group_name, float("nan"))

    html = f"""
    <div class="comparison-panel" style="border-color:{group_color}40;">
      <div class="comparison-group-header">
        <div class="comparison-score-badge" style="color:{pct_color(sel_score)};">{_score_txt(sel_score)}</div>
        <div class="comparison-group-title" style="color:{group_color};">{group.get('icon', '•')} {group_name}</div>
        <div class="comparison-score-badge" style="color:{pct_color(cmp_score)};">{_score_txt(cmp_score)}</div>
      </div>
    """
    for metric in group.get("metrics", []):
        sel_value, sel_pct = _metric_vp(selected_player, sel_ref, metric, mode)
        cmp_value, cmp_pct = _metric_vp(comparison_player, cmp_ref, metric, mode)
        html += comparison_metric_row(
            metric.get("label", metric.get("column", "Metric")),
            _format_value(sel_value, metric.get("fmt", "0.00")),
            sel_pct,
            _format_value(cmp_value, metric.get("fmt", "0.00")),
            cmp_pct,
        )
    html += "</div>"

    with panel_cols[idx % 2]:
        st.markdown(html, unsafe_allow_html=True)


def radar_overlay_figure(labels: list[str], sel_values: list[float], cmp_values: list[float], title: str) -> go.Figure:
    def clean(vals):
        return [0 if pd.isna(v) else float(v) for v in vals]

    closed_labels = labels + [labels[0]]
    sel_clean = clean(sel_values)
    cmp_clean = clean(cmp_values)
    sel_closed = sel_clean + [sel_clean[0]]
    cmp_closed = cmp_clean + [cmp_clean[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=sel_closed,
            theta=closed_labels,
            fill="toself",
            name=_fmt_text(selected_player.get("Player")),
            line=dict(width=3, color="#5FFFE0"),
            marker=dict(size=5, color="#5FFFE0"),
            fillcolor="rgba(95,255,224,0.16)",
            hovertemplate="%{theta}: %{r:.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=cmp_closed,
            theta=closed_labels,
            fill="toself",
            name=_fmt_text(comparison_player.get("Player")),
            line=dict(width=3, color="#A855F7"),
            marker=dict(size=5, color="#A855F7"),
            fillcolor="rgba(168,85,247,0.14)",
            hovertemplate="%{theta}: %{r:.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18, color="#F6F7FB")),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(color="#8EA2C6"), gridcolor="rgba(255,255,255,0.15)"),
            angularaxis=dict(tickfont=dict(color="#DDE8FF", size=12), gridcolor="rgba(255,255,255,0.12)"),
        ),
        legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center", font=dict(color="#DDE8FF")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=38, r=38, t=58, b=58),
        showlegend=True,
        height=450,
    )
    return fig


st.markdown("### Comparison radar")
axes = GK_RADAR_AXES if IS_GK else RADAR_AXES.get(compare_role, [])
if axes:
    labels = [axis["axis"] for axis in axes]
    if IS_GK:
        sel_style = [gk_radar_axis_score(selected_player, sel_ref, axis.get("style", []), mode) for axis in axes]
        cmp_style = [gk_radar_axis_score(comparison_player, cmp_ref, axis.get("style", []), mode) for axis in axes]
        sel_perf = [gk_radar_axis_score(selected_player, sel_ref, axis.get("performance", []), mode) for axis in axes]
        cmp_perf = [gk_radar_axis_score(comparison_player, cmp_ref, axis.get("performance", []), mode) for axis in axes]
    else:
        sel_style = [radar_axis_score(selected_player, sel_ref, axis.get("style", []), mode) for axis in axes]
        cmp_style = [radar_axis_score(comparison_player, cmp_ref, axis.get("style", []), mode) for axis in axes]
        sel_perf = [radar_axis_score(selected_player, sel_ref, axis.get("performance", []), mode) for axis in axes]
        cmp_perf = [radar_axis_score(comparison_player, cmp_ref, axis.get("performance", []), mode) for axis in axes]

    r1, r2 = st.columns(2)
    with r1:
        st.markdown('<div class="comparison-radar-card">', unsafe_allow_html=True)
        st.plotly_chart(radar_overlay_figure(labels, sel_style, cmp_style, "Playing Style · volume percentiles"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with r2:
        st.markdown('<div class="comparison-radar-card">', unsafe_allow_html=True)
        st.plotly_chart(radar_overlay_figure(labels, sel_perf, cmp_perf, "Performance · execution percentiles"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Radar non definito per questo ruolo.")

