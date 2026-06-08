from __future__ import annotations

import html
import math
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.competition_utils import filter_big_five
from src.data_loader import available_seasons, load_players_enriched
from src.metric_catalog import ROLE_BUCKETS
from src.ui import inject_css, pct_color

st.set_page_config(page_title="Player Finder", page_icon="🔎", layout="wide")
inject_css()

st.markdown(
    """
<style>
.finder-hero {
    border:1px solid rgba(95,255,224,0.20);
    background: radial-gradient(circle at top left, rgba(95,255,224,0.13), transparent 34%),
                linear-gradient(115deg, rgba(16,22,43,0.92), rgba(33,21,60,0.72));
    border-radius:26px;
    padding:30px 32px;
    margin:0.8rem 0 1.5rem 0;
    box-shadow:0 18px 62px rgba(0,0,0,0.30), inset 0 0 26px rgba(95,255,224,0.04);
}
.finder-kicker {color:#5FFFE0;font-size:0.82rem;font-weight:950;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:10px;}
.finder-title {color:#F8FBFF;font-size:3rem;line-height:1;font-weight:950;letter-spacing:-0.04em;text-shadow:0 0 18px rgba(95,255,224,0.18);margin-bottom:12px;}
.finder-subtitle {color:#B7CAE8;font-size:1.02rem;line-height:1.55;max-width:1160px;font-weight:650;}
.finder-pill-row {display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.finder-pill {
    display:inline-flex;align-items:center;min-height:28px;padding:0 11px;border-radius:999px;
    border:1px solid rgba(95,255,224,0.24);background:rgba(95,255,224,0.08);
    color:#DDE8FF;font-size:0.76rem;font-weight:850;
}
.finder-section-title {color:#F6F7FB;font-size:1.55rem;font-weight:950;letter-spacing:-0.03em;margin:1.4rem 0 0.85rem 0;}
.finder-profile-card {
    border:1px solid rgba(95,255,224,0.18);
    background:rgba(16,22,43,0.78);
    border-radius:22px;
    padding:18px 20px;
    margin-bottom:14px;
    box-shadow:0 14px 44px rgba(0,0,0,0.22);
}
.finder-profile-name {color:#5FFFE0;font-size:1.25rem;font-weight:950;letter-spacing:-0.02em;}
.finder-profile-meta {color:#AFC3E8;font-size:0.86rem;font-weight:700;margin-top:4px;line-height:1.45;}
.finder-family-card {
    border:1px solid rgba(95,255,224,0.16);
    background:rgba(10,16,36,0.72);
    border-radius:20px;
    padding:14px 16px;
    margin-bottom:12px;
}
.finder-family-title {display:flex;justify-content:space-between;gap:12px;align-items:flex-start;color:#F6F7FB;font-size:1.02rem;font-weight:950;}
.finder-family-desc {color:#8EA2C6;font-size:0.80rem;line-height:1.38;font-weight:650;margin:4px 0 10px 0;}
.finder-family-score {
    display:inline-flex;align-items:center;justify-content:center;min-width:54px;height:30px;border-radius:999px;
    border:1px solid rgba(95,255,224,0.28);background:rgba(95,255,224,0.08);color:#5FFFE0;font-size:0.82rem;font-weight:950;
}
.finder-card {
    border:1px solid rgba(95,255,224,0.15);
    background:rgba(16,22,43,0.80);
    border-radius:22px;
    padding:16px 18px;
    margin-bottom:12px;
    box-shadow:0 14px 44px rgba(0,0,0,0.20);
}
.finder-card-top {display:grid;grid-template-columns:46px minmax(0,1fr) 118px;gap:14px;align-items:center;}
.finder-rank {color:#B7CAE8;font-weight:950;text-align:center;font-size:1.1rem;}
.finder-name {color:#F6F7FB;font-size:1.15rem;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.finder-meta {color:#8EA2C6;font-size:0.82rem;font-weight:750;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.finder-fit-pill {
    display:inline-flex;align-items:center;justify-content:center;min-width:84px;height:36px;border-radius:999px;
    border:1px solid rgba(95,255,224,0.35);background:rgba(95,255,224,0.10);
    color:#5FFFE0;font-weight:950;font-size:0.92rem;
}
.finder-detail-grid {display:grid;grid-template-columns:repeat(3, minmax(0,1fr));gap:7px;margin-top:12px;}
.finder-chip {
    display:flex;align-items:center;justify-content:space-between;gap:8px;
    background:rgba(10,16,36,0.58);border:1px solid rgba(255,255,255,0.06);
    border-radius:12px;padding:7px 9px;color:#B7CAE8;font-size:0.76rem;font-weight:750;
}
.finder-chip strong {color:#F6F7FB;font-weight:950;}
.finder-chip-pass {border-color:rgba(95,255,224,0.22);background:rgba(95,255,224,0.06);}
.finder-chip-fail {border-color:rgba(255,79,109,0.22);background:rgba(255,79,109,0.055);}
.finder-warning {
    display:inline-flex;margin:8px 6px 0 0;padding:5px 9px;border-radius:999px;
    background:rgba(255,229,92,0.10);border:1px solid rgba(255,229,92,0.20);
    color:#FFE55C;font-size:0.72rem;font-weight:850;
}
.finder-table-wrap {
    width:100%;overflow-x:auto;border:1px solid rgba(95,255,224,0.18);border-radius:18px;
    background:rgba(10,16,36,0.78);box-shadow:0 14px 44px rgba(0,0,0,0.22);margin:0.8rem 0 1.2rem 0;
}
.finder-table {width:100%;border-collapse:collapse;color:#F6F7FB;font-size:0.84rem;}
.finder-table th {
    background:#10162B;color:#AFC3E8;text-align:left;padding:11px 10px;
    font-size:0.72rem;font-weight:950;letter-spacing:0.06em;text-transform:uppercase;
    border-bottom:1px solid rgba(95,255,224,0.18);
}
.finder-table td {padding:9px 10px;border-bottom:1px solid rgba(255,255,255,0.055);background:rgba(16,22,43,0.72);}
.finder-table tr:nth-child(even) td {background:rgba(12,18,38,0.78);}
.finder-table .num {text-align:right;font-variant-numeric:tabular-nums;font-weight:850;}
.metric-help {
    color:#8EA2C6;font-size:0.78rem;line-height:1.35;margin-top:4px;
}
.metric-dist-card {
    border:1px solid rgba(95,255,224,0.14);
    background:rgba(10,16,36,0.62);
    border-radius:20px;
    padding:14px 16px;
    margin:12px 0 18px 0;
}
.metric-dist-title {color:#F6F7FB;font-size:1rem;font-weight:950;}
.metric-dist-meta {color:#AFC3E8;font-size:0.80rem;font-weight:700;margin-top:3px;}
@media (max-width:1100px) {
    .finder-card-top {grid-template-columns:34px minmax(0,1fr) 86px;}
    .finder-detail-grid {grid-template-columns:1fr;}
}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------------
# Metric library
# -------------------------------------------------------------------------

MetricSpec = dict[str, Any]


def metric(metric_name: str, direction: str = "min", q: float = 0.60, label: str | None = None) -> MetricSpec:
    return {"metric": metric_name, "direction": direction, "q": q, "label": label or metric_name}


FAMILY_LIBRARY: dict[str, dict[str, Any]] = {
    # Defensive / CB oriented
    "First build-up": {
        "description": "Prima costruzione: volume, accuratezza e capacità di uscire dal primo possesso.",
        "metrics": [
            metric("Passes", "min", 0.60),
            metric("Passes accurate, %", "min", 0.50),
            metric("Short passes", "min", 0.55),
            metric("Short passes accurate, %", "min", 0.50),
            metric("Long passes", "min", 0.55),
            metric("Long passes accurate, %", "min", 0.45),
            metric("Progressive open passes", "min", 0.55),
            metric("Lost balls after passes", "max", 0.70),
        ],
    },
    "Progressive passing": {
        "description": "Progressione via passaggio: porta palla o squadra in avanti senza essere solo un riciclatore.",
        "metrics": [
            metric("Progressive passes", "min", 0.60),
            metric("Progressive passes accurate, %", "min", 0.45),
            metric("Passes forward to the final third", "min", 0.60),
            metric("Passes forward to the final third accurate, %", "min", 0.45),
            metric("Final third entries through pass", "min", 0.55),
            metric("Passes into the penalty box", "min", 0.45),
        ],
    },
    "Defend forward": {
        "description": "Difendere in avanti: aggressione, anticipo, recuperi alti e duelli difensivi.",
        "metrics": [
            metric("Defensive challenges", "min", 0.60),
            metric("Defensive challenges won, %", "min", 0.45),
            metric("Tackles", "min", 0.55),
            metric("Tackles successful, %", "min", 0.45),
            metric("Interceptions", "min", 0.60),
            metric("Ball recoveries", "min", 0.55),
            metric("Ball recoveries in opponent's half", "min", 0.55),
        ],
    },
    "Recovery defending proxies": {
        "description": "Proxy per difendere campo alle spalle. Non ci sono speed/sprint: uso sicurezza difensiva, duelli vinti e rischio basso.",
        "metrics": [
            metric("Defensive challenges won, %", "min", 0.55),
            metric("Tackles successful, %", "min", 0.55),
            metric("Challenges won, %", "min", 0.50),
            metric("Air challenges won, %", "min", 0.50),
            metric("Mistakes leading to chances", "max", 0.70),
            metric("Mistakes leading to goals", "max", 0.70),
            metric("Lost balls in own half", "max", 0.65),
        ],
    },
    "Aerial / physical duels": {
        "description": "Corpo, contatto e volume di duelli: utile per centrali, quinti e punte.",
        "metrics": [
            metric("Challenges", "min", 0.55),
            metric("Challenges won, %", "min", 0.50),
            metric("Air challenges", "min", 0.55),
            metric("Air challenges won, %", "min", 0.50),
            metric("Defensive challenges", "min", 0.50),
            metric("Attacking challenges", "min", 0.50),
            metric("Height", "min", 0.45),
        ],
    },
    "Ball security": {
        "description": "Non perdere palloni pericolosi: sicurezza tecnica e controllo.",
        "metrics": [
            metric("Actions successful, %", "min", 0.50),
            metric("Passes accurate, %", "min", 0.50),
            metric("Lost balls", "max", 0.65),
            metric("Lost balls in own half", "max", 0.65),
            metric("Bad ball control", "max", 0.65),
            metric("Individual ball losses", "max", 0.65),
        ],
    },
    "Final third defending / support": {
        "description": "Per difensori moderni: recuperi, ingressi e presenza utile nell’ultimo terzo.",
        "metrics": [
            metric("Ball recoveries in opponent's half", "min", 0.55),
            metric("Final third entries", "min", 0.55),
            metric("Final third entries through pass", "min", 0.55),
            metric("Passes forward to the final third", "min", 0.55),
            metric("Passes into the penalty box", "min", 0.45),
            metric("Crosses", "min", 0.45),
        ],
    },
    # Midfield / AM / W
    "Tempo control": {
        "description": "Volume, ricezioni e continuità nel possesso.",
        "metrics": [
            metric("Passes", "min", 0.60),
            metric("Passes accurate, %", "min", 0.50),
            metric("Open passes received", "min", 0.60),
            metric("Open passes received in the central third", "min", 0.55),
            metric("Short passes", "min", 0.55),
            metric("Progressive open passes", "min", 0.50),
        ],
    },
    "Chance creation": {
        "description": "Creare occasioni: ultimo passaggio, xA e rifinitura.",
        "metrics": [
            metric("xA", "min", 0.60),
            metric("Key passes", "min", 0.60),
            metric("Key passes accurate, %", "min", 0.45),
            metric("Passes for a shot", "min", 0.60),
            metric("Chances created", "min", 0.60),
            metric("Passes into the penalty box", "min", 0.55),
        ],
    },
    "Carrying / 1v1": {
        "description": "Progressione palla al piede, 1v1 e conduzioni nell’ultimo terzo.",
        "metrics": [
            metric("Carry", "min", 0.55),
            metric("Final third entries through carry", "min", 0.55),
            metric("Dribbles", "min", 0.60),
            metric("Dribbles successful, %", "min", 0.45),
            metric("Dribbling in the final third", "min", 0.55),
            metric("Dribbling in the final third successful, %", "min", 0.45),
        ],
    },
    "Wide delivery": {
        "description": "Ampiezza, cross e rifinitura da fascia.",
        "metrics": [
            metric("Crosses", "min", 0.60),
            metric("Crosses accurate, %", "min", 0.45),
            metric("Passes into the penalty box", "min", 0.55),
            metric("Passes into the penalty box accurate, %", "min", 0.45),
            metric("Final third entries", "min", 0.55),
            metric("Open passes received in the final third", "min", 0.50),
        ],
    },
    # Forward oriented
    "Area occupation": {
        "description": "Vivere dentro/attorno all’area: presenza, ricezioni e volume ad alto valore.",
        "metrics": [
            metric("Actions in opponent's box", "min", 0.60),
            metric("Open passes received in the opponent's box", "min", 0.60),
            metric("Shots from the penalty area", "min", 0.60),
            metric("xG (expected goals)", "min", 0.60),
            metric("xGPS (xG per shot)", "min", 0.55),
        ],
    },
    "Box threat": {
        "description": "Minaccia realizzativa: volume, precisione e qualità del tiro.",
        "metrics": [
            metric("Goals", "min", 0.55),
            metric("Shots", "min", 0.60),
            metric("Shots on target", "min", 0.60),
            metric("Shots on target, %", "min", 0.50),
            metric("xGC (xG conversion)", "min", 0.50),
            metric("Shots on target from the penalty area, %", "min", 0.45),
        ],
    },
    "Contact / hold-up": {
        "description": "Reggere il contatto, duellare e non sparire contro difensori fisici.",
        "metrics": [
            metric("Attacking challenges", "min", 0.60),
            metric("Attacking challenges won, %", "min", 0.45),
            metric("Air challenges", "min", 0.55),
            metric("Air challenges won, %", "min", 0.45),
            metric("Challenges", "min", 0.50),
            metric("Fouls suffered", "min", 0.45),
        ],
    },
    "Transition threat": {
        "description": "Ricevere lungo, portare campo e attaccare transizioni.",
        "metrics": [
            metric("Long open passes received", "min", 0.55),
            metric("Super long open passes received", "min", 0.45),
            metric("Carry", "min", 0.50),
            metric("Final third entries", "min", 0.50),
            metric("Final third entries through carry", "min", 0.50),
            metric("Shots from outside the penalty area", "min", 0.45),
            metric("Lost balls in own half", "max", 0.65),
        ],
    },
    "Link-up survival": {
        "description": "Raccordo minimo: venire incontro senza far morire l’azione.",
        "metrics": [
            metric("Passes", "min", 0.45),
            metric("Passes accurate, %", "min", 0.40),
            metric("Short passes accurate, %", "min", 0.40),
            metric("Progressive passes accurate, %", "min", 0.35),
            metric("Passes for a shot", "min", 0.45),
            metric("Key passes", "min", 0.45),
            metric("xA", "min", 0.40),
        ],
    },
}


ROLE_DEFAULT_FAMILIES: dict[str, list[str]] = {
    "CB": [
        "First build-up",
        "Progressive passing",
        "Defend forward",
        "Recovery defending proxies",
        "Aerial / physical duels",
        "Ball security",
        "Final third defending / support",
    ],
    "FB": [
        "Progressive passing",
        "Defend forward",
        "Wide delivery",
        "Carrying / 1v1",
        "Ball security",
        "Final third defending / support",
    ],
    "MF": [
        "Tempo control",
        "Progressive passing",
        "Defend forward",
        "Chance creation",
        "Ball security",
        "Carrying / 1v1",
    ],
    "AM": [
        "Chance creation",
        "Tempo control",
        "Area occupation",
        "Carrying / 1v1",
        "Box threat",
        "Ball security",
    ],
    "W": [
        "Carrying / 1v1",
        "Wide delivery",
        "Area occupation",
        "Chance creation",
        "Transition threat",
        "Defend forward",
    ],
    "FW": [
        "Area occupation",
        "Box threat",
        "Contact / hold-up",
        "Transition threat",
        "Link-up survival",
        "Ball security",
    ],
}

PRESETS: dict[str, dict[str, Any]] = {
    "Inter CB — build-up + defend high": {
        "role": "CB",
        "description": "Centrale per squadra alta: prima costruzione, progressione, difesa in avanti e proxy di difesa campo alle spalle.",
        "families": {
            "First build-up": 0.25,
            "Progressive passing": 0.20,
            "Defend forward": 0.22,
            "Recovery defending proxies": 0.18,
            "Aerial / physical duels": 0.10,
            "Ball security": 0.05,
        },
        "mode_note": "Non ci sono dati di speed/sprint/backpedal: la parte 'correre all’indietro' è stimata con proxy di sicurezza difensiva, errori bassi e duelli vinti.",
    },
    "Juve 9 Fit": {
        "role": "FW",
        "description": "9 che trasformi progressione in presenza d’area: area, contatto, attacco porta e raccordo sufficiente.",
        "families": {
            "Area occupation": 0.25,
            "Box threat": 0.20,
            "Contact / hold-up": 0.20,
            "Transition threat": 0.15,
            "Link-up survival": 0.15,
            "Ball security": 0.05,
        },
        "mode_note": "Profilo bersaglio: non il migliore in assoluto, ma il più compatibile con un bisogno tattico specifico.",
    },
    "Role-based broad fit": {
        "role": None,
        "description": "Profilo ampio basato sul ruolo selezionato.",
        "families": None,
        "mode_note": "Usa famiglie ampie e personalizzabili per il ruolo scelto.",
    },
    "Custom": {
        "role": None,
        "description": "Parti da zero: scegli famiglie, metriche e soglie.",
        "families": {},
        "mode_note": "Modalità libera.",
    },
}


def txt(value, fallback="—") -> str:
    if pd.isna(value):
        return fallback
    value = str(value)
    return fallback if value in {"", "nan", "None", "<NA>"} else value


def fmt_num(value, decimals=2) -> str:
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return str(value)


def fmt_int(value) -> str:
    if pd.isna(value):
        return "—"
    try:
        return f"{float(value):,.0f}".replace(",", ".")
    except Exception:
        return str(value)


def has_col(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns and pd.to_numeric(df[col], errors="coerce").notna().sum() > 0


def available_metric_specs(df: pd.DataFrame, specs: list[MetricSpec]) -> list[MetricSpec]:
    return [s for s in specs if has_col(df, s["metric"])]


def all_competitions(data: pd.DataFrame) -> list[str]:
    if "League" not in data.columns:
        return []
    if "Nation" in data.columns:
        tmp = data[["League", "Nation"]].dropna().drop_duplicates()
        tmp["label"] = tmp["League"].astype(str) + " · " + tmp["Nation"].astype(str)
        return sorted(tmp["label"].unique().tolist())
    return sorted(data["League"].dropna().astype(str).unique().tolist())


def comp_filter(data: pd.DataFrame, label: str) -> pd.Series:
    if "League" not in data.columns:
        return pd.Series(False, index=data.index)
    if " · " in label and "Nation" in data.columns:
        league, nation = label.split(" · ", 1)
        return data["League"].astype(str).eq(league) & data["Nation"].astype(str).eq(nation)
    return data["League"].astype(str).eq(label)


def apply_scope(data: pd.DataFrame, scope: str, selected_comp: str | None, custom_comps: list[str]) -> pd.DataFrame:
    if scope == "Big Five":
        return filter_big_five(data)
    if scope == "Single competition" and selected_comp:
        return data[comp_filter(data, selected_comp)].copy()
    if scope == "Custom competitions" and custom_comps:
        mask = pd.Series(False, index=data.index)
        for comp in custom_comps:
            mask = mask | comp_filter(data, comp)
        return data[mask].copy()
    return data.copy()


def default_threshold(reference: pd.DataFrame, spec: MetricSpec, strictness: str) -> float:
    metric_name = spec["metric"]
    values = pd.to_numeric(reference.get(metric_name), errors="coerce").dropna()
    if values.empty:
        return 0.0

    base_q = float(spec.get("q", 0.60))
    if strictness == "Strict":
        base_q = min(0.82, base_q + 0.10) if spec["direction"] == "min" else min(0.82, base_q + 0.08)
    elif strictness == "Exploratory":
        base_q = max(0.35, base_q - 0.12) if spec["direction"] == "min" else max(0.35, base_q - 0.10)

    return float(values.quantile(base_q))


def pass_criterion(value: Any, threshold: float, direction: str) -> bool:
    if pd.isna(value):
        return False
    try:
        value = float(value)
    except Exception:
        return False
    if direction == "max":
        return value <= threshold
    return value >= threshold


def metric_percentile(reference: pd.DataFrame, values: pd.Series, metric_name: str, direction: str) -> pd.Series:
    ref = pd.to_numeric(reference.get(metric_name), errors="coerce").dropna()
    values = pd.to_numeric(values, errors="coerce")
    if ref.empty:
        return pd.Series(np.nan, index=values.index)

    # Percentile by empirical CDF.
    sorted_ref = np.sort(ref.to_numpy(dtype=float))
    pct = np.searchsorted(sorted_ref, values.to_numpy(dtype=float), side="right") / len(sorted_ref) * 100
    pct = pd.Series(pct, index=values.index)
    pct[values.isna()] = np.nan
    if direction == "max":
        pct = 100 - pct
    return pct.clip(0, 100)


def threshold_percentile(reference: pd.DataFrame, metric_name: str, threshold: float, direction: str) -> float:
    ref = pd.to_numeric(reference.get(metric_name), errors="coerce").dropna()
    if ref.empty or pd.isna(threshold):
        return float("nan")
    pct = (ref <= float(threshold)).mean() * 100
    if direction == "max":
        pct = 100 - pct
    return float(pct)


def style_label(row: pd.Series) -> str:
    return txt(
        row.get("style_cluster_short_label"),
        txt(row.get("style_cluster_name"), txt(row.get("style_cluster_id"), "Unclustered")),
    )


def render_distribution(reference: pd.DataFrame, candidates: pd.DataFrame, metric_name: str, threshold: float, direction: str, anchor_row: pd.Series | None = None) -> None:
    ref_values = pd.to_numeric(reference.get(metric_name), errors="coerce").dropna()
    cand_values = pd.to_numeric(candidates.get(metric_name), errors="coerce").dropna()
    if ref_values.empty:
        st.info("Distribuzione non disponibile per questa metrica.")
        return

    remaining = int((cand_values >= threshold).sum()) if direction == "min" else int((cand_values <= threshold).sum())
    total = int(cand_values.shape[0])
    pct_thr = threshold_percentile(reference, metric_name, threshold, direction)
    sign = "≥" if direction == "min" else "≤"

    st.markdown(
        f"""
<div class="metric-dist-card">
  <div class="metric-dist-title">{html.escape(metric_name)}</div>
  <div class="metric-dist-meta">
    Soglia {sign} {fmt_num(threshold)} · threshold percentile ≈ {fmt_num(pct_thr, 0)} · candidati rimasti {remaining}/{total}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=ref_values,
            nbinsx=42,
            name="Reference pool",
            marker=dict(color="rgba(95,255,224,0.28)", line=dict(color="rgba(95,255,224,0.55)", width=1)),
            opacity=0.88,
        )
    )
    if not cand_values.empty:
        fig.add_trace(
            go.Histogram(
                x=cand_values,
                nbinsx=42,
                name="Current candidates",
                marker=dict(color="rgba(255,229,92,0.25)", line=dict(color="rgba(255,229,92,0.55)", width=1)),
                opacity=0.55,
            )
        )
    fig.add_vline(x=float(threshold), line_width=3, line_dash="dash", line_color="#5FFFE0")
    if anchor_row is not None and metric_name in anchor_row.index and pd.notna(anchor_row.get(metric_name)):
        fig.add_vline(x=float(anchor_row.get(metric_name)), line_width=3, line_dash="dot", line_color="#FF4F6D")
    fig.update_layout(
        template="plotly_dark",
        height=330,
        barmode="overlay",
        margin=dict(l=20, r=20, t=20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,16,36,0.45)",
        font=dict(color="#F6F7FB"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="Players"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_table(df: pd.DataFrame) -> str:
    parts = ['<div class="finder-table-wrap"><table class="finder-table">']
    parts.append("<thead><tr>")
    for col in df.columns:
        parts.append(f"<th>{html.escape(str(col))}</th>")
    parts.append("</tr></thead><tbody>")
    for _, row in df.iterrows():
        parts.append("<tr>")
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                out = "—"
            elif isinstance(value, (float, np.floating)):
                out = f"{float(value):.1f}" if "Score" in col or "score" in col or "pct" in col.lower() else f"{float(value):.2f}"
            else:
                out = str(value)
            cls = "num" if isinstance(value, (int, float, np.integer, np.floating)) and not pd.isna(value) else ""
            parts.append(f'<td class="{cls}">{html.escape(out)}</td>')
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def render_cards(df: pd.DataFrame, criteria: list[MetricSpec], active_family_names: list[str], title: str, limit: int = 12) -> None:
    st.markdown(f'<div class="finder-section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("Nessun giocatore in questa sezione.")
        return

    for rank, (_, row) in enumerate(df.head(limit).iterrows(), start=1):
        score = float(row.get("Finder Score", np.nan))
        match = int(row.get("criteria_matched", 0))
        total = int(row.get("criteria_total", 0))
        score_color = pct_color(score) if not pd.isna(score) else "#8EA2C6"
        meta = (
            f"{fmt_int(row.get('Age'))} yrs · {txt(row.get('Position'))} · "
            f"{txt(row.get('Team'))} · {txt(row.get('League'))} · {style_label(row)}"
        )
        chips = []
        for family in active_family_names[:6]:
            val = row.get(f"{family} score", np.nan)
            chips.append(
                f'<div class="finder-chip">'
                f'<span>{html.escape(family)}</span>'
                f'<strong style="color:{pct_color(val) if not pd.isna(val) else "#8EA2C6"};">{fmt_num(val, 0)}</strong>'
                f'</div>'
            )

        if len(chips) < 6:
            for criterion in criteria[: 6 - len(chips)]:
                metric_name = criterion["metric"]
                value = row.get(metric_name, np.nan)
                threshold = criterion["threshold"]
                direction = criterion["direction"]
                passed = pass_criterion(value, threshold, direction)
                sign = "≥" if direction == "min" else "≤"
                chips.append(
                    f'<div class="finder-chip {"finder-chip-pass" if passed else "finder-chip-fail"}">'
                    f'<span>{html.escape(metric_name)}</span>'
                    f'<strong>{fmt_num(value)} {sign} {fmt_num(threshold)}</strong>'
                    f'</div>'
                )

        warnings = str(row.get("Profile warning", "") or "")
        warn_html = "".join([f'<span class="finder-warning">{html.escape(w.strip())}</span>' for w in warnings.split(";") if w.strip()])

        st.markdown(
            f"""
<div class="finder-card">
  <div class="finder-card-top">
    <div class="finder-rank">{rank}</div>
    <div>
      <div class="finder-name">{html.escape(txt(row.get("Player")))}</div>
      <div class="finder-meta">{html.escape(meta)}</div>
    </div>
    <div><span class="finder-fit-pill" style="color:{score_color};border-color:{score_color}80;">{fmt_num(score, 0)}</span></div>
  </div>
  <div class="finder-detail-grid">
    {''.join(chips)}
  </div>
  <div>{warn_html}</div>
</div>
""",
            unsafe_allow_html=True,
        )


def profile_warnings(row: pd.Series, role: str) -> str:
    warnings: list[str] = []
    if role == "CB":
        if row.get("First build-up score", 50) >= 70 and row.get("Recovery defending proxies score", 50) < 45:
            warnings.append("build-up CB, recovery proxy weak")
        if row.get("Defend forward score", 50) >= 70 and row.get("Ball security score", 50) < 45:
            warnings.append("aggressive but risky on ball")
        if row.get("Progressive passing score", 50) >= 70 and row.get("Aerial / physical duels score", 50) < 40:
            warnings.append("progressor, less physical")
        if row.get("Defend forward score", 50) >= 65 and row.get("Recovery defending proxies score", 50) >= 60:
            warnings.append("good high-line defensive proxy")
    elif role == "FW":
        if row.get("Area occupation score", 50) >= 70 and row.get("Link-up survival score", 50) < 40:
            warnings.append("box presence but poor link-up")
        if row.get("Link-up survival score", 50) >= 70 and row.get("Contact / hold-up score", 50) < 45:
            warnings.append("too clean / low contact")
        if row.get("Transition threat score", 50) >= 70 and row.get("Area occupation score", 50) < 45:
            warnings.append("transition striker, not box striker")
        if row.get("Area occupation score", 50) >= 60 and row.get("Contact / hold-up score", 50) >= 55 and row.get("Link-up survival score", 50) >= 45:
            warnings.append("good fit: area + contact + enough link-up")
    else:
        if row.get("Ball security score", 50) < 35:
            warnings.append("technical security risk")
        if row.get("Chance creation score", 50) >= 70:
            warnings.append("creative profile")
        if row.get("Carrying / 1v1 score", 50) >= 70:
            warnings.append("carry/1v1 profile")
    return "; ".join(warnings)


# -------------------------------------------------------------------------
# Data and sidebar
# -------------------------------------------------------------------------

df = load_players_enriched()

st.markdown(
    """
<div class="finder-hero">
  <div class="finder-kicker">Profile-based scouting filter</div>
  <div class="finder-title">Player Finder</div>
  <div class="finder-subtitle">
    Costruisci un profilo bersaglio usando famiglie di metriche ampie, soglie raw, distribuzioni e un eventuale giocatore-ancora.
    È pensato per domande tipo: “cerco un centrale per l’Inter che costruisca bene, difenda in avanti e regga campo alle spalle”.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Finder setup")
    seasons = available_seasons(df)
    season = st.selectbox("Season", seasons, index=0)
    season_df = df[df["Season"].astype(str).eq(str(season))].copy()

    preset_name = st.selectbox("Profile template", list(PRESETS.keys()), index=0)
    preset = PRESETS[preset_name]

    role_options = [r for r in ["CB", "FB", "MF", "AM", "W", "FW"] if r in ROLE_BUCKETS]
    default_role = preset["role"] if preset.get("role") in role_options else "CB"
    role = st.selectbox("Target role", role_options, index=role_options.index(default_role))

    scope = st.selectbox("Candidate scope", ["All leagues", "Big Five", "Single competition", "Custom competitions"], index=1)
    comps = all_competitions(season_df)
    selected_comp = None
    custom_comps: list[str] = []
    if scope == "Single competition":
        selected_comp = st.selectbox("Competition", comps)
    elif scope == "Custom competitions":
        custom_comps = st.multiselect("Custom competitions", comps, default=[])

    min_minutes = st.number_input("Minimum minutes", min_value=0, max_value=4000, value=900, step=100)
    age_cols = st.columns(2)
    with age_cols[0]:
        min_age = st.number_input("Min age", min_value=14, max_value=45, value=18, step=1, key="finder_min_age")
    with age_cols[1]:
        max_age = st.number_input("Max age", min_value=14, max_value=45, value=32, step=1, key="finder_max_age")

    st.markdown("---")
    st.markdown("### Anchor / cluster")
    role_base_for_anchor = season_df[season_df["Role bucket"].astype(str).eq(role)].copy()
    anchor_pool = apply_scope(role_base_for_anchor, scope, selected_comp, custom_comps)
    anchor_pool = anchor_pool[pd.to_numeric(anchor_pool.get("Minutes played"), errors="coerce").fillna(0) >= int(min_minutes)]
    anchor_options = ["No anchor"]
    if not anchor_pool.empty:
        anchor_pool = anchor_pool.sort_values(["League", "Team", "Player"], na_position="last")
        anchor_options += [
            f"{r.Player} · {r.Team} · {r.League} · {r.Position}"
            for r in anchor_pool[["Player", "Team", "League", "Position"]].itertuples(index=False)
        ]
    anchor_choice = st.selectbox("Start from player", anchor_options, index=0)
    anchor_row = None
    if anchor_choice != "No anchor":
        anchor_name, anchor_team, anchor_league, *_ = anchor_choice.split(" · ")
        match = anchor_pool[
            anchor_pool["Player"].astype(str).eq(anchor_name)
            & anchor_pool["Team"].astype(str).eq(anchor_team)
            & anchor_pool["League"].astype(str).eq(anchor_league)
        ]
        if not match.empty:
            anchor_row = match.iloc[0]

    cluster_mode = st.selectbox("Cluster filter", ["All clusters", "Same as anchor", "Manual clusters"], index=0)
    role_clusters = (
        role_base_for_anchor[["style_cluster_id", "style_cluster_name"]]
        .dropna()
        .drop_duplicates()
        .sort_values("style_cluster_id")
    )
    cluster_ids = role_clusters["style_cluster_id"].astype(str).tolist() if not role_clusters.empty else []
    manual_clusters: list[str] = []
    if cluster_mode == "Manual clusters":
        manual_clusters = st.multiselect("Clusters", cluster_ids, default=[])
    elif cluster_mode == "Same as anchor" and anchor_row is None:
        st.caption("Seleziona un anchor player per usare il suo cluster.")

    st.markdown("---")
    strictness = st.selectbox("Threshold mode", ["Balanced", "Strict", "Exploratory"], index=0)
    anchor_weight = st.slider("Anchor similarity weight", min_value=0, max_value=60, value=20 if anchor_row is not None else 0, step=5) / 100


# -------------------------------------------------------------------------
# Candidate and reference pools
# -------------------------------------------------------------------------

role_pool = season_df[season_df["Role bucket"].astype(str).eq(role)].copy()
role_pool = role_pool[pd.to_numeric(role_pool.get("Minutes played"), errors="coerce").fillna(0) >= int(min_minutes)]
reference_pool = apply_scope(role_pool, scope, selected_comp, custom_comps)
candidate_pool = reference_pool.copy()
candidate_pool = candidate_pool[pd.to_numeric(candidate_pool.get("Age"), errors="coerce").between(min_age, max_age, inclusive="both")]

if cluster_mode == "Same as anchor" and anchor_row is not None and pd.notna(anchor_row.get("style_cluster_id")):
    candidate_pool = candidate_pool[candidate_pool["style_cluster_id"].astype(str).eq(str(anchor_row.get("style_cluster_id")))]
elif cluster_mode == "Manual clusters" and manual_clusters:
    candidate_pool = candidate_pool[candidate_pool["style_cluster_id"].astype(str).isin(manual_clusters)]

# Exclude anchor itself from results.
if anchor_row is not None:
    candidate_pool = candidate_pool.drop(index=[anchor_row.name], errors="ignore")

if reference_pool.empty or candidate_pool.empty:
    st.warning("Reference pool o candidate pool vuoto. Allarga campionati, età o minuti.")
    st.stop()

# -------------------------------------------------------------------------
# Family selection and thresholds
# -------------------------------------------------------------------------

preset_families = preset.get("families")
if preset_families is None:
    preset_families = {fam: 1 / max(len(ROLE_DEFAULT_FAMILIES.get(role, [])), 1) for fam in ROLE_DEFAULT_FAMILIES.get(role, [])}

default_family_names = [f for f in preset_families.keys() if f in FAMILY_LIBRARY]
if not default_family_names:
    default_family_names = ROLE_DEFAULT_FAMILIES.get(role, list(FAMILY_LIBRARY.keys())[:4])

st.markdown(
    f"""
<div class="finder-profile-card">
  <div class="finder-profile-name">{html.escape(preset_name)}</div>
  <div class="finder-profile-meta">
    Role {html.escape(role)} · season {html.escape(str(season))} · reference n={len(reference_pool)} · candidates n={len(candidate_pool)}
    <br>{html.escape(str(preset.get("description", "")))}
    <br>{html.escape(str(preset.get("mode_note", "")))}
  </div>
</div>
""",
    unsafe_allow_html=True,
)

all_family_names = list(FAMILY_LIBRARY.keys())
active_family_names = st.multiselect(
    "Metric families",
    all_family_names,
    default=default_family_names,
    help="Scegli famiglie ampie. Ogni famiglia contiene più metriche raw, modificabili sotto.",
)

if not active_family_names:
    st.warning("Seleziona almeno una famiglia.")
    st.stop()

active_criteria: list[MetricSpec] = []
family_weights: dict[str, float] = {}
family_metrics: dict[str, list[MetricSpec]] = {}

with st.expander("Metric families, weights and thresholds", expanded=True):
    st.caption("Le soglie sono raw. A destra puoi aggiungere/togliere metriche nella famiglia; sotto puoi controllare la distribuzione.")
    for family_name in active_family_names:
        family = FAMILY_LIBRARY[family_name]
        specs = available_metric_specs(reference_pool, family["metrics"])
        if not specs:
            continue

        default_weight = float(preset_families.get(family_name, 1 / len(active_family_names))) if isinstance(preset_families, dict) else 1 / len(active_family_names)
        st.markdown(
            f"""
<div class="finder-family-card">
  <div class="finder-family-title"><span>{html.escape(family_name)}</span><span class="finder-family-score">weight</span></div>
  <div class="finder-family-desc">{html.escape(family["description"])}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        c_weight, c_metrics = st.columns([0.28, 0.72])
        with c_weight:
            family_weights[family_name] = st.number_input(
                f"{family_name} weight",
                min_value=0.0,
                max_value=1.0,
                value=float(round(default_weight, 2)),
                step=0.05,
                key=f"weight_{family_name}",
            )
        with c_metrics:
            metric_labels = [s["metric"] for s in specs]
            selected_metrics = st.multiselect(
                f"{family_name} metrics",
                metric_labels,
                default=metric_labels,
                key=f"metrics_{family_name}",
            )

        selected_specs = [s for s in specs if s["metric"] in selected_metrics]
        family_metrics[family_name] = []

        for spec in selected_specs:
            metric_name = spec["metric"]
            direction = spec["direction"]
            raw_default = default_threshold(reference_pool, spec, strictness)
            sign = "≥" if direction == "min" else "≤"

            c0, c1, c2, c3 = st.columns([0.44, 0.16, 0.26, 0.14])
            with c0:
                st.markdown(f"**{metric_name}**")
            with c1:
                st.markdown(f"`{sign}`")
            with c2:
                values = pd.to_numeric(reference_pool.get(metric_name), errors="coerce").dropna()
                step = 0.01 if values.empty or abs(raw_default) < 3 else 0.10
                threshold = st.number_input(
                    f"{metric_name} threshold",
                    value=float(round(raw_default, 2)),
                    step=step,
                    key=f"thr_{family_name}_{metric_name}",
                    label_visibility="collapsed",
                )
            with c3:
                active = st.checkbox(
                    "active",
                    value=True,
                    key=f"active_{family_name}_{metric_name}",
                    label_visibility="collapsed",
                )

            spec2 = dict(spec)
            spec2["threshold"] = float(threshold)
            spec2["family"] = family_name
            if active:
                active_criteria.append(spec2)
            family_metrics[family_name].append(spec2)

with st.expander("Add custom metrics", expanded=False):
    numeric_cols = [
        c for c in reference_pool.columns
        if c not in {"Season", "Player", "Team", "Position", "Role bucket", "League", "Nation"}
        and pd.to_numeric(reference_pool[c], errors="coerce").notna().sum() > 0
    ]
    custom_metric_names = st.multiselect("Extra raw metrics", sorted(numeric_cols), default=[])
    for cm in custom_metric_names:
        c0, c1, c2 = st.columns([0.40, 0.20, 0.40])
        with c0:
            direction = st.selectbox(f"{cm} direction", ["min", "max"], index=0, key=f"custom_dir_{cm}")
        with c1:
            q = st.slider(f"{cm} q", min_value=0.10, max_value=0.90, value=0.60, step=0.05, key=f"custom_q_{cm}")
        spec = metric(cm, direction, q)
        thr = default_threshold(reference_pool, spec, strictness)
        with c2:
            threshold = st.number_input(f"{cm} threshold", value=float(round(thr, 2)), step=0.10, key=f"custom_thr_{cm}")
        spec["threshold"] = float(threshold)
        spec["family"] = "Custom"
        active_criteria.append(spec)

if not active_criteria:
    st.warning("Nessuna metrica attiva.")
    st.stop()

# Normalize family weights
total_w = sum(max(0, w) for w in family_weights.values())
if total_w <= 0:
    family_weights = {f: 1 / len(active_family_names) for f in active_family_names}
else:
    family_weights = {f: max(0, w) / total_w for f, w in family_weights.items()}

# -------------------------------------------------------------------------
# Scoring
# -------------------------------------------------------------------------

scored = candidate_pool.copy()

for spec in active_criteria:
    metric_name = spec["metric"]
    scored[f"pass__{metric_name}"] = scored[metric_name].apply(lambda v, s=spec: pass_criterion(v, s["threshold"], s["direction"]))
    scored[f"pct__{metric_name}"] = metric_percentile(reference_pool, scored[metric_name], metric_name, spec["direction"])

for family_name in active_family_names:
    specs = [s for s in family_metrics.get(family_name, []) if f"pct__{s['metric']}" in scored.columns]
    pct_cols = [f"pct__{s['metric']}" for s in specs]
    if pct_cols:
        scored[f"{family_name} score"] = scored[pct_cols].mean(axis=1)
    else:
        scored[f"{family_name} score"] = np.nan

fit = pd.Series(0.0, index=scored.index)
weight_sum = 0.0
for family_name in active_family_names:
    col = f"{family_name} score"
    if col in scored.columns:
        w = family_weights.get(family_name, 0)
        fit = fit + scored[col].fillna(50) * w
        weight_sum += w
scored["Fit Score"] = fit / max(weight_sum, 1e-9)

pass_cols = [f"pass__{s['metric']}" for s in active_criteria if f"pass__{s['metric']}" in scored.columns]
scored["criteria_matched"] = scored[pass_cols].sum(axis=1) if pass_cols else 0
scored["criteria_total"] = len(pass_cols)

# Anchor similarity on active metric percentiles
if anchor_row is not None and anchor_weight > 0:
    anchor_vec = []
    cand_cols = []
    for spec in active_criteria:
        metric_name = spec["metric"]
        pct_col = f"pct__{metric_name}"
        if pct_col not in scored.columns:
            continue
        anchor_pct = metric_percentile(reference_pool, pd.Series([anchor_row.get(metric_name)], index=[0]), metric_name, spec["direction"]).iloc[0]
        if pd.notna(anchor_pct):
            anchor_vec.append(float(anchor_pct))
            cand_cols.append(pct_col)
    if cand_cols:
        arr = scored[cand_cols].fillna(50).to_numpy(dtype=float)
        anchor_arr = np.array(anchor_vec, dtype=float)
        dist = np.sqrt(((arr - anchor_arr) ** 2).mean(axis=1))
        scored["Anchor Similarity"] = np.clip(100 - dist * 1.15, 0, 100)
    else:
        scored["Anchor Similarity"] = np.nan
else:
    scored["Anchor Similarity"] = np.nan

if anchor_weight > 0 and "Anchor Similarity" in scored.columns:
    scored["Finder Score"] = scored["Fit Score"] * (1 - anchor_weight) + scored["Anchor Similarity"].fillna(scored["Fit Score"]) * anchor_weight
else:
    scored["Finder Score"] = scored["Fit Score"]

scored["Profile warning"] = scored.apply(lambda row: profile_warnings(row, role), axis=1)
scored = scored.sort_values(["criteria_matched", "Finder Score", "Minutes played"], ascending=[False, False, False])

# -------------------------------------------------------------------------
# Distribution inspector
# -------------------------------------------------------------------------

st.markdown('<div class="finder-section-title">Distribution inspector</div>', unsafe_allow_html=True)
active_metric_names = []
for s in active_criteria:
    if s["metric"] not in active_metric_names:
        active_metric_names.append(s["metric"])
inspect_metric = st.selectbox("Metric to inspect", active_metric_names, index=0)
inspect_spec = next(s for s in active_criteria if s["metric"] == inspect_metric)
render_distribution(reference_pool, candidate_pool, inspect_metric, inspect_spec["threshold"], inspect_spec["direction"], anchor_row)

# -------------------------------------------------------------------------
# Results
# -------------------------------------------------------------------------

summary = st.columns(5)
summary[0].metric("Reference pool", len(reference_pool))
summary[1].metric("Candidate pool", len(candidate_pool))
summary[2].metric("Strict matches", int(scored["criteria_matched"].eq(scored["criteria_total"]).sum()))
summary[3].metric("Near matches", int((scored["criteria_matched"] >= max(1, scored["criteria_total"] - 2)).sum()))
summary[4].metric("Median fit", fmt_num(scored["Finder Score"].median(), 0))

strict_matches = scored[scored["criteria_matched"].eq(scored["criteria_total"])].copy()
near_matches = scored[(scored["criteria_matched"] >= max(1, scored["criteria_total"] - 2)) & ~scored.index.isin(strict_matches.index)].copy()
wildcards = scored[
    (pd.to_numeric(scored.get("Age"), errors="coerce") <= 23)
    & (scored["criteria_matched"] >= max(1, scored["criteria_total"] - 3))
    & ~scored.index.isin(strict_matches.index)
    & ~scored.index.isin(near_matches.index)
].copy()

render_cards(strict_matches, active_criteria, active_family_names, "Strict matches", limit=12)
render_cards(near_matches, active_criteria, active_family_names, "Near matches", limit=10)
render_cards(wildcards, active_criteria, active_family_names, "Wildcard profiles U23", limit=8)

with st.expander("Full candidate table", expanded=False):
    family_score_cols = [f"{f} score" for f in active_family_names if f"{f} score" in scored.columns]
    metric_cols = [s["metric"] for s in active_criteria if s["metric"] in scored.columns]
    base_cols = [
        "Player",
        "Age",
        "Position",
        "Team",
        "League",
        "Nation",
        "style_cluster_name",
        "Minutes played",
        "Finder Score",
        "Fit Score",
        "Anchor Similarity",
        "criteria_matched",
        "criteria_total",
        "Profile warning",
    ]
    show_cols = [c for c in base_cols + family_score_cols + metric_cols if c in scored.columns]
    table = scored.head(200)[show_cols].copy()
    st.markdown(render_table(table), unsafe_allow_html=True)

    csv = table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download shortlist CSV",
        data=csv,
        file_name=f"player_finder_{role}_{season}.csv",
        mime="text/csv",
    )
