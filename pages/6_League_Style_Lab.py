from __future__ import annotations

import html
import math

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.export_utils import render_export_png_button
from src.league_style import (
    CARD_GROUPS,
    INDEX_DEFINITIONS,
    METRIC_SPECS,
    aggregate_league_profiles,
    available_competitions,
    available_seasons,
    format_metric_value,
    league_display_columns,
    load_team_league_base,
    scatter_variable_options,
)
from src.ui import inject_css, pct_color

st.set_page_config(page_title="League Style Lab", page_icon="🌍", layout="wide")
inject_css()

st.markdown(
    """
<style>
.league-hero {
    border: 1px solid rgba(95,255,224,0.20);
    background: radial-gradient(circle at top left, rgba(95,255,224,0.12), transparent 35%),
                linear-gradient(115deg, rgba(16,22,43,0.90), rgba(33,21,60,0.70));
    border-radius: 26px;
    padding: 30px 32px;
    margin: 0.8rem 0 1.4rem 0;
    box-shadow: 0 18px 62px rgba(0,0,0,0.30), inset 0 0 26px rgba(95,255,224,0.04);
}
.league-kicker {
    color: #5FFFE0;
    font-size: 0.82rem;
    font-weight: 950;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.league-title {
    color: #F8FBFF;
    font-size: 3.2rem;
    line-height: 1.0;
    font-weight: 950;
    letter-spacing: -0.04em;
    text-shadow: 0 0 18px rgba(95,255,224,0.18);
    margin-bottom: 12px;
}
.league-subtitle {
    color: #B7CAE8;
    font-size: 1.02rem;
    line-height: 1.55;
    max-width: 1120px;
    font-weight: 650;
}
.league-pill-row {display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;}
.league-pill {
    display:inline-flex;align-items:center;min-height:28px;padding:5px 10px;border-radius:999px;
    background:rgba(95,255,224,0.10);color:#BFFFF4;border:1px solid rgba(95,255,224,0.20);
    font-size:0.74rem;font-weight:850;letter-spacing:0.03em;text-transform:uppercase;
}
.league-section-title {
    color:#F8FBFF;font-size:1.65rem;font-weight:950;margin:1.8rem 0 0.8rem 0;letter-spacing:-0.02em;
}
.league-ranking-panel {
    background:rgba(16,22,43,0.84);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:22px;
    padding:16px 16px 10px 16px;
    margin-bottom:18px;
    box-shadow:0 14px 44px rgba(0,0,0,0.23);
}
.league-ranking-header {
    display:flex;align-items:center;justify-content:space-between;gap:12px;
    padding-bottom:10px;margin-bottom:6px;border-bottom:1px solid rgba(255,255,255,0.08);
}
.league-ranking-title {
    color:#5FFFE0;font-size:1rem;font-weight:950;letter-spacing:0.08em;text-transform:uppercase;
}
.league-ranking-context {
    color:#8EA2C6;font-size:0.74rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;
}
.league-ranking-row {
    display:grid;grid-template-columns:38px minmax(0,1fr) 62px;
    align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.055);
}
.league-ranking-row:last-child {border-bottom:0;}
.league-rank {color:#B7CAE8;font-size:0.95rem;font-weight:950;text-align:center;}
.league-name {color:#F6F7FB;font-size:1rem;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.league-meta {color:#8EA2C6;font-size:0.78rem;font-weight:700;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.league-value {
    color:#F6F7FB;font-size:1rem;font-weight:950;text-align:right;font-variant-numeric:tabular-nums;
}
.league-card {
    border:1px solid rgba(95,255,224,0.24);
    background:linear-gradient(135deg, rgba(16,22,43,0.92), rgba(33,21,60,0.72));
    border-radius:26px;
    padding:24px 28px 22px 28px;
    box-shadow:0 18px 80px rgba(0,0,0,0.32), inset 0 0 26px rgba(95,255,224,0.04);
    margin:1rem 0 1.2rem 0;
}
.league-card-topline {display:flex;gap:10px;align-items:center;margin-bottom:10px;flex-wrap:wrap;}
.league-tag {
    display:inline-flex;align-items:center;padding:5px 10px;border-radius:4px;
    background:rgba(168,85,247,0.18);border:1px solid rgba(168,85,247,0.35);
    color:#DCC8FF;font-size:0.76rem;font-weight:800;letter-spacing:0.07em;text-transform:uppercase;
}
.league-tag-alt {background:rgba(95,255,224,0.14);border-color:rgba(95,255,224,0.30);color:#A8FFF0;}
.league-card-name {font-size:3rem;line-height:1;font-weight:950;color:#F8FBFF;margin-bottom:12px;}
.league-card-meta {color:#B7CAE8;font-size:1rem;margin-bottom:14px;}
.league-info-grid {display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;max-width:1000px;}
.league-info-box {
    background:rgba(18,25,50,0.82);border:1px solid rgba(95,255,224,0.16);border-radius:4px;
    padding:10px 14px;min-height:68px;display:flex;flex-direction:column;justify-content:center;
}
.league-info-label {font-size:0.72rem;color:#8EA2C6;letter-spacing:0.08em;margin-bottom:5px;text-transform:uppercase;}
.league-info-value {font-size:1.05rem;font-weight:900;color:#F6F7FB;}
.league-metric-panel {
    background:rgba(16,22,43,0.84);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:22px;
    padding:16px 16px 12px 16px;
    margin-bottom:16px;
    box-shadow:0 14px 44px rgba(0,0,0,0.23);
}
.league-metric-header {
    display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:11px;
}
.league-metric-title {
    color:#5FFFE0;font-size:1.05rem;font-weight:950;letter-spacing:0.08em;text-transform:uppercase;
}
.league-metric-row {
    display:grid;
    grid-template-columns:1.40fr 0.60fr 2fr 0.42fr;
    align-items:center;
    gap:10px;
    padding:7px 0;
    border-bottom:1px solid rgba(255,255,255,0.055);
}
.league-metric-row:last-child {border-bottom:0;}
.league-metric-label {font-size:0.86rem;color:#DDE8FF;}
.league-metric-value {font-size:0.88rem;color:#FFFFFF;font-weight:850;text-align:right;}
.league-bar-track {height:9px;border-radius:999px;background:rgba(255,255,255,0.10);overflow:hidden;}
.league-bar-fill {height:100%;border-radius:999px;box-shadow:0 0 14px currentColor;}
.league-metric-pct {font-size:0.78rem;font-weight:850;text-align:right;color:#F6F7FB;}
@media (max-width:1100px) {
    .league-info-grid {grid-template-columns:repeat(2,minmax(0,1fr));}
    .league-card-name {font-size:2.3rem;}
}
</style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="fm-title">LEAGUE STYLE LAB</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fm-subtitle">Overview di tutti i campionati · Team Dataset + xG/xA derivati dai giocatori · indici stilistici 0–100</div>',
    unsafe_allow_html=True,
)

export_left, export_right = st.columns([5.5, 1.2])
with export_left:
    st.write("")
with export_right:
    try:
        render_export_png_button("league_style_lab")
    except Exception:
        st.write("")

df = load_team_league_base()

with st.sidebar:
    st.markdown("### League Style filters")
    seasons = available_seasons(df)
    season = st.selectbox("Season", seasons, index=0)
    mode = st.selectbox("Metric value", ["Raw", "Possession-adjusted"], index=0)
    aggregation = st.selectbox("Aggregation", ["Median team profile", "Mean team profile"], index=0)

    st.markdown('<div class="control-label">Minimum teams per league</div>', unsafe_allow_html=True)
    if "league_min_teams" not in st.session_state:
        st.session_state["league_min_teams"] = 6
    mt1, mtv, mt2 = st.columns([0.9, 1.5, 0.9])
    with mt1:
        if st.button("−", key="league_min_teams_minus", use_container_width=True):
            st.session_state["league_min_teams"] = max(2, int(st.session_state["league_min_teams"]) - 1)
    with mt2:
        if st.button("+", key="league_min_teams_plus", use_container_width=True):
            st.session_state["league_min_teams"] = min(24, int(st.session_state["league_min_teams"]) + 1)
    min_teams = int(st.session_state["league_min_teams"])
    with mtv:
        st.markdown(f'<div class="minute-stepper-value">{min_teams}</div>', unsafe_allow_html=True)

    show_only = st.selectbox("Show leagues", ["All leagues", "Custom selection"], index=0)

league = aggregate_league_profiles(df, season=season, mode=mode, aggregation=aggregation, min_teams=min_teams)

if league.empty:
    st.warning("Nessun campionato disponibile con questi filtri.")
    st.stop()

if show_only == "Custom selection":
    options = league["Competition"].sort_values().tolist()
    selected = st.sidebar.multiselect("Leagues", options, default=options[: min(10, len(options))])
    if selected:
        league = league[league["Competition"].isin(selected)].copy()

if league.empty:
    st.warning("Nessun campionato selezionato.")
    st.stop()


def safe(value, fallback="—"):
    if pd.isna(value):
        return fallback
    return str(value)


def score_text(value):
    if pd.isna(value):
        return "—"
    return f"{float(value):.0f}"


def value_text(metric_name: str, value: float) -> str:
    return format_metric_value(metric_name, value)


def metric_pct(row: pd.Series, metric_name: str) -> float:
    return row.get(f"{metric_name} percentile", np.nan)


def render_bar(pct: float) -> str:
    try:
        v = max(0, min(100, float(pct)))
    except Exception:
        v = 0
    color = pct_color(v)
    return f'<div class="league-bar-track"><div class="league-bar-fill" style="width:{v:.0f}%;background:{color};color:{color};"></div></div>'


def render_ranking_panel(index_name: str, table: pd.DataFrame):
    top = table.sort_values(index_name, ascending=False).head(5)
    parts = []
    parts.append('<div class="league-ranking-panel">')
    parts.append('<div class="league-ranking-header">')
    parts.append(f'<div class="league-ranking-title">{html.escape(index_name)}</div>')
    parts.append('<div class="league-ranking-context">Top 5</div>')
    parts.append('</div>')
    for i, (_, row) in enumerate(top.iterrows(), start=1):
        parts.append('<div class="league-ranking-row">')
        parts.append(f'<div class="league-rank">{i}</div>')
        parts.append('<div>')
        parts.append(f'<div class="league-name">{html.escape(row["Flag"] + " " + row["Competition"])}</div>')
        parts.append(f'<div class="league-meta">{int(row["Teams"])} teams · {safe(row["Reliability"])}</div>')
        parts.append('</div>')
        parts.append(f'<div class="league-value" style="color:{pct_color(row[index_name])};">{score_text(row[index_name])}</div>')
        parts.append('</div>')
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)
    with st.expander(f"EXPAND · {index_name}"):
        show = table.sort_values(index_name, ascending=False).head(20)[["Flag", "League", "Nation", "Teams", "Reliability", index_name]].copy()
        show[index_name] = show[index_name].round(1)
        st.dataframe(show, use_container_width=True, hide_index=True)


# Hero
summary_indices = ["Directness", "Control", "Progression", "Chance Threat", "Pressing / Regain", "Physicality", "Chaos / Risk"]
pills = []
for idx in summary_indices[:6]:
    if idx in league.columns and league[idx].notna().any():
        r = league.sort_values(idx, ascending=False).iloc[0]
        pills.append(f'<span class="league-pill">{html.escape(idx)}: {html.escape(r["Flag"] + " " + r["Competition"])}</span>')

st.markdown(
    f"""
<div class="league-hero">
  <div class="league-kicker">League Style Lab</div>
  <div class="league-title">All Leagues Overview</div>
  <div class="league-subtitle">
    Questa pagina confronta tutti i campionati presenti nel dataset usando indici stilistici aggregati.
    I punteggi indicano intensità dello stile, non qualità assoluta del campionato.
  </div>
  <div class="league-pill-row">
    <span class="league-pill">{html.escape(str(season))}</span>
    <span class="league-pill">{html.escape(mode)}</span>
    <span class="league-pill">{html.escape(aggregation)}</span>
    <span class="league-pill">Leagues n = {len(league)}</span>
    {''.join(pills)}
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

# Rankings
st.markdown('<div class="league-section-title">Ranking campionati per stile</div>', unsafe_allow_html=True)
rank_cols = st.columns(3)
for i, idx in enumerate(summary_indices):
    if idx in league.columns:
        with rank_cols[i % 3]:
            render_ranking_panel(idx, league)

# Complete table
st.markdown('<div class="league-section-title">All Leagues Table</div>', unsafe_allow_html=True)
table_cols = [c for c in league_display_columns() if c in league.columns]
table = league[table_cols].copy()
for c in table.columns:
    if c not in ["Flag", "Competition", "Reliability"]:
        if pd.api.types.is_numeric_dtype(table[c]):
            table[c] = table[c].round(1)
st.dataframe(table.sort_values("Competition"), use_container_width=True, hide_index=True)

# League card
st.markdown('<div class="league-section-title">League Card</div>', unsafe_allow_html=True)
selected_competition = st.selectbox("Select league card", league["Competition"].sort_values().tolist())
league_row = league[league["Competition"].eq(selected_competition)].iloc[0]

poss = value_text("Ball possession %", league_row.get("Ball possession %"))
xg = value_text("xG/team", league_row.get("xG/team"))
shots = value_text("Shots", league_row.get("Shots"))
teams = int(league_row.get("Teams", 0))

st.markdown(
    f"""
<div class="league-card">
  <div class="league-card-topline">
    <span class="league-tag">{html.escape(league_row["Flag"])} {html.escape(safe(league_row["Nation"]))}</span>
    <span class="league-tag league-tag-alt">{html.escape(str(season))}</span>
  </div>
  <div class="league-card-name">{html.escape(safe(league_row["League"]))}</div>
  <div class="league-card-meta">{html.escape(safe(league_row["Competition"]))} · {html.escape(mode)} · {html.escape(aggregation)}</div>
  <div class="league-info-grid">
    <div class="league-info-box"><span class="league-info-label">Teams</span><span class="league-info-value">{teams}</span></div>
    <div class="league-info-box"><span class="league-info-label">Reliability</span><span class="league-info-value">{html.escape(safe(league_row["Reliability"]))}</span></div>
    <div class="league-info-box"><span class="league-info-label">Possession</span><span class="league-info-value">{poss}</span></div>
    <div class="league-info-box"><span class="league-info-label">xG/team</span><span class="league-info-value">{xg}</span></div>
    <div class="league-info-box"><span class="league-info-label">Shots/team</span><span class="league-info-value">{shots}</span></div>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

card_cols = st.columns(2)
for i, (family, metrics) in enumerate(CARD_GROUPS.items()):
    parts = []
    parts.append('<div class="league-metric-panel">')
    parts.append('<div class="league-metric-header">')
    parts.append(f'<div class="league-metric-title">{html.escape(family)}</div>')
    parts.append('</div>')
    for metric_name in metrics:
        if metric_name not in league_row.index:
            continue
        val = league_row.get(metric_name)
        pct = metric_pct(league_row, metric_name)
        color = pct_color(pct) if not pd.isna(pct) else "#8EA2C6"
        parts.append('<div class="league-metric-row">')
        parts.append(f'<div class="league-metric-label">{html.escape(metric_name)}</div>')
        parts.append(f'<div class="league-metric-value">{html.escape(value_text(metric_name, val))}</div>')
        parts.append(render_bar(pct))
        parts.append(f'<div class="league-metric-pct" style="color:{color};">{score_text(pct)}</div>')
        parts.append('</div>')
    parts.append('</div>')
    with card_cols[i % 2]:
        st.markdown("".join(parts), unsafe_allow_html=True)

# Scatter lab
st.markdown('<div class="league-section-title">Scatter Lab</div>', unsafe_allow_html=True)
variables = [v for v in scatter_variable_options() if v in league.columns]
s1, s2, s3 = st.columns([1, 1, 1])
with s1:
    x_var = st.selectbox("X variable", variables, index=variables.index("Control") if "Control" in variables else 0)
with s2:
    y_var = st.selectbox("Y variable", variables, index=variables.index("Directness") if "Directness" in variables else min(1, len(variables)-1))
with s3:
    highlight = st.selectbox("Highlight league", ["None", *league["Competition"].sort_values().tolist()], index=0)

plot_df = league.copy()
plot_df["Hover"] = (
    plot_df["Flag"].astype(str)
    + " "
    + plot_df["Competition"].astype(str)
    + "<br>Teams: "
    + plot_df["Teams"].astype(int).astype(str)
    + "<br>Reliability: "
    + plot_df["Reliability"].astype(str)
)
plot_df["Highlight"] = np.where(plot_df["Competition"].eq(highlight), "Selected", "Other") if highlight != "None" else "League"

fig = px.scatter(
    plot_df,
    x=x_var,
    y=y_var,
    size="Teams",
    color="Highlight" if highlight != "None" else "Nation",
    hover_name="Competition",
    hover_data={
        "Flag": True,
        "Nation": True,
        "Teams": True,
        "Reliability": True,
        x_var: ":.2f",
        y_var: ":.2f",
    },
    template="plotly_dark",
    height=620,
)
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(10,16,36,0.45)",
    font=dict(color="#F6F7FB"),
    legend=dict(font=dict(color="#DDE8FF")),
    margin=dict(l=30, r=30, t=40, b=40),
)
fig.update_traces(marker=dict(line=dict(width=1, color="rgba(255,255,255,0.55)")), selector=dict(mode="markers"))
st.plotly_chart(fig, use_container_width=True)

with st.expander("Note metodologiche"):
    st.markdown(
        """
        **Unità di analisi:** campionato × nazione × stagione.  
        **Fonte principale:** Team Dataset aggregato per campionato.  
        **Fonte integrativa:** Player Dataset per stimare xG/team e xA/team tramite media pesata sui minuti.  
        **Bandiere:** per leggibilità sono mostrate in tooltip/card/tabelle; i marker restano pallini per evitare sovrapposizioni e perdita di leggibilità.
        """
    )
