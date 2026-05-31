from __future__ import annotations

import html
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui import inject_css, pct_color
from src.competition_utils import is_big_five_mask

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

st.set_page_config(page_title="Style Archetypes", page_icon="🧩", layout="wide")
inject_css()

st.markdown(
    """
<style>
.arch-hero {
    border: 1px solid rgba(95,255,224,0.20);
    background: radial-gradient(circle at top left, rgba(95,255,224,0.13), transparent 34%),
                linear-gradient(115deg, rgba(16,22,43,0.92), rgba(33,21,60,0.72));
    border-radius: 26px;
    padding: 30px 32px;
    margin: 0.8rem 0 1.4rem 0;
    box-shadow: 0 18px 62px rgba(0,0,0,0.30), inset 0 0 26px rgba(95,255,224,0.04);
}
.arch-kicker {color:#5FFFE0;font-size:0.82rem;font-weight:950;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:10px;}
.arch-title {color:#F8FBFF;font-size:3.1rem;line-height:1;font-weight:950;letter-spacing:-0.04em;text-shadow:0 0 18px rgba(95,255,224,0.18);margin-bottom:12px;}
.arch-subtitle {color:#B7CAE8;font-size:1.02rem;line-height:1.55;max-width:1120px;font-weight:650;}
.arch-pill-row {display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;}
.arch-pill {display:inline-flex;align-items:center;min-height:28px;padding:5px 10px;border-radius:999px;background:rgba(95,255,224,0.10);color:#BFFFF4;border:1px solid rgba(95,255,224,0.20);font-size:0.74rem;font-weight:850;letter-spacing:0.03em;text-transform:uppercase;}
.arch-section-title {color:#F8FBFF;font-size:1.65rem;font-weight:950;margin:1.8rem 0 0.8rem 0;letter-spacing:-0.02em;}
.arch-card {background:rgba(16,22,43,0.84);border:1px solid rgba(95,255,224,0.16);border-radius:22px;padding:18px 18px 15px 18px;margin-bottom:16px;box-shadow:0 14px 44px rgba(0,0,0,0.23);min-height:285px;}
.arch-card-head {display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:10px;}
.arch-id {display:inline-flex;padding:5px 9px;border-radius:999px;background:rgba(95,255,224,0.10);border:1px solid rgba(95,255,224,0.24);color:#5FFFE0;font-size:0.72rem;font-weight:950;letter-spacing:0.08em;text-transform:uppercase;}
.arch-name {color:#F8FBFF;font-size:1.25rem;line-height:1.12;font-weight:950;letter-spacing:-0.02em;margin-top:8px;}
.arch-count {color:#BFFFF4;font-size:1.4rem;font-weight:950;text-align:right;}
.arch-count-label {color:#8EA2C6;font-size:0.68rem;font-weight:850;text-transform:uppercase;text-align:right;letter-spacing:0.08em;}
.arch-desc {color:#B7CAE8;font-size:0.86rem;line-height:1.42;font-weight:650;margin:10px 0 12px 0;}
.arch-mini-label {color:#5FFFE0;font-size:0.72rem;font-weight:950;letter-spacing:0.08em;text-transform:uppercase;margin-top:8px;}
.arch-mini-text {color:#DDE8FF;font-size:0.78rem;line-height:1.35;font-weight:650;margin-top:3px;}
.arch-table-wrap {width:100%;overflow-x:auto;border:1px solid rgba(95,255,224,0.18);border-radius:18px;background:rgba(10,16,36,0.78);box-shadow:0 14px 44px rgba(0,0,0,0.22);margin-bottom:1.2rem;}
.arch-table {width:100%;border-collapse:collapse;min-width:880px;color:#F6F7FB;font-size:0.86rem;}
.arch-table thead th {background:#10162B;color:#AFC3E8;text-align:left;padding:11px 10px;font-size:0.74rem;font-weight:950;letter-spacing:0.06em;text-transform:uppercase;border-bottom:1px solid rgba(95,255,224,0.18);}
.arch-table tbody td {padding:10px 10px;border-bottom:1px solid rgba(255,255,255,0.055);background:rgba(16,22,43,0.72);}
.arch-table tbody tr:nth-child(even) td {background:rgba(12,18,38,0.78);}
.arch-table tbody tr:hover td {background:rgba(95,255,224,0.075);}
.arch-table .num {text-align:right;font-variant-numeric:tabular-nums;font-weight:850;}
.arch-score-pill {display:inline-flex;min-width:44px;height:24px;border-radius:999px;align-items:center;justify-content:center;padding:0 8px;background:rgba(95,255,224,0.08);border:1px solid rgba(95,255,224,0.16);font-weight:950;}
</style>
""",
    unsafe_allow_html=True,
)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


