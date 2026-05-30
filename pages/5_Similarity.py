from __future__ import annotations

import html
import math

import numpy as np
import pandas as pd
import streamlit as st

from src.competition_utils import filter_big_five
from src.data_loader import available_leagues, available_seasons, load_players_enriched
from src.export_utils import render_export_png_button
from src.metric_catalog import ROLE_BUCKETS
from src.scoring import build_reference_df
from src.similarity import (
    build_feature_matrix,
    role_similarity_features,
    competition_label,
    competition_options,
    fit_index_scores,
    league_profile_and_weights,
    split_competition_label,
    weighted_similarity_scores,
)
from src.ui import inject_css, pct_color

st.set_page_config(page_title="Similarity Score", page_icon="🧬", layout="wide")
inject_css()

st.markdown(
    """
    <style>
    .sim-hero {
        border: 1px solid rgba(95,255,224,0.20);
        background: linear-gradient(115deg, rgba(16,22,43,0.88), rgba(33,21,60,0.68));
        border-radius: 24px;
        padding: 24px 28px;
        margin: 1.0rem 0 2.0rem 0;
        box-shadow: 0 18px 62px rgba(0,0,0,0.30), inset 0 0 24px rgba(95,255,224,0.04);
    }
    .sim-tag-row {display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;}
    .sim-tag {
        display:inline-flex;align-items:center;padding:5px 10px;border-radius:5px;
        background:rgba(168,85,247,0.18);border:1px solid rgba(168,85,247,0.35);
        color:#DCC8FF;font-size:0.76rem;font-weight:900;letter-spacing:0.07em;text-transform:uppercase;
    }
    .sim-tag-alt {background:rgba(95,255,224,0.14);border-color:rgba(95,255,224,0.30);color:#A8FFF0;}
    .sim-name {
        color:#F8FBFF;font-size:3rem;line-height:1;font-weight:950;letter-spacing:-0.03em;
        text-shadow:0 0 18px rgba(95,255,224,0.16);margin-bottom:10px;
    }
    .sim-meta {color:#B7CAE8;font-size:1rem;font-weight:650;margin-bottom:12px;}
    .sim-pill-row {display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}
    .sim-pill {
        display:inline-flex;align-items:center;min-height:28px;padding:5px 10px;border-radius:999px;
        background:rgba(95,255,224,0.10);color:#BFFFF4;border:1px solid rgba(95,255,224,0.20);
        font-size:0.74rem;font-weight:850;letter-spacing:0.03em;text-transform:uppercase;
    }
    .sim-title {
        color:#F8FBFF;font-size:2.55rem;font-weight:950;letter-spacing:-0.03em;margin:1.1rem 0 0.2rem 0;
    }
    .sim-subtitle {color:#B7CAE8;font-size:1rem;font-weight:650;margin-bottom:1.2rem;}
    .sim-table {
        background:rgba(16,22,43,0.50);
        border:1px solid rgba(255,255,255,0.06);
        border-radius:20px;
        overflow:hidden;
        box-shadow:0 14px 44px rgba(0,0,0,0.22);
        margin-bottom:18px;
    }
    .sim-table-header {
        display:grid;grid-template-columns:54px minmax(0,1fr) 88px 88px;gap:12px;
        align-items:center;
        padding:12px 18px;
        color:#AFC3E8;
        font-size:0.78rem;
        font-weight:950;
        letter-spacing:0.08em;
        text-transform:uppercase;
        border-bottom:1px solid rgba(255,255,255,0.08);
        background:rgba(10,16,36,0.52);
    }
    .sim-row {
        display:grid;grid-template-columns:54px minmax(0,1fr) 88px 88px;gap:12px;
        align-items:center;
        min-height:72px;
        padding:10px 18px;
        border-bottom:1px solid rgba(255,255,255,0.055);
        background:rgba(6,10,24,0.18);
    }
    .sim-row:nth-child(even) {background:rgba(255,255,255,0.025);}
    .sim-row:last-child {border-bottom:0;}
    .sim-rank {color:#B7CAE8;font-size:1rem;font-weight:950;text-align:center;}
    .sim-player {min-width:0;}
    .sim-player-name {color:#F6F7FB;font-size:1.05rem;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
    .sim-player-meta {color:#8EA2C6;font-size:0.78rem;font-weight:700;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
    .sim-fit-pill {
        display:inline-flex;align-items:center;justify-content:center;
        height:28px;min-width:46px;padding:0 9px;border-radius:999px;
        background:rgba(168,85,247,0.12);border:1px solid rgba(168,85,247,0.28);
        color:#DCC8FF;font-weight:950;font-size:0.80rem;
    }
    .sim-score-ring {
        width:52px;height:52px;border-radius:999px;padding:4px;margin-left:auto;
        display:flex;align-items:center;justify-content:center;
        box-shadow:0 0 18px rgba(95,255,224,0.12);
    }
    .sim-score-inner {
        width:100%;height:100%;border-radius:999px;background:#0A1024;
        display:flex;align-items:center;justify-content:center;
        color:#F6F7FB;font-size:1rem;font-weight:950;
    }
    .sim-feature-card {
        background:rgba(16,22,43,0.70);border:1px solid rgba(255,255,255,0.08);
        border-radius:18px;padding:14px;margin-top:14px;color:#B7CAE8;font-size:0.88rem;
    }
    .sim-feature-title {color:#5FFFE0;font-weight:950;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;}
    @media (max-width: 1100px) {
        .sim-name {font-size:2.2rem;}
        .sim-table-header, .sim-row {grid-template-columns:42px minmax(0,1fr) 62px 68px;gap:8px;padding-left:10px;padding-right:10px;}
        .sim-score-ring {width:44px;height:44px;}
    }
    
    .sim-detail-table-wrap {
        width: 100%;
        overflow-x: auto;
        border: 1px solid rgba(95,255,224,0.18);
        border-radius: 18px;
        background: rgba(10,16,36,0.78);
        box-shadow: 0 14px 44px rgba(0,0,0,0.22);
        margin: 0.4rem 0 1rem 0;
    }
    .sim-detail-table {
        width: 100%;
        border-collapse: collapse;
        min-width: 780px;
        color: #F6F7FB;
        font-size: 0.86rem;
    }
    .sim-detail-table thead th {
        background: #10162B;
        color: #AFC3E8;
        text-align: left;
        padding: 11px 10px;
        font-size: 0.74rem;
        font-weight: 950;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(95,255,224,0.18);
    }
    .sim-detail-table tbody td {
        padding: 10px 10px;
        border-bottom: 1px solid rgba(255,255,255,0.055);
        background: rgba(16,22,43,0.72);
    }
    .sim-detail-table tbody tr:nth-child(even) td { background: rgba(12,18,38,0.78); }
    .sim-detail-table tbody tr:hover td { background: rgba(95,255,224,0.075); }
    .sim-detail-table .num { text-align: right; font-variant-numeric: tabular-nums; font-weight: 850; }
    .sim-detail-table .feature { font-weight: 950; color: #F6F7FB; white-space: nowrap; }

</style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="fm-title">SIMILARITY SCORE</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fm-subtitle">Trova giocatori simili · role profile · league weighting · fit index per campionato target</div>',
    unsafe_allow_html=True,
)

export_left, export_right = st.columns([5.5, 1.2])
with export_left:
    st.write("")
with export_right:
    render_export_png_button("similarity_score")

df = load_players_enriched()


def fmt_intish(value, suffix=""):
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):,.0f}{suffix}".replace(",", ".")
    except Exception:
        return f"{value}{suffix}"


def txt(value, fallback="—"):
    if pd.isna(value):
        return fallback
    return str(value)


def comp_mask(data: pd.DataFrame, label: str) -> pd.Series:
    league, nation = split_competition_label(label)
    if nation:
        return data["League"].astype(str).eq(league) & data["Nation"].astype(str).eq(nation)
    return data["League"].astype(str).eq(league)


def scope_pool(data: pd.DataFrame, season: str, scope: str, player_comp_label: str, custom_labels: list[str], min_minutes: int) -> pd.DataFrame:
    pool = data[data["Season"].astype(str).eq(str(season))].copy()
    pool = pool[pd.to_numeric(pool["Minutes played"], errors="coerce").fillna(0) >= min_minutes]

    if scope == "Player competition":
        pool = pool[comp_mask(pool, player_comp_label)]
    elif scope == "Big Five":
        pool = filter_big_five(pool)
    elif scope == "Custom competitions" and custom_labels:
        mask = pd.Series(False, index=pool.index)
        for label in custom_labels:
            mask = mask | comp_mask(pool, label)
        pool = pool[mask]
    elif scope == "All leagues":
        pass
    return pool


with st.sidebar:
    st.markdown("### Similarity filters")
    seasons = available_seasons(df)
    season = st.selectbox("Season", seasons, index=0)

    season_df = df[df["Season"].astype(str).eq(str(season))].copy()
    player_league_filter = st.selectbox("Player league filter", ["All leagues", *available_leagues(season_df)])
    player_pool = season_df.copy()
    if player_league_filter != "All leagues":
        player_pool = player_pool[player_pool["League"].astype(str).eq(player_league_filter)]

    teams = ["All teams", *sorted(player_pool["Team"].dropna().astype(str).unique().tolist())]
    selected_team = st.selectbox("Team filter", teams)
    if selected_team != "All teams":
        player_pool = player_pool[player_pool["Team"].astype(str).eq(selected_team)]

    if player_pool.empty:
        st.warning("Nessun giocatore per questi filtri.")
        st.stop()

    player_options = (
        player_pool.assign(_label=player_pool["Player"].astype(str) + " · " + player_pool["Team"].astype(str) + " · " + player_pool["Position"].astype(str))
        .sort_values(["Player", "Team"])
    )
    selected_label = st.selectbox("Selected player", player_options["_label"].tolist())
    selected_idx = player_options.loc[player_options["_label"].eq(selected_label)].index[0]
    selected_player = df.loc[selected_idx]

    st.markdown("---")
    default_role = selected_player.get("Role bucket", "AM")
    role_keys = list(ROLE_BUCKETS.keys())
    default_role_index = role_keys.index(default_role) if default_role in role_keys else 0
    compare_role = st.selectbox("Compare as role", role_keys, index=default_role_index)

    profile = st.selectbox("Similarity profile", ["Balanced", "Playing Style", "Performance"], index=0)
    mode = st.selectbox("Metric value", ["Raw", "Possession-adjusted"], index=1)

    reference_scope = st.selectbox(
        "Candidate scope",
        ["Player competition", "Big Five", "All leagues", "Custom competitions"],
        index=1,
    )

    season_comp_options = competition_options(season_df)
    custom_labels: list[str] = []
    if reference_scope == "Custom competitions":
        custom_labels = st.multiselect("Custom competitions", season_comp_options, default=season_comp_options[:3])

    target_default_label = competition_label(selected_player)
    target_index = season_comp_options.index(target_default_label) if target_default_label in season_comp_options else 0
    target_competition = st.selectbox("Target league for Fit Index", season_comp_options, index=target_index)

    weighting_label = st.selectbox("League weighting", ["Off", "Light", "Medium", "Strong"], index=2)
    weighting_map = {"Off": 0.0, "Light": 0.75, "Medium": 1.25, "Strong": 1.85}
    weighting_intensity = weighting_map[weighting_label]

    exclude_same_team = st.checkbox("Exclude same team", value=True)

    st.markdown('<div class="control-label">Minimum minutes</div>', unsafe_allow_html=True)
    if "similarity_min_minutes_ref" not in st.session_state:
        st.session_state["similarity_min_minutes_ref"] = 900

    minus_col, value_col, plus_col = st.columns([0.9, 1.5, 0.9])
    with minus_col:
        if st.button("−", key="similarity_minutes_minus", use_container_width=True):
            st.session_state["similarity_min_minutes_ref"] = max(0, int(st.session_state["similarity_min_minutes_ref"]) - 100)
    with plus_col:
        if st.button("+", key="similarity_minutes_plus", use_container_width=True):
            st.session_state["similarity_min_minutes_ref"] = min(2500, int(st.session_state["similarity_min_minutes_ref"]) + 100)

    min_minutes = int(st.session_state["similarity_min_minutes_ref"])
    with value_col:
        st.markdown(f'<div class="minute-stepper-value">{min_minutes}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Age filter")
    age_min, age_max = st.columns(2)
    with age_min:
        min_age = st.number_input("Min age", min_value=14, max_value=45, value=16, step=1, key="similarity_min_age")
    with age_max:
        max_age = st.number_input("Max age", min_value=14, max_value=45, value=40, step=1, key="similarity_max_age")

    if max_age < min_age:
        st.warning("Max age deve essere ≥ Min age.")
        max_age = min_age

    manual_feature_weights = {}
    with st.expander("Advanced metric weights"):
        st.caption("Peso opzionale delle feature usate per la similarità. 1.00 = neutro.")
        preview_features = role_similarity_features(compare_role, profile)
        weight_options = [0.50, 0.75, 1.00, 1.25, 1.50, 2.00]
        for feature in preview_features:
            feature_name = feature["name"]
            manual_feature_weights[feature_name] = st.selectbox(
                feature_name,
                weight_options,
                index=2,
                key=f"sim_weight_{compare_role}_{profile}_{feature_name}",
            )

selected_comp_label = competition_label(selected_player)

candidate_pool_all_roles = scope_pool(
    df,
    str(season),
    reference_scope,
    selected_comp_label,
    custom_labels,
    min_minutes,
)
candidate_pool = candidate_pool_all_roles[candidate_pool_all_roles["Role bucket"].astype(str).eq(compare_role)].copy()
candidate_pool = candidate_pool[
    pd.to_numeric(candidate_pool["Age"], errors="coerce").between(min_age, max_age, inclusive="both")
].copy()

# Ensure the selected player can be represented even if he is outside the chosen role/candidate group.
reference_df = candidate_pool.copy()
if selected_player.name not in reference_df.index:
    reference_df = pd.concat([reference_df, selected_player.to_frame().T], axis=0)

if exclude_same_team:
    candidate_pool = candidate_pool[~candidate_pool["Team"].astype(str).eq(txt(selected_player.get("Team")))]

candidate_pool = candidate_pool[candidate_pool.index != selected_player.name].copy()

if candidate_pool.empty or len(reference_df) < 3:
    st.warning("Nessun candidato disponibile con questi filtri. Amplia scope o abbassa i minuti.")
    st.stop()

combined = pd.concat([selected_player.to_frame().T, candidate_pool], axis=0)
feature_matrix, feature_names = build_feature_matrix(combined, reference_df, compare_role, profile, mode)

if feature_matrix.empty or len(feature_names) == 0:
    st.warning("Nessuna feature di similarità disponibile per questo ruolo/profilo.")
    st.stop()

selected_vector = feature_matrix.loc[selected_player.name]
candidate_matrix = feature_matrix.loc[candidate_pool.index]

# Target league profile and league weighting.
target_league, target_nation = split_competition_label(target_competition)
target_reference = df[
    df["Season"].astype(str).eq(str(season))
    & df["Role bucket"].astype(str).eq(compare_role)
    & (pd.to_numeric(df["Minutes played"], errors="coerce").fillna(0) >= min_minutes)
    & (pd.to_numeric(df["Age"], errors="coerce").between(min_age, max_age, inclusive="both"))
].copy()
target_reference_with_scope = target_reference.copy()
target_matrix, _ = build_feature_matrix(target_reference_with_scope, reference_df, compare_role, profile, mode)
league_profile, weights, target_n = league_profile_and_weights(
    target_matrix,
    target_reference_with_scope,
    target_league,
    target_nation,
    intensity=weighting_intensity,
)

manual_weights = pd.Series(manual_feature_weights, dtype=float)
if weights is None or weights.empty:
    combined_weights = manual_weights.reindex(feature_names).fillna(1.0)
else:
    combined_weights = weights.reindex(feature_names).fillna(1.0) * manual_weights.reindex(feature_names).fillna(1.0)

similarity_scores = weighted_similarity_scores(
    selected_vector,
    candidate_matrix,
    combined_weights,
)
fit_scores = fit_index_scores(candidate_matrix, league_profile, combined_weights)

results = candidate_pool.copy()
results["Similarity"] = similarity_scores
results["Fit Index"] = fit_scores
results = results.dropna(subset=["Similarity"]).sort_values("Similarity", ascending=False).head(20).reset_index(drop=True)
results.insert(0, "Rank", np.arange(1, len(results) + 1))

season_tag = txt(selected_player.get("Season"))
age = fmt_intish(selected_player.get("Age"), " yrs")
minutes = fmt_intish(selected_player.get("Minutes played"), " min")
pos = txt(selected_player.get("Position"))
club = txt(selected_player.get("Team"))
league = txt(selected_player.get("League"))

st.markdown(
    f"""
    <div class="sim-hero">
      <div class="sim-tag-row">
        <span class="sim-tag">{html.escape(compare_role)}</span>
        <span class="sim-tag sim-tag-alt">{html.escape(season_tag)}</span>
      </div>
      <div class="sim-name">{html.escape(txt(selected_player.get('Player')))}</div>
      <div class="sim-meta">{html.escape(club)} · {html.escape(league)} · {html.escape(pos)} · {html.escape(age)} · {html.escape(minutes)}</div>
      <div class="sim-pill-row">
        <span class="sim-pill">Profile: {html.escape(profile)}</span>
        <span class="sim-pill">Candidate scope: {html.escape(reference_scope)}</span>
        <span class="sim-pill">Mode: {html.escape(mode)}</span>
        <span class="sim-pill">League weighting: {html.escape(weighting_label)}</span>
        <span class="sim-pill">Target: {html.escape(target_competition)}</span>
        <span class="sim-pill">Age: {min_age}-{max_age}</span>
        <span class="sim-pill">Features: {len(feature_names)}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="sim-title">20 Most Similar Players</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sim-subtitle">{html.escape(reference_scope)} · {html.escape(str(season))} · {html.escape(compare_role)} · age {min_age}-{max_age} · ≥ {min_minutes} minutes · target league n={target_n}</div>',
    unsafe_allow_html=True,
)

