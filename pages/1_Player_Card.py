from __future__ import annotations

import math

import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import available_leagues, available_seasons, load_players_enriched
from src.metric_catalog import BIG_FIVE_LEAGUES, CARD_GROUPS, RADAR_AXES, ROLE_BUCKETS
from src.scoring import (
    all_group_scores,
    build_reference_df,
    format_metric_value,
    metric_value_and_percentile,
    radar_axis_score,
    role_overall,
)
from src.ui import inject_css, metric_row_html, pct_color, radar_figure

st.set_page_config(page_title="Player Card", page_icon="⚽", layout="wide")
inject_css()

st.markdown('<div class="fm-title">PLAYER CARD</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fm-subtitle">Valori grezzi o possession-adjusted · barre e radar in percentile · overall pesato per ruolo</div>',
    unsafe_allow_html=True,
)

df = load_players_enriched()

with st.sidebar:
    st.markdown("### Filters")
    seasons = available_seasons(df)
    season = st.selectbox("Season", seasons, index=0)

    season_df = df[df["Season"].astype(str).eq(str(season))].copy()
    player_league_filter = st.selectbox("Player league filter", ["All leagues", *available_leagues(season_df)])
    pool = season_df.copy()
    if player_league_filter != "All leagues":
        pool = pool[pool["League"].astype(str).eq(player_league_filter)]

    teams = ["All teams", *sorted(pool["Team"].dropna().astype(str).unique().tolist())]
    selected_team = st.selectbox("Team filter", teams)
    if selected_team != "All teams":
        pool = pool[pool["Team"].astype(str).eq(selected_team)]

    if pool.empty:
        st.warning("Nessun giocatore per questi filtri.")
        st.stop()

    player_options = (
        pool.assign(_label=pool["Player"].astype(str) + " · " + pool["Team"].astype(str) + " · " + pool["Position"].astype(str))
        .sort_values(["Player", "Team"])
    )
    selected_label = st.selectbox("Player", player_options["_label"].tolist())
    player_idx = player_options.loc[player_options["_label"].eq(selected_label)].index[0]
    player = df.loc[player_idx]

    st.markdown("---")
    st.markdown("### Percentile context")
    default_role = player.get("Role bucket", "AM/W")
    role_keys = list(ROLE_BUCKETS.keys())
    default_role_index = role_keys.index(default_role) if default_role in role_keys else 0
    compare_role = st.radio("Compare as role", role_keys, index=default_role_index, horizontal=True)

    reference_scope = st.radio(
        "Reference scope",
        ["Player league", "Big Five", "All leagues", "Custom leagues"],
        index=0,
    )

    custom_leagues: list[str] = []
    if reference_scope == "Custom leagues":
        custom_leagues = st.multiselect(
            "Custom leagues",
            available_leagues(season_df),
            default=[l for l in BIG_FIVE_LEAGUES if l in available_leagues(season_df)],
        )

    min_minutes = st.slider("Minimum minutes in reference group", 0, 2500, 900, step=100)
    mode = st.radio("Metric value", ["Raw", "Possession-adjusted"], index=0)

player_league = str(player.get("League")) if pd.notna(player.get("League")) else None
reference_df = build_reference_df(
    df,
    season=str(season),
    role_bucket=compare_role,
    reference_scope=reference_scope,
    player_league=player_league,
    custom_leagues=custom_leagues,
    min_minutes=min_minutes,
)

scores = all_group_scores(player, reference_df, mode)
overall = role_overall(scores, compare_role)

# Header
left, right = st.columns([4.5, 1.15], vertical_alignment="center")
with left:
    meta = [
        f"{player.get('Team', '—')}",
        f"{player.get('League', '—')}",
        f"{player.get('Season', '—')}",
        f"Pos: {player.get('Position', '—')}",
        f"Compare as: {compare_role}",
        f"Min ref minutes: {min_minutes}",
    ]
    st.markdown(
        f"""
        <div class="hero-card">
          <div class="hero-name">{player.get('Player', '—')}</div>
          <div class="hero-meta">{' · '.join(meta)}</div>
          <div style="margin-top:10px;">
            <span class="pill">{mode}</span>
            <span class="pill">Reference: {reference_scope}</span>
            <span class="pill">Reference n = {len(reference_df)}</span>
            <span class="pill">Team possession = {float(player.get('Ball possession, %'))*100:.1f}%</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with right:
    ov_text = "—" if math.isnan(overall) else f"{overall:.0f}"
    st.markdown(
        f"""
        <div class="overall-badge">
          <div class="overall-inner">
            <div class="overall-value">{ov_text}</div>
            <div class="overall-label">OVERALL</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if len(reference_df) < 20:
    st.warning(
        f"Reference group piccolo: {len(reference_df)} giocatori. I percentili potrebbero essere instabili. "
        "Abbassa i minuti minimi o amplia il perimetro campionati."
    )

# Group score strip
score_cols = st.columns(5)
for i, (group_name, score) in enumerate(scores.items()):
    if group_name not in CARD_GROUPS:
        continue
    with score_cols[i % 5]:
        group_color = CARD_GROUPS[group_name].get("color", "#5FFFE0")
        score_txt = "—" if math.isnan(score) else f"{score:.0f}"
        st.markdown(
            f"""
            <div class="metric-panel" style="padding:12px 14px; min-height:92px; border-color:{group_color}44;">
              <div class="small-note">{group_name}</div>
              <div style="font-size:1.8rem;font-weight:900;color:{pct_color(score)};">{score_txt}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Metric families
st.markdown("### Metric families")
cols = st.columns(2)
for idx, (group_name, group) in enumerate(CARD_GROUPS.items()):
    html = f"""
    <div class="metric-panel">
      <div class="metric-group-title" style="color:{group.get('color', '#5FFFE0')};">
        <span>{group.get('icon', '•')}</span><span>{group_name}</span>
      </div>
    """
    for metric in group.get("metrics", []):
        value, pct = metric_value_and_percentile(player, df, reference_df, metric, mode)
        html += metric_row_html(
            metric.get("label", metric.get("column", "Metric")),
            format_metric_value(value, metric.get("fmt", "0.00")),
            pct,
        )
    html += "</div>"
    with cols[idx % 2]:
        st.markdown(html, unsafe_allow_html=True)

# Radar section
st.markdown("### Role radar")
axes = RADAR_AXES.get(compare_role, [])
if axes:
    labels = [axis["axis"] for axis in axes]
    style_values = [radar_axis_score(player, reference_df, axis.get("style", []), mode) for axis in axes]
    perf_values = [radar_axis_score(player, reference_df, axis.get("performance", []), mode) for axis in axes]

    r1, r2 = st.columns(2)
    with r1:
        st.plotly_chart(radar_figure(labels, style_values, "Playing Style · volume percentiles"), use_container_width=True)
    with r2:
        st.plotly_chart(radar_figure(labels, perf_values, "Performance · execution percentiles"), use_container_width=True)
else:
    st.info("Radar non definito per questo ruolo.")

with st.expander("Reference group details"):
    cols_to_show = ["Player", "Team", "League", "Position", "Minutes played", "Role bucket"]
    st.dataframe(reference_df[cols_to_show].sort_values("Minutes played", ascending=False), use_container_width=True)