@st.cache_data(show_spinner="Carico archetipi...")
def load_archetype_data() -> dict[str, pd.DataFrame]:
    return {
        "players": pd.read_csv(PROCESSED / "players_enriched_with_clusters.csv.gz", compression="gzip", low_memory=False) if (PROCESSED / "players_enriched_with_clusters.csv.gz").exists() else pd.DataFrame(),
        "gk": pd.read_csv(PROCESSED / "gk_enriched_with_clusters.csv.gz", compression="gzip", low_memory=False) if (PROCESSED / "gk_enriched_with_clusters.csv.gz").exists() else pd.DataFrame(),
        "profiles": _read_csv(PROCESSED / "style_cluster_profiles.csv"),
        "metrics": _read_csv(PROCESSED / "style_cluster_metric_profiles.csv"),
        "labels": _read_csv(PROCESSED / "style_cluster_labels.csv"),
        "gk_profiles": _read_csv(PROCESSED / "gk_style_cluster_profiles.csv"),
        "gk_metrics": _read_csv(PROCESSED / "gk_style_cluster_metric_profiles.csv"),
        "gk_labels": _read_csv(PROCESSED / "gk_style_cluster_labels.csv"),
    }


def fmt_num(value, digits=1):
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def dark_table(df: pd.DataFrame, score_cols: set[str] | None = None) -> str:
    score_cols = score_cols or set()
    parts = ['<div class="arch-table-wrap"><table class="arch-table">']
    parts.append("<thead><tr>")
    for col in df.columns:
        parts.append(f"<th>{html.escape(str(col))}</th>")
    parts.append("</tr></thead><tbody>")
    for _, row in df.iterrows():
        parts.append("<tr>")
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                txt = "—"
            elif isinstance(val, (int, np.integer)):
                txt = str(int(val))
            elif isinstance(val, (float, np.floating)):
                txt = f"{float(val):.2f}" if abs(float(val)) < 10 and col not in {"n_players"} else f"{float(val):.1f}"
            else:
                txt = str(val)
            if col in score_cols:
                try:
                    color = pct_color(float(val))
                except Exception:
                    color = "#8EA2C6"
                cell = f'<td class="num"><span class="arch-score-pill" style="color:{color};">{html.escape(txt)}</span></td>'
            elif isinstance(val, (int, float, np.integer, np.floating)) and not pd.isna(val):
                cell = f'<td class="num">{html.escape(txt)}</td>'
            else:
                cell = f'<td>{html.escape(txt)}</td>'
            parts.append(cell)
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def apply_cluster_labels(profile_df: pd.DataFrame, labels_df: pd.DataFrame) -> pd.DataFrame:
    """Overwrite Unlabeled cluster names in profile files with FM-like labels."""
    if profile_df.empty or labels_df.empty or "style_cluster_id" not in profile_df.columns:
        return profile_df

    labels = labels_df.copy()
    keep = [
        c for c in [
            "style_cluster_id",
            "style_cluster_name",
            "style_cluster_short_label",
            "description",
            "style_cluster_description",
        ]
        if c in labels.columns
    ]
    labels = labels[keep].drop_duplicates("style_cluster_id")

    if "description" in labels.columns and "style_cluster_description" not in labels.columns:
        labels = labels.rename(columns={"description": "style_cluster_description"})

    out = profile_df.drop(
        columns=[
            "style_cluster_name",
            "style_cluster_short_label",
            "style_cluster_description",
            "description",
        ],
        errors="ignore",
    ).merge(labels, on="style_cluster_id", how="left")

    # Safe fallback only if a cluster has no label at all.
    if "style_cluster_name" not in out.columns:
        out["style_cluster_name"] = out["style_cluster_id"].astype(str)
    out["style_cluster_name"] = out["style_cluster_name"].fillna(out["style_cluster_id"].astype(str))
    if "style_cluster_short_label" not in out.columns:
        out["style_cluster_short_label"] = out["style_cluster_name"]
    out["style_cluster_short_label"] = out["style_cluster_short_label"].fillna(out["style_cluster_name"])
    if "style_cluster_description" not in out.columns:
        out["style_cluster_description"] = ""
    out["style_cluster_description"] = out["style_cluster_description"].fillna("")

    return out