if len(results) == 0:
    st.info("Nessun risultato di similarità disponibile.")
    st.stop()


def score_ring(score: float) -> str:
    if pd.isna(score):
        score = 0
    score = float(max(0, min(100, score)))
    color = pct_color(score)
    return (
        f'<div class="sim-score-ring" style="background:conic-gradient({color} {score * 3.6:.1f}deg, rgba(255,255,255,0.10) 0deg);">'
        f'<div class="sim-score-inner">{score:.0f}</div>'
        f'</div>'
    )


def render_result_table(table: pd.DataFrame) -> None:
    html_out = (
        '<div class="sim-table">'
        '<div class="sim-table-header">'
        '<div>#</div><div>Player</div><div>Fit</div><div>Score</div>'
        '</div>'
    )

    for _, row in table.iterrows():
        fit = row.get("Fit Index", np.nan)
        fit_txt = "—" if pd.isna(fit) else f"{float(fit):.0f}"
        cluster = txt(row.get("style_cluster_short_label"), txt(row.get("style_cluster_name"), txt(row.get("style_cluster_id"), "Unclustered")))
        meta = (
            f"{fmt_intish(row.get('Age'))}, {txt(row.get('Position'))}, "
            f"{txt(row.get('Team'))} · {txt(row.get('League'))} · {cluster}"
        )
        html_out += (
            '<div class="sim-row">'
            f'<div class="sim-rank">{int(row["Rank"])}</div>'
            '<div class="sim-player">'
            f'<div class="sim-player-name">{html.escape(txt(row.get("Player")))}</div>'
            f'<div class="sim-player-meta">{html.escape(meta)}</div>'
            '</div>'
            f'<div><span class="sim-fit-pill">{fit_txt}</span></div>'
            f'<div>{score_ring(row.get("Similarity", 0))}</div>'
            '</div>'
        )

    html_out += "</div>"
    st.markdown(html_out, unsafe_allow_html=True)


