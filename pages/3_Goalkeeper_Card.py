from __future__ import annotations

import math

import numpy as np
import pandas as pd
import streamlit as st

from src.gk_data_loader import available_gk_leagues, available_gk_seasons, load_gk_enriched
from src.gk_metric_catalog import BIG_FIVE_LEAGUES, GK_CARD_GROUPS, GK_RADAR_AXES
from src.gk_scoring import (
    all_group_scores,
    build_gk_reference_df,
    format_metric_value,
    metric_value_and_percentile,
    overall,
    radar_axis_score,
)
from src.ui import inject_css, metric_row_html, pct_color, radar_figure
from src.export_utils import render_export_png_button

st.set_page_config(page_title="GK Card", page_icon="🧤", layout="wide")
inject_css()

st.markdown('<div class="fm-title">GOALKEEPER CARD</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fm-subtitle">Portieri · shot stopping · handling · distribuzione · radar in percentile</div>',
    unsafe_allow_html=True,
)

export_left, export_right = st.columns([5.5, 1.2])
with export_left:
    st.write("")
with export_right:
    render_export_png_button("gk_card")


df = load_gk_enriched()

with st.sidebar:
    st.markdown("### GK Filters")
    seasons = available_gk_seasons(df)
    season = st.selectbox("Season", seasons, index=0)

    season_df = df[df["Season"].astype(str).eq(str(season))].copy()
    league_filter = st.selectbox("GK league filter", ["All leagues", *available_gk_leagues(season_df)])
    pool = season_df.copy()
    if league_filter != "All leagues":
        pool = pool[pool["League"].astype(str).eq(league_filter)]

    teams = ["All teams", *sorted(pool["Team"].dropna().astype(str).unique().tolist())]
    selected_team = st.selectbox("Team filter", teams)
    if selected_team != "All teams":
        pool = pool[pool["Team"].astype(str).eq(selected_team)]

    if pool.empty:
        st.warning("Nessun portiere per questi filtri.")
        st.stop()

    player_options = (
        pool.assign(_label=pool["Player"].astype(str) + " · " + pool["Team"].astype(str))
        .sort_values(["Player", "Team"])
    )
    selected_label = st.selectbox("Goalkeeper", player_options["_label"].tolist())
    player_idx = player_options.loc[player_options["_label"].eq(selected_label)].index[0]
    player = df.loc[player_idx]

    st.markdown("---")
    st.markdown("### Percentile context")

    reference_scope = st.selectbox(
        "Reference scope",
        ["Player league", "Big Five", "All leagues", "Custom leagues"],
        index=0,
    )

    custom_leagues: list[str] = []
    if reference_scope == "Custom leagues":
        custom_leagues = st.multiselect(
            "Custom leagues",
            available_gk_leagues(season_df),
            default=[l for l in BIG_FIVE_LEAGUES if l in available_gk_leagues(season_df)],
        )

    st.markdown('<div class="control-label">Minimum minutes in reference group</div>', unsafe_allow_html=True)
    if "gk_min_minutes_ref" not in st.session_state:
        st.session_state["gk_min_minutes_ref"] = 900

    minus_col, value_col, plus_col = st.columns([0.9, 1.5, 0.9])
    with minus_col:
        if st.button("−", key="gk_minutes_minus", use_container_width=True):
            st.session_state["gk_min_minutes_ref"] = max(0, int(st.session_state["gk_min_minutes_ref"]) - 100)
    with plus_col:
        if st.button("+", key="gk_minutes_plus", use_container_width=True):
            st.session_state["gk_min_minutes_ref"] = min(2500, int(st.session_state["gk_min_minutes_ref"]) + 100)

    min_minutes = int(st.session_state["gk_min_minutes_ref"])
    with value_col:
        st.markdown(f'<div class="minute-stepper-value">{min_minutes}</div>', unsafe_allow_html=True)

    mode = st.selectbox("Metric value", ["Raw", "Possession-adjusted"], index=0)

player_league = str(player.get("League")) if pd.notna(player.get("League")) else None
reference_df = build_gk_reference_df(
    df,
    season=str(player.get("Season")),
    reference_scope=reference_scope,
    player_league=player_league,
    custom_leagues=custom_leagues,
    min_minutes=min_minutes,
)

scores = all_group_scores(player, reference_df, mode)
ov = overall(scores)


def fmt_intish(value, suffix=""):
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):,.0f}{suffix}".replace(",", ".")
    except Exception:
        return f"{value}{suffix}"


def fmt_text(value, fallback="—"):
    if pd.isna(value):
        return fallback
    return str(value)