def representative_players_text(player_df: pd.DataFrame, cluster_id: str, max_players: int = 8) -> tuple[str, bool]:
    """Representative players prioritising Big Five leagues for immediate interpretability."""
    if player_df.empty or "style_cluster_id" not in player_df.columns:
        return "", False
    sub = player_df[player_df["style_cluster_id"].astype(str).eq(str(cluster_id))].copy()
    if sub.empty:
        return "", False
    big = sub.loc[is_big_five_mask(sub)].copy() if {"League", "Nation"}.issubset(sub.columns) else pd.DataFrame()
    used_big_five = not big.empty
    if used_big_five:
        sub = big
    sub["_sort_conf"] = pd.to_numeric(sub.get("style_cluster_confidence", -1), errors="coerce").fillna(-1) if "style_cluster_confidence" in sub.columns else -1
    sub["_sort_min"] = pd.to_numeric(sub.get("Minutes played", 0), errors="coerce").fillna(0) if "Minutes played" in sub.columns else 0
    sub = sub.sort_values(["_sort_conf", "_sort_min"], ascending=[False, False]).head(max_players)
    names = []
    for _, row in sub.iterrows():
        player = str(row.get("Player", "Unknown"))
        team = str(row.get("Team", ""))
        league = str(row.get("League", "")) if "League" in row.index and pd.notna(row.get("League")) else ""
        names.append(f"{player} ({team}, {league})" if league else f"{player} ({team})")
    return " | ".join(names), used_big_five


def cluster_cards(profile_df: pd.DataFrame, player_df: pd.DataFrame) -> None:
    cols = st.columns(3)
    for i, (_, row) in enumerate(profile_df.iterrows()):
        desc = row.get("style_cluster_description") or row.get("description") or ""
        reps, reps_big_five = representative_players_text(player_df, str(row.get("style_cluster_id", "")))
        if not reps:
            reps = str(row.get("representative_players", ""))
            reps_big_five = False
        rep_label = "Representative players · Big Five" if reps_big_five else "Representative players"
        parts = []
        parts.append('<div class="arch-card">')
        parts.append('<div class="arch-card-head">')
        parts.append('<div>')
        parts.append(f'<div class="arch-id">{html.escape(str(row.get("style_cluster_id", "")))}</div>')
        parts.append(f'<div class="arch-name">{html.escape(str(row.get("style_cluster_name", "Unlabeled")))}</div>')
        parts.append('</div>')
        parts.append('<div>')
        parts.append(f'<div class="arch-count">{int(row.get("n_players", 0)) if pd.notna(row.get("n_players", np.nan)) else "—"}</div>')
        parts.append('<div class="arch-count-label">players</div>')
        parts.append('</div>')
        parts.append('</div>')
        parts.append(f'<div class="arch-desc">{html.escape(str(desc))}</div>')
        parts.append('<div class="arch-mini-label">Distinctive high</div>')
        parts.append(f'<div class="arch-mini-text">{html.escape(str(row.get("distinctive_high", "—")))}</div>')
        parts.append('<div class="arch-mini-label">Distinctive low</div>')
        parts.append(f'<div class="arch-mini-text">{html.escape(str(row.get("distinctive_low", "—")))}</div>')
        if reps:
            parts.append(f'<div class="arch-mini-label">{html.escape(rep_label)}</div>')
            parts.append(f'<div class="arch-mini-text">{html.escape(reps)}</div>')
        parts.append('</div>')
        with cols[i % 3]:
            st.markdown("".join(parts), unsafe_allow_html=True)


data = load_archetype_data()

role_options = ["CB", "FB", "MF", "AM", "W", "FW", "GK"]
with st.sidebar:
    st.markdown("### Archetype filters")
    role = st.selectbox("Role", role_options, index=0)

if role == "GK":
    profile_df = apply_cluster_labels(data["gk_profiles"].copy(), data["gk_labels"].copy())
    metric_df = data["gk_metrics"].copy()
    player_df = data["gk"].copy()
else:
    profile_df = apply_cluster_labels(data["profiles"].copy(), data["labels"].copy())
    metric_df = data["metrics"].copy()
    player_df = data["players"].copy()

