from __future__ import annotations

import html
from typing import Any

import streamlit as st

from src.ui import inject_css
from src.metric_catalog import CARD_GROUPS
from src.gk_metric_catalog import GK_CARD_GROUPS

st.set_page_config(page_title="Football Scouting Lab", page_icon="⚽", layout="wide")
inject_css()

st.markdown(
    """
    <style>
    .home-hero {
        border: 1px solid rgba(95,255,224,0.20);
        background: radial-gradient(circle at top left, rgba(95,255,224,0.12), transparent 35%),
                    linear-gradient(115deg, rgba(16,22,43,0.90), rgba(33,21,60,0.70));
        border-radius: 26px;
        padding: 30px 32px;
        margin: 0.6rem 0 1.6rem 0;
        box-shadow: 0 18px 62px rgba(0,0,0,0.30), inset 0 0 26px rgba(95,255,224,0.04);
    }
    .home-kicker {
        color: #5FFFE0;
        font-size: 0.82rem;
        font-weight: 950;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .home-title {
        color: #F8FBFF;
        font-size: 3.2rem;
        line-height: 1.0;
        font-weight: 950;
        letter-spacing: -0.04em;
        text-shadow: 0 0 18px rgba(95,255,224,0.18);
        margin-bottom: 12px;
    }
    .home-subtitle {
        color: #B7CAE8;
        font-size: 1.02rem;
        line-height: 1.55;
        max-width: 1050px;
        font-weight: 650;
    }
    .glossary-section-title {
        color: #F8FBFF;
        font-size: 1.55rem;
        font-weight: 950;
        margin: 2rem 0 0.8rem 0;
        letter-spacing: -0.02em;
    }
    .glossary-family {
        background: rgba(16,22,43,0.82);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 16px 16px 10px 16px;
        margin-bottom: 18px;
        box-shadow: 0 14px 44px rgba(0,0,0,0.23);
    }
    .glossary-family-head {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:12px;
        padding-bottom: 10px;
        margin-bottom: 6px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .glossary-family-title {
        font-size: 1.05rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .glossary-family-count {
        color: #8EA2C6;
        font-size: 0.74rem;
        font-weight: 850;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .glossary-row {
        display:grid;
        grid-template-columns: 1.05fr 2.2fr 0.55fr 0.65fr;
        gap: 14px;
        align-items:start;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.055);
    }
    .glossary-row:last-child {border-bottom:0;}
    .glossary-label {
        color: #F6F7FB;
        font-size: 0.94rem;
        font-weight: 950;
    }
    .glossary-def {
        color: #B7CAE8;
        font-size: 0.88rem;
        line-height: 1.45;
        font-weight: 620;
    }
    .glossary-pill {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        min-height: 24px;
        border-radius: 999px;
        padding: 4px 8px;
        background: rgba(95,255,224,0.10);
        border: 1px solid rgba(95,255,224,0.22);
        color: #BFFFF4;
        font-size: 0.70rem;
        font-weight: 900;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        text-align:center;
    }
    .glossary-pill-negative {
        background: rgba(255,79,109,0.10);
        border-color: rgba(255,79,109,0.25);
        color: #FFB3C0;
    }
    .glossary-note-grid {
        display:grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
        margin: 1rem 0 1.6rem 0;
    }
    .glossary-note {
        background: rgba(16,22,43,0.75);
        border: 1px solid rgba(95,255,224,0.16);
        border-radius: 18px;
        padding: 14px 16px;
    }
    .glossary-note-title {
        color:#5FFFE0;
        font-size:0.82rem;
        font-weight:950;
        letter-spacing:0.08em;
        text-transform:uppercase;
        margin-bottom:6px;
    }
    .glossary-note-text {
        color:#B7CAE8;
        font-size:0.84rem;
        line-height:1.45;
    }
    @media (max-width: 1100px) {
        .glossary-row {grid-template-columns: 1fr;}
        .glossary-note-grid {grid-template-columns: 1fr;}
        .home-title {font-size: 2.35rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="home-hero">
      <div class="home-kicker">Football Scouting Lab</div>
      <div class="home-title">Glossario metriche</div>
      <div class="home-subtitle">
        La prima pagina operativa è la card dei giocatori di movimento: valori raw o possession-adjusted,
        percentili per ruolo/campionato, overall role-based e doppio radar Playing Style / Performance.
        Qui trovi il glossario operativo delle metriche usate nell’app, incluse le metriche dei portieri.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

GENERAL_DEFINITIONS = [
    (
        "Raw",
        "Valore osservato nel dataset, senza correzioni per il contesto di possesso squadra.",
    ),
    (
        "Possession-adjusted",
        "Valore corretto con una formula non lineare sigmoide in base al possesso della squadra. Le metriche on-ball sono leggermente penalizzate in squadre ad alto possesso e premiate in squadre a basso possesso; le metriche off-ball fanno il contrario.",
    ),
    (
        "Percentile",
        "Posizionamento 0–100 rispetto al gruppo di riferimento selezionato. 90 significa che il giocatore è sopra circa il 90% dei pari ruolo/contesto.",
    ),
    (
        "Overall role-based",
        "Media pesata dei punteggi di famiglia. I pesi cambiano per ruolo: ad esempio un attaccante pesa di più final product e shooting, un difensore pesa di più difesa, duelli e sicurezza.",
    ),
    (
        "Playing Style radar",
        "Radar costruito su metriche di volume: descrive quanto spesso un giocatore compie certe azioni.",
    ),
    (
        "Performance radar",
        "Radar costruito su metriche di qualità/successo: descrive quanto bene il giocatore esegue quelle azioni.",
    ),
    (
        "Fit Index",
        "Nella pagina Similarity misura quanto il profilo percentile del giocatore è compatibile con il profilo medio del campionato target.",
    ),
    (
        "League Weighting",
        "Aumenta il peso delle feature che caratterizzano maggiormente il campionato target rispetto al riferimento generale.",
    ),
]

DEFINITIONS: dict[str, str] = {
    # Final Product / Shooting
    "Goals": "Gol segnati, normalmente espressi per 90 minuti o nel formato scelto dalla pagina.",
    "Assists": "Assist realizzati: ultimo passaggio che porta direttamente a un gol.",
    "Goals + Assists": "Somma di gol e assist; misura sintetica di produzione diretta.",
    "xG": "Expected Goals: probabilità cumulata che i tiri del giocatore diventino gol in base alla qualità delle occasioni.",
    "xA": "Expected Assists: probabilità cumulata che i passaggi del giocatore generino assist attesi.",
    "xG + xA": "Somma di expected goals ed expected assists; misura di minaccia offensiva attesa.",
    "Scoring attack involvement": "Coinvolgimento in azioni d’attacco che terminano con un gol o con una situazione di scoring rilevante.",
    "Actions in box": "Azioni effettuate nell’area di rigore avversaria; proxy di presenza e pericolosità in zona calda.",
    "Shots": "Tiri tentati.",
    "Shots on target": "Tiri nello specchio della porta.",
    "Shots on target %": "Quota di tiri che finiscono nello specchio; misura di precisione del tiro.",
    "xG per shot": "Qualità media dei tiri: xG medio generato da ogni conclusione.",
    "xG conversion": "Efficienza realizzativa rispetto agli xG; valori più alti indicano migliore conversione delle occasioni.",
    "Shots in box": "Tiri effettuati dall’interno dell’area di rigore.",
    "Shots outside box": "Tiri effettuati da fuori area.",
    # Creation
    "Key passes": "Passaggi che portano direttamente a una conclusione.",
    "Key pass accuracy": "Percentuale di key passes riusciti.",
    "Passes for a shot": "Passaggi che creano o preparano un tiro.",
    "Chances created": "Occasioni create per i compagni.",
    "Crosses": "Cross effettuati.",
    "Cross accuracy": "Percentuale di cross riusciti.",
    # Receiving
    "Open passes received": "Passaggi ricevuti in gioco aperto.",
    "Long open passes received": "Passaggi lunghi ricevuti in gioco aperto.",
    "Super long received": "Passaggi molto lunghi ricevuti.",
    "Received in final third": "Passaggi ricevuti nell’ultimo terzo di campo.",
    "Received in box": "Passaggi ricevuti nell’area di rigore avversaria.",
    # Dribbling
    "Dribbles": "Dribbling tentati.",
    "Successful dribbles": "Dribbling riusciti.",
    "Dribble success %": "Percentuale di dribbling riusciti.",
    "Final third dribbles": "Dribbling tentati nell’ultimo terzo.",
    "Final third dribble success %": "Percentuale di dribbling riusciti nell’ultimo terzo.",
    # Progression
    "Progressive passes": "Passaggi che fanno avanzare significativamente il pallone verso la porta avversaria.",
    "Progressive pass accuracy": "Percentuale di passaggi progressivi riusciti.",
    "Progressive open passes": "Passaggi progressivi in gioco aperto.",
    "Passes to final third": "Passaggi in avanti verso l’ultimo terzo.",
    "Final third pass accuracy": "Percentuale di passaggi verso l’ultimo terzo riusciti.",
    "Passes into box": "Passaggi nell’area di rigore avversaria.",
    "Final third entries": "Ingressi complessivi nell’ultimo terzo tramite passaggio o conduzione.",
    "Entries via pass": "Ingressi nell’ultimo terzo effettuati tramite passaggio.",
    "Entries via carry": "Ingressi nell’ultimo terzo effettuati portando palla.",
    "Carry": "Conduzioni palla progressive o rilevanti.",
    # Passing
    "Passes": "Passaggi tentati.",
    "Pass accuracy": "Percentuale di passaggi riusciti.",
    "Short pass accuracy": "Percentuale di passaggi corti riusciti.",
    "Long passes": "Passaggi lunghi tentati.",
    "Long pass accuracy": "Percentuale di passaggi lunghi riusciti.",
    "Super long pass accuracy": "Percentuale di passaggi molto lunghi riusciti.",
    # Defending / duels
    "Defensive challenges": "Contrasti/duelli difensivi affrontati.",
    "Defensive challenge win %": "Percentuale di duelli difensivi vinti.",
    "Tackles": "Tackle effettuati.",
    "Tackle success %": "Percentuale di tackle riusciti.",
    "Interceptions": "Intercetti effettuati.",
    "Ball recoveries": "Palloni recuperati.",
    "Recoveries opp. half": "Recuperi palla nella metà campo avversaria.",
    "Loose ball recoveries": "Recuperi di palloni vaganti.",
    "Challenges": "Duelli complessivi affrontati.",
    "Challenge win %": "Percentuale di duelli complessivi vinti.",
    "Attacking challenges": "Duelli offensivi affrontati.",
    "Attacking challenge win %": "Percentuale di duelli offensivi vinti.",
    "Aerial challenges": "Duelli aerei affrontati.",
    "Aerial win %": "Percentuale di duelli aerei vinti.",
    # Ball security
    "Lost balls": "Palloni persi. Metrica negativa: percentile alto significa perderne pochi rispetto al riferimento.",
    "Lost balls own half": "Palloni persi nella propria metà campo. Metrica negativa.",
    "Lost after passes": "Palloni persi dopo un passaggio. Metrica negativa.",
    "Individual losses": "Perdite individuali del pallone. Metrica negativa.",
    "Bad control": "Errori di controllo palla. Metrica negativa.",
    "Mistakes to chances": "Errori che portano a occasioni avversarie. Metrica negativa.",
    "Mistakes to goals": "Errori che portano a gol avversari. Metrica negativa.",
    # GK
    "Goals prevented": "Differenza tra xG dei tiri affrontati e gol concessi: indica quanti gol il portiere ha evitato rispetto all’atteso.",
    "Goals prevented %": "Goals prevented rapportato al volume/qualità dei tiri affrontati; misura normalizzata dello shot-stopping.",
    "Shots saved %": "Percentuale di tiri nello specchio parati.",
    "xG per goal conceded": "xG medio necessario agli avversari per segnare un gol al portiere; più alto è meglio.",
    "Opponent xG conversion": "Conversione degli xG avversari in gol. Metrica negativa: più bassa è meglio.",
    "Close-range save %": "Percentuale di parate su tiri ravvicinati.",
    "Mid-range save %": "Percentuale di parate su tiri da media distanza.",
    "Long-range save %": "Percentuale di parate su tiri dalla lunga distanza.",
    "Shots on target faced": "Tiri nello specchio affrontati. Volume di lavoro, non necessariamente qualità.",
    "Opponent xG": "xG dei tiri affrontati dal portiere.",
    "Opponent shots xG": "xG cumulato dei tiri avversari affrontati.",
    "Caught shots %": "Percentuale di tiri bloccati/trattenuti senza respinta.",
    "Parried to safety %": "Percentuale di respinte verso zone sicure.",
    "Parried into danger %": "Percentuale di respinte verso zone pericolose. Metrica negativa.",
    "Caught shots": "Numero/volume di tiri bloccati.",
    "Parried to safety": "Numero/volume di respinte sicure.",
    "Parried into danger": "Numero/volume di respinte in zona pericolosa. Metrica negativa.",
    "Cross claim rate": "Quota di cross avversari controllati/attaccati efficacemente dal portiere.",
    "Interception success %": "Percentuale di uscite/intercetti riusciti su cross o passaggi.",
    "Interception attempts": "Tentativi di intercetto su cross o passaggi.",
    "Successful interceptions": "Intercetti riusciti su cross o passaggi.",
    "Opponent crosses": "Cross avversari affrontati. Volume di contesto.",
    "Sweeping actions": "Azioni da portiere-libero fuori dalla linea di porta.",
    "Successful sweeping": "Azioni di sweeping riuscite.",
    "Sweeping success %": "Percentuale di sweeping riusciti.",
    "Sweeping unsuccessful": "Sweeping non riusciti. Metrica negativa.",
    "Open play passes": "Passaggi effettuati in gioco aperto dal portiere.",
    "Open play pass accuracy %": "Percentuale di passaggi in gioco aperto riusciti.",
    "Progressive open passes": "Passaggi progressivi in gioco aperto effettuati dal portiere.",
    "Goal-kick accuracy %": "Percentuale di rinvii dal fondo riusciti.",
    "Throws accuracy %": "Percentuale di rimesse con le mani riuscite.",
    "Long distribution share": "Quota di distribuzioni lunghe sul totale: descrive stile più diretto o più corto.",
    "Actions successful %": "Percentuale complessiva di azioni riuscite.",
    "Mistakes to chances": "Errori che generano occasioni avversarie. Metrica negativa.",
    "Mistakes to goals": "Errori che generano gol avversari. Metrica negativa.",
    "Yellow cards": "Cartellini gialli. Metrica negativa.",
    "Red cards": "Cartellini rossi. Metrica negativa.",
}


def metric_definition(metric: dict[str, Any]) -> str:
    label = metric.get("label") or metric.get("column") or metric.get("derived") or "Metric"
    if label in DEFINITIONS:
        return DEFINITIONS[label]

    column = metric.get("column") or metric.get("derived") or label
    kind = metric.get("kind", "")
    if kind == "negative" or metric.get("higher_is_better") is False:
        return f"{column}. Metrica negativa: valori più bassi sono migliori; il percentile viene invertito."
    if kind == "quality":
        return f"{column}. Indicatore di qualità/efficienza: percentuali o conversioni, non aggiustate per possesso."
    if kind == "volume":
        return f"{column}. Indicatore di volume/frequenza dell’azione."
    return f"{column}. Indicatore derivato o specifico del dataset."


def kind_label(metric: dict[str, Any]) -> str:
    kind = metric.get("kind", "metric")
    if metric.get("higher_is_better") is False or kind == "negative":
        return "negative"
    if kind == "quality":
        return "quality"
    if kind == "volume":
        return "volume"
    if kind == "derived":
        return "derived"
    if kind == "style":
        return "style"
    return kind


def adjustment_label(metric: dict[str, Any]) -> str:
    adj = metric.get("adjustment", "none")
    if adj == "on_ball":
        return "on-ball"
    if adj == "off_ball":
        return "off-ball"
    return "no adj"


def render_family(group_name: str, group: dict[str, Any]) -> None:
    color = group.get("color", "#5FFFE0")
    metrics = group.get("metrics", [])
    html_rows = f"""
    <div class="glossary-family" style="border-color:{color}38;">
      <div class="glossary-family-head">
        <div class="glossary-family-title" style="color:{color};">{html.escape(group.get('icon', '•'))} {html.escape(group_name)}</div>
        <div class="glossary-family-count">{len(metrics)} metrics</div>
      </div>
    """
    for metric in metrics:
        label = metric.get("label") or metric.get("column") or metric.get("derived") or "Metric"
        kind = kind_label(metric)
        pill_class = "glossary-pill glossary-pill-negative" if kind == "negative" else "glossary-pill"
        html_rows += f"""
        <div class="glossary-row">
          <div class="glossary-label">{html.escape(label)}</div>
          <div class="glossary-def">{html.escape(metric_definition(metric))}</div>
          <div><span class="{pill_class}">{html.escape(kind)}</span></div>
          <div><span class="glossary-pill">{html.escape(adjustment_label(metric))}</span></div>
        </div>
        """
    html_rows += "</div>"
    st.markdown(html_rows, unsafe_allow_html=True)


st.markdown('<div class="glossary-section-title">Concetti generali dell’app</div>', unsafe_allow_html=True)
notes_html = '<div class="glossary-note-grid">'
for title, text in GENERAL_DEFINITIONS:
    notes_html += f"""
    <div class="glossary-note">
      <div class="glossary-note-title">{html.escape(title)}</div>
      <div class="glossary-note-text">{html.escape(text)}</div>
    </div>
    """
notes_html += "</div>"
st.markdown(notes_html, unsafe_allow_html=True)

tab_outfield, tab_gk = st.tabs(["Giocatori di movimento", "Portieri"])

with tab_outfield:
    st.markdown(
        '<div class="glossary-section-title">Metriche giocatori di movimento</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, (group_name, group) in enumerate(CARD_GROUPS.items()):
        with cols[i % 2]:
            render_family(group_name, group)

with tab_gk:
    st.markdown(
        '<div class="glossary-section-title">Metriche portieri</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, (group_name, group) in enumerate(GK_CARD_GROUPS.items()):
        with cols[i % 2]:
            render_family(group_name, group)

st.markdown(
    """
    <div class="glossary-note" style="margin-top:1.4rem;">
      <div class="glossary-note-title">Nota interpretativa</div>
      <div class="glossary-note-text">
        Le metriche sono pensate come supporto allo scouting, non come giudizio assoluto. I percentili cambiano in base a stagione,
        ruolo selezionato, campionati di riferimento e soglia minuti. Le metriche negative sono invertite nel percentile:
        un punteggio alto significa comportamento migliore, cioè meno eventi negativi.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
