from __future__ import annotations

import streamlit as st

from src.data_loader import load_players_enriched
from src.ui import inject_css

st.set_page_config(
    page_title="Football Scouting Lab",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

st.markdown('<div class="fm-title">FOOTBALL SCOUTING LAB</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fm-subtitle">Repository-based Streamlit app · Player Card first · GK module later</div>',
    unsafe_allow_html=True,
)

with st.spinner("Preparazione dati..."):
    df = load_players_enriched()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Players", f"{df['Player'].nunique():,}".replace(",", "."))
c2.metric("Rows", f"{len(df):,}".replace(",", "."))
c3.metric("Leagues", f"{df['League'].nunique():,}".replace(",", "."))
c4.metric("Seasons", f"{df['Season'].nunique():,}".replace(",", "."))

st.markdown(
    """
    <div class="hero-card">
      <div class="hero-name">Player Card</div>
      <div class="hero-meta">
        La prima pagina operativa è la card dei giocatori di movimento: valori raw o possession-adjusted,
        percentili per ruolo/campionato, overall role-based e doppio radar Playing Style / Performance.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info("Apri la pagina **Player Card** dalla sidebar per iniziare lo scouting.")