nation = fmt_text(player.get("Nationality"))
club = fmt_text(player.get("Team"))
age = fmt_intish(player.get("Age"), " yrs")
height = fmt_intish(player.get("Height"), " cm")
minutes_txt = fmt_intish(player.get("Minutes played"))
season_tag = fmt_text(player.get("Season"))
possession = player.get("Ball possession, %")
possession_txt = "—" if pd.isna(possession) else f"{float(possession)*100:.1f}%"
cluster_name = fmt_text(player.get("style_cluster_name"), "Unclustered")
cluster_short = fmt_text(player.get("style_cluster_short_label"), cluster_name)
cluster_id = fmt_text(player.get("style_cluster_id"), "—")
cluster_conf = player.get("style_cluster_confidence")
cluster_conf_txt = "—" if pd.isna(cluster_conf) else f"{float(cluster_conf):.0f}%"

left, right = st.columns([5, 1.15], vertical_alignment="center")
with left:
    st.markdown(
        f"""
        <div class="hero-card hero-card-large">
          <div class="hero-topline">
            <span class="hero-tag">GOALKEEPER</span>
            <span class="hero-tag hero-tag-alt">{season_tag}</span>
          </div>
          <div class="hero-name hero-name-large">{fmt_text(player.get('Player'))}</div>
          <div class="hero-meta hero-meta-upper">{club} · {fmt_text(player.get('League'))}</div>
          <div class="hero-info-grid">
            <div class="hero-info-box"><span class="hero-info-label">NATION</span><span class="hero-info-value">{nation}</span></div>
            <div class="hero-info-box"><span class="hero-info-label">CLUB</span><span class="hero-info-value">{club}</span></div>
            <div class="hero-info-box"><span class="hero-info-label">AGE</span><span class="hero-info-value">{age}</span></div>
            <div class="hero-info-box"><span class="hero-info-label">HEIGHT</span><span class="hero-info-value">{height}</span></div>
            <div class="hero-info-box"><span class="hero-info-label">MINUTES</span><span class="hero-info-value">{minutes_txt}</span></div>
            <div class="hero-info-box"><span class="hero-info-label">ARCHETYPE</span><span class="hero-info-value">{cluster_short}</span></div>
          </div>
          <div class="hero-context-line">Percentile vs GK · {reference_scope} · reference n = {len(reference_df)} · {mode} · team possession = {possession_txt} · style cluster = {cluster_id} · confidence = {cluster_conf_txt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with right:
    ov_text = "—" if math.isnan(ov) else f"{ov:.0f}"
    st.markdown(
        f"""
        <div class="overall-badge">
          <div class="overall-inner">
            <div class="overall-value">{ov_text}</div>
            <div class="overall-label">GK OVERALL</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if len(reference_df) < 20:
    st.warning(
        f"Reference group piccolo: {len(reference_df)} portieri. I percentili potrebbero essere instabili. "
        "Abbassa i minuti minimi o amplia il perimetro campionati."
    )

st.markdown("### Goalkeeper metric families")
cols = st.columns(2)
for idx, (group_name, group) in enumerate(GK_CARD_GROUPS.items()):
    group_score = scores.get(group_name, np.nan)
    group_score_txt = "—" if pd.isna(group_score) else f"{group_score:.0f}"
    group_color = group.get("color", "#5FFFE0")
    html = f"""
    <div class="metric-panel">
      <div class="metric-group-header">
        <div class="metric-group-title" style="color:{group_color};">
          <span>{group.get('icon', '•')}</span><span>{group_name}</span>
        </div>
        <div class="group-score-badge" style="color:{pct_color(group_score)}; border-color:{group_color}55;">{group_score_txt}</div>
      </div>
    """
    for metric in group.get("metrics", []):
        value, pct = metric_value_and_percentile(player, reference_df, metric, mode)
        html += metric_row_html(
            metric.get("label", metric.get("column", "Metric")),
            format_metric_value(value, metric.get("fmt", "0.00")),
            pct,
        )
    html += "</div>"
    with cols[idx % 2]:
        st.markdown(html, unsafe_allow_html=True)

st.markdown("### GK radar")
axes = GK_RADAR_AXES
labels = [axis["axis"] for axis in axes]
style_values = [radar_axis_score(player, reference_df, axis.get("style", []), mode) for axis in axes]
perf_values = [radar_axis_score(player, reference_df, axis.get("performance", []), mode) for axis in axes]

r1, r2 = st.columns(2)
with r1:
    st.plotly_chart(radar_figure(labels, style_values, "Playing Style · GK volume percentiles"), use_container_width=True)
with r2:
    st.plotly_chart(radar_figure(labels, perf_values, "Performance · GK execution percentiles"), use_container_width=True)