if profile_df.empty or metric_df.empty:
    st.warning("Cluster files non disponibili. Aggiungi i file clustering in data/processed.")
    st.stop()

profile_df = profile_df[profile_df["role_bucket"].astype(str).eq(role)].sort_values("style_cluster_id")
metric_df = metric_df[metric_df["role_bucket"].astype(str).eq(role)]
if role != "GK" and "Role bucket" in player_df.columns:
    player_df = player_df[player_df["Role bucket"].astype(str).eq(role)].copy()
player_df = player_df[player_df["style_cluster_id"].notna()].copy() if "style_cluster_id" in player_df.columns else pd.DataFrame()

st.markdown(
    f"""
<div class="arch-hero">
  <div class="arch-kicker">Style Archetypes</div>
  <div class="arch-title">{html.escape(role)} Archetype Lab</div>
  <div class="arch-subtitle">
    Cluster offline costruiti sulle metriche raw di stile. I nomi sono FM-like e servono come preset scouting, non come giudizio assoluto di qualità.
  </div>
  <div class="arch-pill-row">
    <span class="arch-pill">Role: {html.escape(role)}</span>
    <span class="arch-pill">Clusters: {len(profile_df)}</span>
    <span class="arch-pill">Clustered players: {len(player_df)}</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="arch-section-title">Cluster cards</div>', unsafe_allow_html=True)
cluster_cards(profile_df, player_df)

cluster_options = profile_df["style_cluster_id"].tolist()
selected_cluster = st.selectbox("Cluster detail", cluster_options, format_func=lambda x: f"{x} · {profile_df.loc[profile_df['style_cluster_id'].eq(x), 'style_cluster_name'].iloc[0]}")

st.markdown('<div class="arch-section-title">Cluster map</div>', unsafe_allow_html=True)
if not player_df.empty and {"style_cluster_x", "style_cluster_y"}.issubset(player_df.columns):
    plot_df = player_df.dropna(subset=["style_cluster_x", "style_cluster_y", "style_cluster_id"]).copy()
    if len(plot_df) > 6000:
        plot_df = plot_df.sample(6000, random_state=42)
    base_df = plot_df[~plot_df["style_cluster_id"].eq(selected_cluster)]
    sel_df = plot_df[plot_df["style_cluster_id"].eq(selected_cluster)]
    fig = go.Figure()
    for cid, sub in base_df.groupby("style_cluster_id"):
        name = sub.get("style_cluster_name", pd.Series([cid])).iloc[0]
        fig.add_trace(go.Scatter(
            x=sub["style_cluster_x"], y=sub["style_cluster_y"], mode="markers",
            text=(sub["Player"].astype(str) + "<br>" + sub.get("Team", pd.Series("", index=sub.index)).astype(str) + "<br>" + sub.get("League", pd.Series("", index=sub.index)).astype(str)),
            hovertemplate="%{text}<extra></extra>",
            marker=dict(size=9, color="rgba(16,22,43,0.65)", line=dict(color="rgba(95,255,224,0.52)", width=1.5), opacity=0.70),
            name=str(name),
        ))
    if not sel_df.empty:
        fig.add_trace(go.Scatter(
            x=sel_df["style_cluster_x"], y=sel_df["style_cluster_y"], mode="markers",
            text=(sel_df["Player"].astype(str) + "<br>" + sel_df.get("Team", pd.Series("", index=sel_df.index)).astype(str) + "<br>" + sel_df.get("League", pd.Series("", index=sel_df.index)).astype(str)),
            hovertemplate="%{text}<extra></extra>",
            marker=dict(size=12, color="#5FFFE0", line=dict(color="#070A18", width=2.3), opacity=0.95),
            name="Selected cluster",
        ))
    fig.update_layout(
        template="plotly_dark", height=620, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,16,36,0.45)",
        font=dict(color="#F6F7FB"), legend=dict(font=dict(color="#DDE8FF")), margin=dict(l=30, r=30, t=30, b=30),
        xaxis=dict(title="Style component 1", gridcolor="rgba(255,255,255,0.10)", zerolinecolor="rgba(255,255,255,0.12)"),
        yaxis=dict(title="Style component 2", gridcolor="rgba(255,255,255,0.10)", zerolinecolor="rgba(255,255,255,0.12)"),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Coordinate cluster non disponibili.")
