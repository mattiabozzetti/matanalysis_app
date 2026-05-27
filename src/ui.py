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
        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 2rem;
        }
        header[data-testid="stHeader"], .stApp > header {
            background: linear-gradient(90deg, #050711 0%, #070A18 52%, #0A1024 100%) !important;
            border-bottom: 1px solid rgba(95,255,224,0.12) !important;
            box-shadow: 0 10px 28px rgba(0,0,0,0.24) !important;
        }
        [data-testid="stToolbar"] {
            background: transparent !important;
            color: #F6F7FB !important;
        }
        [data-testid="stToolbar"] * {
            color: #F6F7FB !important;
            fill: #F6F7FB !important;
        }
        [data-testid="stDecoration"] {
            display: none !important;
        }
        [data-testid="stStatusWidget"] {
            background: rgba(7,10,24,0.88) !important;
            color: #F6F7FB !important;
            border: 1px solid rgba(95,255,224,0.18) !important;
            border-radius: 999px !important;
        }
        iframe, [data-testid="stAppViewContainer"] {
            background: #070A18 !important;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(7,10,24,0.98), rgba(15,20,40,0.98));
            border-right: 1px solid rgba(95,255,224,0.18);
        }
        .fm-title {
            font-size: 2.25rem;
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
            margin-bottom: 18px;
            min-height: 162px;
        }
        .hero-card-large {padding: 24px 28px 22px 28px;}
        .hero-topline {display:flex; gap:10px; align-items:center; margin-bottom:10px; flex-wrap:wrap;}
        .hero-tag {
            display:inline-flex; align-items:center; padding:5px 10px; border-radius:4px;
            background: rgba(168,85,247,0.18); border: 1px solid rgba(168,85,247,0.35);
            color:#DCC8FF; font-size:0.76rem; font-weight:800; letter-spacing:0.07em;
        }
        .hero-tag-alt {
            background: rgba(95,255,224,0.14); border: 1px solid rgba(95,255,224,0.30); color:#A8FFF0;
        }
        .hero-name {font-size: 2rem; font-weight: 900; margin-bottom: 4px;}
        .hero-name-large {font-size: 3.1rem; line-height: 1; margin-bottom: 14px;}
        .hero-meta {color: var(--muted); font-size: 0.95rem;}
        .hero-meta-upper {font-size: 1rem; margin-bottom: 14px;}
        .hero-info-grid {
            display:grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap:10px; max-width: 900px;
        }
        .hero-info-box {
            background: rgba(18,25,50,0.82); border:1px solid rgba(95,255,224,0.16); border-radius: 4px;
            padding:10px 14px; min-height:68px; display:flex; flex-direction:column; justify-content:center;
        }
        .hero-info-label {font-size:0.72rem; color:var(--muted); letter-spacing:0.08em; margin-bottom:5px;}
        .hero-info-value {font-size:1.05rem; font-weight:800; color:#F6F7FB;}
        .hero-context-line {margin-top: 14px; color:#B7CAE8; font-size:0.88rem; letter-spacing:0.04em; text-transform:uppercase;}
        .overall-badge {
            width: 126px; height: 126px; border-radius: 999px;
            background: conic-gradient(from 180deg, #5FFFE0, #7CFF8A, #FFE66D, #5FFFE0);
            display: flex; align-items: center; justify-content: center;
            padding: 4px; margin-left: auto;
            box-shadow: 0 0 34px rgba(95,255,224,0.20);
        }
        .overall-inner {
            background: #0A1024; border-radius: 999px; width: 100%; height: 100%;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .overall-value {font-size: 2.4rem; font-weight: 900; line-height: 1;}
        .overall-label {font-size: 0.72rem; color: var(--muted); letter-spacing: 0.08em; margin-top: 6px;}
        .metric-panel {
            background: var(--panel);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 16px 16px 12px 16px;
            margin-bottom: 16px;
            box-shadow: 0 14px 44px rgba(0,0,0,0.23);
        }
        .metric-group-header {display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 11px;}
        .metric-group-title {
            font-size: 1.05rem;
            font-weight: 900;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            display: flex; align-items: center; gap: 8px;
            margin-bottom: 0;
        }
        .group-score-badge {
            min-width: 38px; height: 30px; padding: 0 10px; border-radius: 999px;
            display:inline-flex; align-items:center; justify-content:center;
            background: rgba(95,255,224,0.10); border:1px solid rgba(95,255,224,0.22);
            font-size: 0.95rem; font-weight: 900;
            box-shadow: 0 0 14px rgba(95,255,224,0.08);
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

        /* WIDGETS */
        .stSelectbox label, .stMultiSelect label, .stSlider label, .stRadio label {
            color: #AFC3E8 !important; font-weight: 700 !important;
        }
        div[data-baseweb="select"] > div {
            background: rgba(18,25,50,0.96) !important;
            border: 1px solid rgba(95,255,224,0.20) !important;
            border-radius: 14px !important;
            color: #F6F7FB !important;
            min-height: 46px !important;
            box-shadow: none !important;
        }
        div[data-baseweb="select"] * {color:#F6F7FB !important;}
        div[role="listbox"] {
            background: rgba(13,18,35,0.98) !important;
            color: #F6F7FB !important;
            border: 1px solid rgba(95,255,224,0.20) !important;
        }
        div[role="option"] {background: transparent !important;}
        div[role="option"]:hover {background: rgba(95,255,224,0.10) !important;}
        [data-testid="stSidebar"] .stRadio > div {
            background: transparent !important;
        }
        [data-testid="stSidebar"] .stRadio label {
            background: transparent !important;
            color: #DDE8FF !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] {
            gap: 8px;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            padding: 4px 0;
        }
        [data-baseweb="radio"] > div:first-child {
            background-color: rgba(18,25,50,1) !important;
            border-color: rgba(95,255,224,0.35) !important;
            box-shadow: 0 0 0 1px rgba(95,255,224,0.14) !important;
        }
        [data-baseweb="radio"] * {
            color: #DDE8FF !important;
        }
        .stSlider [data-baseweb="slider"] > div > div {
            background: rgba(95,255,224,0.65) !important;
        }
        .stSlider [role="slider"] {
            background: #5FFFE0 !important;
            border: 2px solid #0A1024 !important;
            box-shadow: 0 0 0 2px rgba(95,255,224,0.25) !important;
        }
        .stSlider [data-testid="stTickBarMin"], .stSlider [data-testid="stTickBarMax"] {
            color:#AFC3E8 !important;
        }
        button[kind="secondaryFormSubmit"], .stButton>button {
            background: rgba(18,25,50,0.96) !important;
            color:#F6F7FB !important;
            border: 1px solid rgba(95,255,224,0.22) !important;
        }

        div[data-baseweb="popover"], div[data-baseweb="menu"] {
            background: rgba(13,18,35,0.98) !important;
            color: #F6F7FB !important;
        }
        div[data-baseweb="select"] svg {
            fill: #AFC3E8 !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(95,255,224,0.12) !important;
        }

        .stExpander {
            background: rgba(16, 22, 43, 0.55); border-radius: 16px; border:1px solid rgba(255,255,255,0.08);
        }

        @media (max-width: 1200px) {
            .hero-info-grid {grid-template-columns: repeat(3, minmax(0, 1fr));}
        }
        @media (max-width: 900px) {
            .hero-name-large {font-size: 2.3rem;}
            .hero-info-grid {grid-template-columns: repeat(2, minmax(0, 1fr));}
        }

        /* RADIO FIX: keep the dark palette but make the selected dot visible */
        input[type="radio"] {
            accent-color: #5FFFE0 !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            color: #DDE8FF !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="radio"] {
            color: #DDE8FF !important;
        }
        [data-testid="stSidebar"] [data-baseweb="radio"] div[role="radio"],
        [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {
            border: 2px solid rgba(95,255,224,0.38) !important;
            background: rgba(16, 22, 43, 0.95) !important;
            box-shadow: inset 0 0 0 3px rgba(16,22,43,0.95), 0 0 0 1px rgba(95,255,224,0.08) !important;
        }
        [data-testid="stSidebar"] [data-baseweb="radio"] div[role="radio"][aria-checked="true"],
        [data-testid="stSidebar"] [data-baseweb="radio"] input:checked ~ div:first-of-type,
        [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
            border-color: #5FFFE0 !important;
            background: radial-gradient(circle at center, #5FFFE0 0 42%, rgba(16,22,43,0.98) 46% 100%) !important;
            box-shadow: 0 0 14px rgba(95,255,224,0.38) !important;
        }

        /* SLIDER FIX: remove Streamlit red accent and force the neon palette */
        [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {
            padding-top: 0.6rem !important;
        }
        [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div {
            background: rgba(95,255,224,0.24) !important;
        }
        [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div {
            background: linear-gradient(90deg, #5FFFE0, #7CFF8A) !important;
        }
        [data-testid="stSidebar"] .stSlider [role="slider"] {
            width: 22px !important;
            height: 22px !important;
            background: #5FFFE0 !important;
            border: 4px solid #10162B !important;
            box-shadow: 0 0 0 2px rgba(95,255,224,0.80), 0 0 18px rgba(95,255,224,0.45) !important;
        }
        [data-testid="stSidebar"] .stSlider [data-testid="stThumbValue"] {
            color: #5FFFE0 !important;
            font-weight: 900 !important;
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
            line=dict(width=3, color="#5FFFE0"),
            marker=dict(size=5, color="#5FFFE0"),
            fillcolor="rgba(95,255,224,0.18)",
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