left, right = st.columns(2)
with left:
    render_result_table(results.iloc[:10])
with right:
    render_result_table(results.iloc[10:20])

def render_similarity_dark_table(df: pd.DataFrame) -> str:
    parts = ['<div class="sim-detail-table-wrap"><table class="sim-detail-table">']
    parts.append('<thead><tr>')
    for col in df.columns:
        parts.append(f'<th>{html.escape(str(col))}</th>')
    parts.append('</tr></thead><tbody>')
    for _, row in df.iterrows():
        parts.append('<tr>')
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                txt = '—'
            elif isinstance(value, (float, np.floating)):
                txt = f'{float(value):.1f}' if 'percentile' in col.lower() or 'profile' in col.lower() else f'{float(value):.2f}'
            else:
                txt = str(value)
            cls = 'num' if col != 'Feature' else 'feature'
            if col == 'Feature':
                parts.append(f'<td class="feature">{html.escape(txt)}</td>')
            else:
                parts.append(f'<td class="num">{html.escape(txt)}</td>')
        parts.append('</tr>')
    parts.append('</tbody></table></div>')
    return ''.join(parts)

with st.expander("Similarity model details"):
    st.markdown(
        """
        **Similarity Score**: distanza ponderata tra profili percentili role-specific.  
        **Fit Index**: compatibilità del giocatore con il profilo medio del campionato target.  
        **League Weighting**: aumenta il peso delle feature che caratterizzano di più il campionato target rispetto al riferimento generale.
        """
    )
    feature_df = pd.DataFrame(
        {
            "Feature": feature_names,
            "Selected percentile": selected_vector.reindex(feature_names).round(1).values,
            "Final weight": combined_weights.reindex(feature_names).round(2).values if not combined_weights.empty else np.nan,
            "Target league profile": league_profile.reindex(feature_names).round(1).values if not league_profile.empty else np.nan,
        }
    )
    st.markdown(render_similarity_dark_table(feature_df), unsafe_allow_html=True)
