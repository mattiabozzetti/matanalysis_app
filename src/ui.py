from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #070A18;
            --panel: rgba(16, 22, 43, 0.82);
            --panel2: rgba(28, 36, 68, 0.72);
            --cyan: #5FFFE0;
            --green: #7CFF8A;
            --yellow: #FFE66D;
            --orange: #FF9F43;
            --red: #FF4F6D;
            --purple: #A855F7;
            --muted: #8EA2C6;
            --text: #F6F7FB;
        }
        .stApp {
            background: radial-gradient(circle at top left, rgba(95,255,224,0.10), transparent 30%),
                        radial-gradient(circle at 80% 20%, rgba(168,85,247,0.16), transparent 35%),
                        linear-gradient(135deg, #050711 0%, #070A18 45%, #0A1024 100%);
            color: var(--text);
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(7,10,24,0.96), rgba(15,20,40,0.96));
            border-right: 1px solid rgba(95,255,224,0.18);
        }
        .fm-title {
            font-size: 2.2rem;
            font-weight: 900;
            letter-spacing: 0.04em;
            margin: 0 0 0.2rem 0;
            color: #F8FBFF;
            text-shadow: 0 0 18px rgba(95,255,224,0.22);
        }
        .fm-subtitle {
            color: var(--muted);
            font-size: 0.95rem;
            margin-bottom: 1.4rem;
        }
        .hero-card {
            border: 1px solid rgba(95,255,224,0.24);
            background: linear-gradient(135deg, rgba(16,22,43,0.92), rgba(33,21,60,0.72));
            border-radius: 26px;
            padding: 22px 24px;
            box-shadow: 0 18px 80px rgba(0,0,0,0.32), inset 0 0 26px rgba(95,255,224,0.04);
            margin-bottom: 16px;
        }
        .hero-name {font-size: 2rem; font-weight: 900; margin-bottom: 4px;}
        .hero-meta {color: var(--muted); font-size: 0.95rem;}
        .overall-badge {
            width: 108px; height: 108px; border-radius: 999px;
            background: conic-gradient(from 180deg, #5FFFE0, #7CFF8A, #FFE66D, #5FFFE0);
            display: flex; align-items: center; justify-content: center;
            padding: 4px; margin-left: auto;
            box-shadow: 0 0 34px rgba(95,255,224,0.20);
        }
        .overall-inner {
            background: #0A1024; border-radius: 999px; width: 100%; height: 100%;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .overall-value {font-size: 2rem; font-weight: 900; line-height: 1;}
        .overall-label {font-size: 0.72rem; color: var(--muted); letter-spacing: 0.08em; margin-top: 4px;}
        .metric-panel {
            background: var(--panel);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 16px 16px 12px 16px;
            margin-bottom: 16px;
            box-shadow: 0 14px 44px rgba(0,0,0,0.23);
        }
        .metric-group-title {
            font-size: 1.05rem;
            font-weight: 900;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 11px;
            display: flex; align-items: center; gap: 8px;
        }
        .metric-row {
            display: grid;
            grid-template-columns: 1.45fr 0.55fr 2fr 0.42fr;
            align-items: center;
            gap: 10px;
            padding: 7px 0;
            border-bottom: 1px solid rgba(255,255,255,0.055);
        }
        .metric-row:last-child {border-bottom: 0;}
        .metric-label {font-size: 0.86rem; color: #DDE8FF;}
        .metric-value {font-size: 0.88rem; color: #FFFFFF; font-weight: 800; text-align: right;}
        .bar-track {height: 9px; border-radius: 999px; background: rgba(255,255,255,0.10); overflow: hidden;}
        .bar-fill {height: 100%; border-radius: 999px; box-shadow: 0 0 14px currentColor;}
        .metric-pct {font-size: 0.78rem; font-weight: 800; text-align: right; color: #F6F7FB;}
        .pill {
            display: inline-block; padding: 5px 9px; border-radius: 999px;
            background: rgba(95,255,224,0.10); color: #BFFFF4;
            border: 1px solid rgba(95,255,224,0.18); font-size: 0.74rem;
            margin: 2px 4px 2px 0;
        }
        .small-note {color: var(--muted); font-size: 0.82rem;}
        div[data-testid="stMetric"] {
            background: rgba(16,22,43,0.70);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def pct_color(pct: float) -> str:
    if pct is None or math.isnan(pct):
        return "#2E3A59"
    if pct >= 90:
        return "#5FFFE0"
    if pct >= 75:
        return "#7CFF8A"
    if pct >= 50:
        return "#FFE66D"
    if pct >= 25:
        return "#FF9F43"
    return "#FF4F6D"


def metric_row_html(label: str, value: str, pct: float) -> str:
    pct_txt = "—" if pct is None or math.isnan(pct) else f"{pct:.0f}"
    width = 0 if pct is None or math.isnan(pct) else max(0, min(100, pct))
    color = pct_color(pct)
    return f"""
    <div class="metric-row">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="bar-track"><div class="bar-fill" style="width:{width:.0f}%; background:{color}; color:{color};"></div></div>
        <div class="metric-pct">{pct_txt}</div>
    </div>
    """


def radar_figure(labels: list[str], values: list[float], title: str) -> go.Figure:
    clean_values = [0 if pd.isna(v) else float(v) for v in values]
    closed_labels = labels + [labels[0]]
    closed_values = clean_values + [clean_values[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=closed_values,
            theta=closed_labels,
            fill="toself",
            line=dict(width=3),
            marker=dict(size=5),
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
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=38, r=38, t=56, b=38),
        showlegend=False,
        height=430,
    )
    return fig
