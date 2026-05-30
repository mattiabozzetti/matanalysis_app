from __future__ import annotations

import html
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_players_enriched
from src.gk_data_loader import load_gk_enriched

from src.export_utils import render_export_png_button
from src.team_scouting import (
    BASE_METRICS,
    CARD_GROUPS,
    STYLE_INDEX_COMPONENTS,
    available_competitions,
    available_seasons,
    build_team_profiles,
    format_metric_value,
    load_team_scouting_base,
    scatter_variable_options,
    table_columns,
)
from src.ui import inject_css, pct_color

st.set_page_config(page_title="Team Scouting", page_icon="🧭", layout="wide")
inject_css()

st.markdown(
    """
<style>
.team-hero {
    border: 1px solid rgba(95,255,224,0.20);
    background: radial-gradient(circle at top left, rgba(95,255,224,0.12), transparent 35%),
                linear-gradient(115deg, rgba(16,22,43,0.90), rgba(33,21,60,0.70));
    border-radius: 26px;
    padding: 30px 32px;
    margin: 0.8rem 0 1.4rem 0;
    box-shadow: 0 18px 62px rgba(0,0,0,0.30), inset 0 0 26px rgba(95,255,224,0.04);
}
.team-kicker {
    color:#5FFFE0;font-size:0.82rem;font-weight:950;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:10px;
}
.team-title {
    color:#F8FBFF;font-size:3.2rem;line-height:1;font-weight:950;letter-spacing:-0.04em;
    text-shadow:0 0 18px rgba(95,255,224,0.18);margin-bottom:12px;
}
.team-subtitle {
    color:#B7CAE8;font-size:1.02rem;line-height:1.55;max-width:1120px;font-weight:650;
}
.team-pill-row {display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;}
.team-pill {
    display:inline-flex;align-items:center;min-height:28px;padding:5px 10px;border-radius:999px;
    background:rgba(95,255,224,0.10);color:#BFFFF4;border:1px solid rgba(95,255,224,0.20);
    font-size:0.74rem;font-weight:850;letter-spacing:0.03em;text-transform:uppercase;
}
.team-section-title {
    color:#F8FBFF;font-size:1.65rem;font-weight:950;margin:1.8rem 0 0.8rem 0;letter-spacing:-0.02em;
}
.team-ranking-panel {
    background:rgba(16,22,43,0.84);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:22px;
    padding:16px 16px 10px 16px;
    margin-bottom:18px;
    box-shadow:0 14px 44px rgba(0,0,0,0.23);
}
.team-ranking-header {
    display:flex;align-items:center;justify-content:space-between;gap:12px;
    padding-bottom:10px;margin-bottom:6px;border-bottom:1px solid rgba(255,255,255,0.08);
}
.team-ranking-title {color:#5FFFE0;font-size:1rem;font-weight:950;letter-spacing:0.08em;text-transform:uppercase;}
.team-ranking-context {color:#8EA2C6;font-size:0.74rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;}
.team-ranking-row {
    display:grid;grid-template-columns:38px minmax(0,1fr) 62px;
    align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.055);
}
.team-ranking-row:last-child {border-bottom:0;}
.team-rank {color:#B7CAE8;font-size:0.95rem;font-weight:950;text-align:center;}
.team-name {color:#F6F7FB;font-size:1rem;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.team-meta {color:#8EA2C6;font-size:0.78rem;font-weight:700;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.team-value {color:#F6F7FB;font-size:1rem;font-weight:950;text-align:right;font-variant-numeric:tabular-nums;}
.team-card {
    border:1px solid rgba(95,255,224,0.24);
    background:linear-gradient(135deg, rgba(16,22,43,0.92), rgba(33,21,60,0.72));
    border-radius:26px;
    padding:24px 28px 22px 28px;
    box-shadow:0 18px 80px rgba(0,0,0,0.32), inset 0 0 26px rgba(95,255,224,0.04);
    margin:1rem 0 1.2rem 0;
}
.team-card-topline {display:flex;gap:10px;align-items:center;margin-bottom:10px;flex-wrap:wrap;}
.team-tag {
    display:inline-flex;align-items:center;padding:5px 10px;border-radius:4px;
    background:rgba(168,85,247,0.18);border:1px solid rgba(168,85,247,0.35);
    color:#DCC8FF;font-size:0.76rem;font-weight:800;letter-spacing:0.07em;text-transform:uppercase;
}
.team-tag-alt {background:rgba(95,255,224,0.14);border-color:rgba(95,255,224,0.30);color:#A8FFF0;}
.team-card-name {font-size:3rem;line-height:1;font-weight:950;color:#F8FBFF;margin-bottom:12px;}
.team-card-meta {color:#B7CAE8;font-size:1rem;margin-bottom:14px;}
.team-info-grid {display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;max-width:1260px;}
.team-info-box {
    background:rgba(18,25,50,0.82);border:1px solid rgba(95,255,224,0.16);border-radius:4px;
    padding:10px 14px;min-height:68px;display:flex;flex-direction:column;justify-content:center;
}
.team-info-label {font-size:0.72rem;color:#8EA2C6;letter-spacing:0.08em;margin-bottom:5px;text-transform:uppercase;}
.team-info-value {font-size:1.05rem;font-weight:900;color:#F6F7FB;}
.team-metric-panel {
    background:rgba(16,22,43,0.84);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:22px;
    padding:16px 16px 12px 16px;
    margin-bottom:16px;
    box-shadow:0 14px 44px rgba(0,0,0,0.23);
}
.team-metric-header {
    display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:11px;
}
.team-metric-title {color:#5FFFE0;font-size:1.05rem;font-weight:950;letter-spacing:0.08em;text-transform:uppercase;}
.team-metric-row {
    display:grid;grid-template-columns:1.32fr 0.58fr 1.85fr 0.58fr;
    align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.055);
}
.team-metric-row:last-child {border-bottom:0;}
.team-metric-label {font-size:0.86rem;color:#DDE8FF;}
.team-metric-value {font-size:0.88rem;color:#FFFFFF;font-weight:850;text-align:right;}
.team-bar-track {height:9px;border-radius:999px;background:rgba(255,255,255,0.10);overflow:hidden;}
.team-bar-fill {height:100%;border-radius:999px;box-shadow:0 0 14px currentColor;}
.team-metric-pct {font-size:0.78rem;font-weight:850;text-align:right;color:#F6F7FB;}
.team-table-wrap {
    width:100%;overflow-x:auto;border:1px solid rgba(95,255,224,0.18);border-radius:18px;
    background:rgba(10,16,36,0.78);box-shadow:0 14px 44px rgba(0,0,0,0.22);margin-bottom:1.2rem;
}
.team-table {width:100%;border-collapse:collapse;min-width:1200px;color:#F6F7FB;font-size:0.86rem;}
.team-table thead th {
    background:#10162B;color:#AFC3E8;text-align:left;padding:11px 10px;
    font-size:0.74rem;font-weight:950;letter-spacing:0.06em;text-transform:uppercase;
    border-bottom:1px solid rgba(95,255,224,0.18);
}
.team-table tbody td {padding:10px 10px;border-bottom:1px solid rgba(255,255,255,0.055);background:rgba(16,22,43,0.72);}
.team-table tbody tr:nth-child(even) td {background:rgba(12,18,38,0.78);}
.team-table tbody tr:hover td {background:rgba(95,255,224,0.075);}
.team-table .num {text-align:right;font-variant-numeric:tabular-nums;font-weight:850;}
.team-table .team-cell {font-weight:950;color:#F6F7FB;white-space:nowrap;}
.team-table .score-pill {
    display:inline-flex;min-width:38px;height:24px;border-radius:999px;align-items:center;justify-content:center;padding:0 8px;
    background:rgba(95,255,224,0.08);border:1px solid rgba(95,255,224,0.16);font-weight:950;
}

.team-style-index-score {
    display:inline-flex;
    align-items:center;
    justify-content:center;
    min-width:44px;
    height:30px;
    border-radius:999px;
    padding:0 10px;
    background:rgba(95,255,224,0.10);
    border:1px solid rgba(95,255,224,0.28);
    color:#5FFFE0;
    font-weight:950;
    font-size:0.88rem;
}
.team-style-index-note {
    color:#8EA2C6;
    font-size:0.78rem;
    font-weight:750;
    margin-top:-4px;
    margin-bottom:10px;
}


.team-metric-scorebox {
    display:flex;
    flex-direction:column;
    align-items:flex-end;
    line-height:1.05;
}
.team-metric-rank {
    color:#8EA2C6;
    font-size:0.62rem;
    font-weight:850;
    margin-top:3px;
    white-space:nowrap;
}
.cluster-composition-wrap {
    border:1px solid rgba(95,255,224,0.18);
    border-radius:22px;
    background:rgba(10,16,36,0.72);
    box-shadow:0 14px 44px rgba(0,0,0,0.22);
    overflow:hidden;
    margin-bottom:1.4rem;
}
.cluster-composition-grid {
    display:grid;
    grid-template-columns: 1.15fr 0.55fr 0.75fr 1fr 1fr 0.5fr;
    gap:0;
}
.cluster-composition-head,
.cluster-composition-row {
    display:contents;
}
.cluster-composition-head > div {
    background:#10162B;
    color:#AFC3E8;
    padding:11px 12px;
    font-size:0.72rem;
    font-weight:950;
    letter-spacing:0.06em;
    text-transform:uppercase;
    border-bottom:1px solid rgba(95,255,224,0.18);
}
.cluster-composition-row > div {
    color:#DDE8FF;
    background:rgba(16,22,43,0.70);
    padding:10px 12px;
    border-bottom:1px solid rgba(255,255,255,0.055);
    font-size:0.82rem;
    font-weight:750;
}
.cluster-composition-row:nth-child(even) > div {background:rgba(12,18,38,0.78);}
.cluster-composition-player {color:#F6F7FB !important;font-weight:950 !important;}
.cluster-pill {
    display:inline-flex;
    align-items:center;
    justify-content:center;
    padding:4px 9px;
    min-height:24px;
    border-radius:999px;
    border:1px solid rgba(95,255,224,0.25);
    background:rgba(95,255,224,0.08);
    color:#5FFFE0;
    font-weight:950;
    font-size:0.74rem;
}

@media (max-width:1100px) {
    .team-info-grid {grid-template-columns:repeat(2,minmax(0,1fr));}
    .team-card-name {font-size:2.3rem;}
}
</style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="fm-title">TEAM SCOUTING LAB</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fm-subtitle">Ranking squadre dentro ogni campionato · stile · performance attesa · performance effettiva</div>',
    unsafe_allow_html=True,
)

export_left, export_right = st.columns([5.5, 1.2])
with export_left:
    st.write("")
with export_right:
    try:
        render_export_png_button("team_scouting_lab")
    except Exception:
        st.write("")

df = load_team_scouting_base()

with st.sidebar:
    st.markdown("### Team Scouting filters")
    seasons = available_seasons(df)
    season = st.selectbox("Season", seasons, index=0)

    competitions = available_competitions(df, season)
    competition = st.selectbox("League", competitions, index=0)

    mode = st.selectbox("Metric value", ["Raw", "Possession-adjusted"], index=0)

team_df = build_team_profiles(df, season=season, competition=competition, mode=mode)

if team_df.empty:
    st.warning("Nessuna squadra disponibile con questi filtri.")
    st.stop()

league_flag = str(team_df["Flag"].iloc[0])
league_name = str(team_df["League"].iloc[0])
nation = str(team_df["Nation"].iloc[0])
n_teams = len(team_df)

def safe(value, fallback="—"):
    if pd.isna(value):
        return fallback
    return str(value)

def score_text(value):
    if pd.isna(value):
        return "—"
    return f"{float(value):.0f}"


DISPLAY_LABELS = {
    "Goals": "Goals / match",
    "xG/team": "xG / match",
    "xA/team": "xA / match",
    "xG+xA/team": "xG+xA / match",
    "Goals - xG": "G - xG / match",
    "Goal overperformance %": "G - xG / match %",
    "Matches": "Matches",
    "Goals total": "GF total",
    "Goals against total": "GA total",
    "Goal difference total": "GD total",
    "xG total": "xG total",
    "xGA total": "xGA total",
    "xGD total": "xGD total",
    "xA total": "xA total",
    "Goals - xG total": "G - xG total",
    "Goal overperformance total %": "G - xG total %",
}


def display_label(name: str) -> str:
    return DISPLAY_LABELS.get(str(name), str(name))


def render_bar(pct: float) -> str:
    try:
        v = max(0, min(100, float(pct)))
    except Exception:
        v = 0
    color = pct_color(v)
    return f'<div class="team-bar-track"><div class="team-bar-fill" style="width:{v:.0f}%;background:{color};color:{color};"></div></div>'

def dark_table(table: pd.DataFrame, score_cols: set[str]) -> str:
    parts = ['<div class="team-table-wrap"><table class="team-table">']
    parts.append("<thead><tr>")
    for col in table.columns:
        parts.append(f"<th>{html.escape(display_label(str(col)))}</th>")
    parts.append("</tr></thead><tbody>")
    for _, row in table.iterrows():
        parts.append("<tr>")
        for col in table.columns:
            val = row[col]
            if pd.isna(val):
                txt = "—"
            elif isinstance(val, (int, np.integer)):
                txt = f"{int(val)}"
            elif isinstance(val, (float, np.floating)):
                if col in {"Matches", "Goals total", "Goals against total", "Goal difference total"}:
                    txt = f"{float(val):.0f}"
                else:
                    txt = f"{float(val):.1f}"
            else:
                txt = str(val)

            if col == "Team":
                cell = f'<td class="team-cell">{html.escape(txt)}</td>'
            elif col in score_cols:
                try:
                    color = pct_color(float(val))
                except Exception:
                    color = "#8EA2C6"
                cell = f'<td class="num"><span class="score-pill" style="color:{color};">{html.escape(txt)}</span></td>'
            elif isinstance(val, (int, float, np.integer, np.floating)) and not pd.isna(val):
                cell = f'<td class="num">{html.escape(txt)}</td>'
            else:
                cell = f'<td>{html.escape(txt)}</td>'
            parts.append(cell)
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)

def render_ranking_panel(metric: str, table: pd.DataFrame):
    top = table.sort_values(metric, ascending=False).head(5)
    parts = ['<div class="team-ranking-panel">']
    parts.append('<div class="team-ranking-header">')
    parts.append(f'<div class="team-ranking-title">{html.escape(display_label(metric))}</div>')
    parts.append('<div class="team-ranking-context">Top 5</div>')
    parts.append('</div>')
    for i, (_, row) in enumerate(top.iterrows(), start=1):
        value = row.get(metric)
        color = pct_color(value) if not pd.isna(value) else "#8EA2C6"
        parts.append('<div class="team-ranking-row">')
        parts.append(f'<div class="team-rank">{i}</div>')
        parts.append('<div>')
        parts.append(f'<div class="team-name">{html.escape(safe(row.get("Team")))}</div>')
        parts.append(f'<div class="team-meta">GF {format_metric_value("Goals total", row.get("Goals total"))} · GA {format_metric_value("Goals against total", row.get("Goals against total"))} · GD {format_metric_value("Goal difference total", row.get("Goal difference total"))}</div>')
        parts.append('</div>')
        parts.append(f'<div class="team-value" style="color:{color};">{score_text(value)}</div>')
        parts.append('</div>')
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)

    with st.expander(f"EXPAND · {display_label(metric)}"):
        cols = ["Team", "Goals", "xG/team", "Goals - xG", "Matches", "Goals total", "Goals against total", "Goal difference total", "xG total", "xGA total", "xGD total", "Goals - xG total", "Expected Performance", "Effective Performance", "Performance Gap", metric]
        cols = list(dict.fromkeys([c for c in cols if c in table.columns]))
        show = table.sort_values(metric, ascending=False).head(20).loc[:, cols].copy()
        integer_cols = {"Matches", "Goals total", "Goals against total", "Goal difference total"}
        for c in list(show.columns):
            if c != "Team":
                num = pd.to_numeric(show[c], errors="coerce")
                show[c] = num.round(0) if c in integer_cols else num.round(1)
        st.markdown(dark_table(show, {metric, "Expected Performance", "Effective Performance", "Performance Gap"}), unsafe_allow_html=True)


def component_percentile(table: pd.DataFrame, metric: str, higher_is_better: bool, selected_index: int) -> float:
    if metric not in table.columns:
        return float("nan")
    values = pd.to_numeric(table[metric], errors="coerce")
    pct = values.rank(pct=True, method="average") * 100
    if not higher_is_better:
        pct = 100 - pct
    try:
        return float(pct.loc[selected_index])
    except Exception:
        return float("nan")


def metric_higher_is_better(metric: str) -> bool:
    spec = BASE_METRICS.get(metric, {})
    return bool(spec.get("higher_is_better", True))


def metric_rank_label(table: pd.DataFrame, metric: str, selected_index: int, *, higher_is_better: bool | None = None) -> str:
    if metric not in table.columns:
        return "—"
    values = pd.to_numeric(table[metric], errors="coerce")
    valid = values.dropna()
    if valid.empty or selected_index not in values.index or pd.isna(values.loc[selected_index]):
        return "—"
    if higher_is_better is None:
        higher_is_better = metric_higher_is_better(metric)
    rank = values.rank(ascending=not higher_is_better, method="min").loc[selected_index]
    return f"{int(rank)}/{int(valid.shape[0])}"


def metric_scorebox(pct: float, rank_label: str) -> str:
    color = pct_color(pct) if not pd.isna(pct) else "#8EA2C6"
    return (
        '<div class="team-metric-scorebox">'
        f'<div class="team-metric-pct" style="color:{color};">{score_text(pct)}</div>'
        f'<div class="team-metric-rank">{html.escape(rank_label)}</div>'
        '</div>'
    )


def render_style_index_panel(index_name: str, components: list[dict], selected_index: int) -> str:
    index_score = team_row.get(index_name, float("nan"))
    color = pct_color(index_score) if not pd.isna(index_score) else "#8EA2C6"

    parts = ['<div class="team-metric-panel">']
    parts.append('<div class="team-metric-header">')
    parts.append(f'<div class="team-metric-title">{html.escape(index_name)}</div>')
    parts.append(f'<div class="team-style-index-score" style="color:{color};border-color:{color}80;">{score_text(index_score)}</div>')
    parts.append('</div>')
    parts.append('<div class="team-style-index-note">Composite score built from the component metrics below.</div>')

    for component in components:
        metric = component.get("metric")
        if metric not in team_row.index:
            continue
        higher = bool(component.get("higher_is_better", True))
        val = team_row.get(metric)
        pct = component_percentile(team_df, metric, higher, selected_index)
        rank_label = metric_rank_label(team_df, metric, selected_index, higher_is_better=higher)
        parts.append('<div class="team-metric-row">')
        parts.append(f'<div class="team-metric-label">{html.escape(display_label(metric))}</div>')
        parts.append(f'<div class="team-metric-value">{html.escape(format_metric_value(metric, val))}</div>')
        parts.append(render_bar(pct))
        parts.append(metric_scorebox(pct, rank_label))
        parts.append('</div>')

    parts.append('</div>')
    return "".join(parts)


# Hero
leaders = []
for metric in ["Expected Performance", "Effective Performance", "Performance Gap", "Directness", "Control", "Pressing / Regain"]:
    if metric in team_df.columns and team_df[metric].notna().any():
        row = team_df.sort_values(metric, ascending=False).iloc[0]
        leaders.append(f'<span class="team-pill">{html.escape(metric)}: {html.escape(row["Team"])}</span>')

st.markdown(
    f"""
<div class="team-hero">
  <div class="team-kicker">Team Scouting Lab</div>
  <div class="team-title">{html.escape(league_flag)} {html.escape(league_name)}</div>
  <div class="team-subtitle">
    Ranking delle squadre dentro il campionato selezionato: stile di gioco, performance attesa e performance effettiva.
    I punteggi sono percentili interni al campionato, quindi confrontano solo le squadre di questa lega/stagione.
  </div>
  <div class="team-pill-row">
    <span class="team-pill">{html.escape(str(season))}</span>
    <span class="team-pill">{html.escape(nation)}</span>
    <span class="team-pill">{n_teams} teams</span>
    <span class="team-pill">{html.escape(mode)}</span>
    {''.join(leaders)}
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

# Rankings
st.markdown('<div class="team-section-title">Ranking squadre</div>', unsafe_allow_html=True)
rank_metrics = [
    "Expected Performance",
    "Effective Performance",
    "Performance Gap",
    "Directness",
    "Control",
    "Progression",
    "Pressing / Regain",
    "Physicality",
    "Chaos / Risk",
]
rank_cols = st.columns(3)
for i, metric in enumerate(rank_metrics):
    if metric in team_df.columns:
        with rank_cols[i % 3]:
            render_ranking_panel(metric, team_df)

# Team Card
st.markdown('<div class="team-section-title">Team Card</div>', unsafe_allow_html=True)
selected_team = st.selectbox("Select team", team_df["Team"].sort_values().tolist())
team_row = team_df[team_df["Team"].eq(selected_team)].iloc[0]

st.markdown(
    f"""
<div class="team-card">
  <div class="team-card-topline">
    <span class="team-tag">{html.escape(league_flag)} {html.escape(league_name)}</span>
    <span class="team-tag team-tag-alt">{html.escape(str(season))}</span>
  </div>
  <div class="team-card-name">{html.escape(safe(team_row.get("Team")))}</div>
  <div class="team-card-meta">{html.escape(competition)} · {html.escape(mode)} · percentili interni al campionato</div>
  <div class="team-info-grid">
    <div class="team-info-box"><span class="team-info-label">Expected</span><span class="team-info-value">{score_text(team_row.get("Expected Performance"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">Effective</span><span class="team-info-value">{score_text(team_row.get("Effective Performance"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">Performance gap</span><span class="team-info-value">{score_text(team_row.get("Performance Gap"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">Matches</span><span class="team-info-value">{format_metric_value("Matches", team_row.get("Matches"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">GF total</span><span class="team-info-value">{format_metric_value("Goals total", team_row.get("Goals total"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">GA total</span><span class="team-info-value">{format_metric_value("Goals against total", team_row.get("Goals against total"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">GD total</span><span class="team-info-value">{format_metric_value("Goal difference total", team_row.get("Goal difference total"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">G - xG total</span><span class="team-info-value">{format_metric_value("Goals - xG total", team_row.get("Goals - xG total"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">xG total</span><span class="team-info-value">{format_metric_value("xG total", team_row.get("xG total"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">xGA total</span><span class="team-info-value">{format_metric_value("xGA total", team_row.get("xGA total"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">xGD total</span><span class="team-info-value">{format_metric_value("xGD total", team_row.get("xGD total"))}</span></div>
    <div class="team-info-box"><span class="team-info-label">Goals / match</span><span class="team-info-value">{format_metric_value("Goals", team_row.get("Goals"))}</span></div>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

selected_index = team_df.index[team_df["Team"].eq(selected_team)][0]

st.markdown('<div class="team-section-title">Style Profile components</div>', unsafe_allow_html=True)
style_cols = st.columns(2)
for i, (index_name, components) in enumerate(STYLE_INDEX_COMPONENTS.items()):
    with style_cols[i % 2]:
        st.markdown(render_style_index_panel(index_name, components, selected_index), unsafe_allow_html=True)

st.markdown('<div class="team-section-title">Performance and operational metrics</div>', unsafe_allow_html=True)
card_cols = st.columns(2)
display_groups = {k: v for k, v in CARD_GROUPS.items() if k != "Style Profile"}
for i, (family, metrics) in enumerate(display_groups.items()):
    parts = ['<div class="team-metric-panel">']
    parts.append('<div class="team-metric-header">')
    parts.append(f'<div class="team-metric-title">{html.escape(family)}</div>')
    parts.append('</div>')
    for metric in metrics:
        if metric not in team_row.index:
            continue
        val = team_row.get(metric)
        pct = team_row.get(f"{metric} percentile", val if metric in STYLE_INDEX_COMPONENTS else np.nan)
        rank_label = metric_rank_label(team_df, metric, selected_index)
        parts.append('<div class="team-metric-row">')
        parts.append(f'<div class="team-metric-label">{html.escape(display_label(metric))}</div>')
        parts.append(f'<div class="team-metric-value">{html.escape(format_metric_value(metric, val))}</div>')
        parts.append(render_bar(pct))
        parts.append(metric_scorebox(pct, rank_label))
        parts.append('</div>')
    parts.append('</div>')
    with card_cols[i % 2]:
        st.markdown("".join(parts), unsafe_allow_html=True)

# Squad / cluster composition
st.markdown('<div class="team-section-title">Cluster composition</div>', unsafe_allow_html=True)

def cluster_text(value, fallback="Unclustered"):
    if pd.isna(value):
        return fallback
    value = str(value)
    return fallback if value in {"", "nan", "None"} else value

def render_cluster_composition(selected_team: str, selected_season: str) -> None:
    try:
        outfield = load_players_enriched()
    except Exception:
        outfield = pd.DataFrame()
    try:
        gk = load_gk_enriched()
    except Exception:
        gk = pd.DataFrame()

    frames = []
    if not outfield.empty:
        tmp = outfield[
            outfield["Season"].astype(str).eq(str(selected_season))
            & outfield["Team"].astype(str).eq(str(selected_team))
        ].copy()
        if not tmp.empty:
            tmp["Unit"] = tmp.get("Role bucket", "OUT")
            frames.append(tmp)

    if not gk.empty:
        tmp = gk[
            gk["Season"].astype(str).eq(str(selected_season))
            & gk["Team"].astype(str).eq(str(selected_team))
        ].copy()
        if not tmp.empty:
            tmp["Role bucket"] = "GK"
            tmp["Position"] = "GK"
            tmp["Unit"] = "GK"
            frames.append(tmp)

    if not frames:
        st.info("Nessuna composizione cluster disponibile per questa squadra.")
        return

    squad = pd.concat(frames, ignore_index=True, sort=False)
    squad["Minutes_sort"] = pd.to_numeric(squad.get("Minutes played"), errors="coerce").fillna(0)
    squad = squad.sort_values(["Unit", "Minutes_sort"], ascending=[True, False])

    parts = ['<div class="cluster-composition-wrap"><div class="cluster-composition-grid">']
    for h in ["Player", "Pos", "Role", "Archetype", "Cluster", "Min"]:
        parts.append(f'<div class="cluster-composition-head"><div>{h}</div></div>')
    for _, row in squad.iterrows():
        player_name = safe(row.get("Player"))
        pos = safe(row.get("Position"))
        role = safe(row.get("Role bucket"))
        archetype = cluster_text(row.get("style_cluster_short_label"), cluster_text(row.get("style_cluster_name")))
        cluster_id = cluster_text(row.get("style_cluster_id"), "—")
        mins = format_metric_value("Matches", row.get("Minutes played"))
        parts.append('<div class="cluster-composition-row">')
        parts.append(f'<div class="cluster-composition-player">{html.escape(player_name)}</div>')
        parts.append(f'<div>{html.escape(pos)}</div>')
        parts.append(f'<div>{html.escape(role)}</div>')
        parts.append(f'<div><span class="cluster-pill">{html.escape(archetype)}</span></div>')
        parts.append(f'<div>{html.escape(cluster_id)}</div>')
        parts.append(f'<div>{html.escape(mins)}</div>')
        parts.append('</div>')
    parts.append('</div></div>')
    st.markdown("".join(parts), unsafe_allow_html=True)

render_cluster_composition(selected_team, season)

# Scatter
st.markdown('<div class="team-section-title">Expected vs Effective / Scatter Lab</div>', unsafe_allow_html=True)
variables = [v for v in scatter_variable_options() if v in team_df.columns]
s1, s2, s3 = st.columns([1, 1, 1])
with s1:
    x_var = st.selectbox("X variable", variables, index=variables.index("Expected Performance") if "Expected Performance" in variables else 0, format_func=display_label)
with s2:
    y_var = st.selectbox("Y variable", variables, index=variables.index("Effective Performance") if "Effective Performance" in variables else min(1, len(variables)-1), format_func=display_label)
with s3:
    highlight = st.selectbox("Highlight team", ["None", *team_df["Team"].sort_values().tolist()], index=0)

plot_df = team_df.dropna(subset=[x_var, y_var]).copy()
plot_df["hover_text"] = (
    plot_df["Team"].astype(str)
    + "<br>GF total: "
    + plot_df["Goals total"].round(0).astype("Int64").astype(str)
    + "<br>GA total: "
    + plot_df["Goals against total"].round(0).astype("Int64").astype(str)
    + "<br>GD total: "
    + plot_df["Goal difference total"].round(0).astype("Int64").astype(str)
    + "<br>xG total: "
    + plot_df["xG total"].round(1).astype(str)
    + "<br>xGA total: "
    + plot_df["xGA total"].round(1).astype(str)
    + f"<br>{x_var}: "
    + plot_df[x_var].round(2).astype(str)
    + f"<br>{y_var}: "
    + plot_df[y_var].round(2).astype(str)
)

base_df = plot_df.copy()
selected_df = pd.DataFrame()
if highlight != "None":
    selected_df = plot_df[plot_df["Team"].eq(highlight)].copy()
    base_df = plot_df[~plot_df["Team"].eq(highlight)].copy()

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=base_df[x_var],
        y=base_df[y_var],
        mode="markers",
        text=base_df["hover_text"],
        hovertemplate="%{text}<extra></extra>",
        marker=dict(
            size=28,
            color="rgba(16,22,43,0.84)",
            line=dict(color="#5FFFE0", width=2.2),
            opacity=0.9,
        ),
        name="Teams",
    )
)
if not selected_df.empty:
    fig.add_trace(
        go.Scatter(
            x=selected_df[x_var],
            y=selected_df[y_var],
            mode="markers+text",
            text=selected_df["Team"],
            textposition="top center",
            customdata=selected_df["hover_text"],
            hovertemplate="%{customdata}<extra></extra>",
            marker=dict(size=36, color="#5FFFE0", line=dict(color="#070A18", width=3.2), opacity=1),
            textfont=dict(color="#F6F7FB", size=13),
            name="Selected",
        )
    )
fig.update_layout(
    template="plotly_dark",
    height=620,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(10,16,36,0.45)",
    font=dict(color="#F6F7FB"),
    legend=dict(font=dict(color="#DDE8FF")),
    margin=dict(l=30, r=30, t=40, b=40),
    xaxis=dict(title=display_label(x_var), gridcolor="rgba(255,255,255,0.10)", zerolinecolor="rgba(255,255,255,0.12)"),
    yaxis=dict(title=display_label(y_var), gridcolor="rgba(255,255,255,0.10)", zerolinecolor="rgba(255,255,255,0.12)"),
)
st.plotly_chart(fig, use_container_width=True)
