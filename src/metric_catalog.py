"""
Metric catalog v1 for the Streamlit football scouting app.
Based on the uploaded Players Dataset.xlsx and Team Dataset.xlsx column names.

Main design choices:
- Outfield players only. GK handled separately later.
- Values shown on the card can be raw or possession-adjusted.
- Radar and card percentiles are computed against a selected reference group.
- Unit for bars/radar = percentile 0-100.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Literal

from .role_utils import ROLE_BUCKETS

Adjustment = Literal["on_ball", "off_ball", "none"]
MetricKind = Literal["volume", "quality", "negative", "derived"]

BIG_FIVE_LEAGUES = ["Serie A", "Premier League", "La Liga", "Bundesliga", "Ligue 1"]


ROLE_WEIGHTS = {
    "CB": {
        "Active Defending": 0.25,
        "Duels": 0.20,
        "Progression": 0.15,
        "Passing Accuracy": 0.15,
        "Ball Security": 0.15,
        "Final Product": 0.05,
        "Creation": 0.05,
    },
    "FB": {
        "Progression": 0.20,
        "Active Defending": 0.20,
        "Creation": 0.15,
        "Passing Accuracy": 0.15,
        "Dribbling": 0.10,
        "Receiving": 0.10,
        "Duels": 0.10,
    },
    "MF": {
        "Progression": 0.25,
        "Passing Accuracy": 0.20,
        "Creation": 0.15,
        "Active Defending": 0.15,
        "Receiving": 0.10,
        "Ball Security": 0.10,
        "Final Product": 0.05,
    },
    "AM": {
        "Creation": 0.25,
        "Final Product": 0.20,
        "Progression": 0.20,
        "Receiving": 0.15,
        "Dribbling": 0.10,
        "Passing Accuracy": 0.05,
        "Ball Security": 0.05,
    },
    "W": {
        "Dribbling": 0.22,
        "Creation": 0.18,
        "Final Product": 0.18,
        "Progression": 0.17,
        "Receiving": 0.10,
        "Duels": 0.08,
        "Active Defending": 0.07,
    },
    "FW": {
        "Final Product": 0.35,
        "Shooting": 0.25,
        "Receiving": 0.15,
        "Dribbling": 0.10,
        "Creation": 0.10,
        "Progression": 0.05,
    },
}

CARD_GROUPS = {
    "Final Product": {
        "color": "#FFE66D",
        "icon": "⚡",
        "metrics": [
            {"label": "Goals", "column": "Goals", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Assists", "column": "Assists", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Goals + Assists", "derived": "Goals + Assists", "kind": "derived", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "xG", "column": "xG (expected goals)", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "xA", "column": "xA", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "xG + xA", "derived": "xG + xA", "kind": "derived", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Scoring attack involvement", "column": "Involvement in scoring attacks", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Actions in box", "column": "Actions in opponent's box", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
        ],
    },
    "Shooting": {
        "color": "#FF4D2E",
        "icon": "◎",
        "metrics": [
            {"label": "Shots", "column": "Shots", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Shots on target", "column": "Shots on target", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Shots on target %", "column": "Shots on target, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "xG", "column": "xG (expected goals)", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "xG per shot", "column": "xGPS (xG per shot)", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "0.00"},
            {"label": "xG conversion", "column": "xGC (xG conversion)", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Shots in box", "column": "Shots from the penalty area", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Shots outside box", "column": "Shots from outside the penalty area", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
        ],
    },
    "Creation": {
        "color": "#20D9FF",
        "icon": "☆",
        "metrics": [
            {"label": "xA", "column": "xA", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Key passes", "column": "Key passes", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Key pass accuracy", "column": "Key passes accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Passes for a shot", "column": "Passes for a shot", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Chances created", "column": "Chances created", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Crosses", "column": "Crosses", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Cross accuracy", "column": "Crosses accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
        ],
    },
    "Receiving": {
        "color": "#FF2E78",
        "icon": "▱",
        "metrics": [
            {"label": "Open passes received", "column": "Open passes received", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Long open passes received", "column": "Long open passes received", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Super long received", "column": "Super long open passes received", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Received in final third", "column": "Open passes received in the final third", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Received in box", "column": "Open passes received in the opponent's box", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
        ],
    },
    "Dribbling": {
        "color": "#A855F7",
        "icon": "↝",
        "metrics": [
            {"label": "Dribbles", "column": "Dribbles", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Successful dribbles", "column": "Dribbles successful", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Dribble success %", "column": "Dribbles successful, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Final third dribbles", "column": "Dribbling in the final third", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Final third dribble success %", "column": "Dribbling in the final third successful, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
        ],
    },
    "Progression": {
        "color": "#A3FF12",
        "icon": "↗",
        "metrics": [
            {"label": "Progressive passes", "column": "Progressive passes", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Progressive pass accuracy", "column": "Progressive passes accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Progressive open passes", "column": "Progressive open passes", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Passes to final third", "column": "Passes forward to the final third", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Final third pass accuracy", "column": "Passes forward to the final third accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Passes into box", "column": "Passes into the penalty box", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Final third entries", "column": "Final third entries", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Entries via pass", "column": "Final third entries through pass", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Entries via carry", "column": "Final third entries through carry", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Carry", "column": "Carry", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
        ],
    },
    "Passing Accuracy": {
        "color": "#22C55E",
        "icon": "✓",
        "metrics": [
            {"label": "Passes", "column": "Passes", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Pass accuracy", "column": "Passes accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Short pass accuracy", "column": "Short passes accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Long passes", "column": "Long passes", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Long pass accuracy", "column": "Long passes accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Super long pass accuracy", "column": "Super long passes accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
        ],
    },
    "Active Defending": {
        "color": "#2F80FF",
        "icon": "◇",
        "metrics": [
            {"label": "Defensive challenges", "column": "Defensive challenges", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Defensive challenge win %", "column": "Defensive challenges won, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Tackles", "column": "Tackles", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Tackle success %", "column": "Tackles successful, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Interceptions", "column": "Interceptions", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Ball recoveries", "column": "Ball recoveries", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Recoveries opp. half", "column": "Ball recoveries in opponent's half", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Loose ball recoveries", "column": "Loose ball recoveries", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
        ],
    },
    "Duels": {
        "color": "#F59E0B",
        "icon": "×",
        "metrics": [
            {"label": "Challenges", "column": "Challenges", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Challenge win %", "column": "Challenges won, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Attacking challenges", "column": "Attacking challenges", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Attacking challenge win %", "column": "Attacking challenges won, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Aerial challenges", "column": "Air challenges", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Aerial win %", "column": "Air challenges won, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
        ],
    },
    "Ball Security": {
        "color": "#FB7185",
        "icon": "!",
        "metrics": [
            {"label": "Lost balls", "column": "Lost balls", "kind": "negative", "adjustment": "on_ball", "higher_is_better": False, "fmt": "0.00"},
            {"label": "Lost balls own half", "column": "Lost balls in own half", "kind": "negative", "adjustment": "on_ball", "higher_is_better": False, "fmt": "0.00"},
            {"label": "Lost after passes", "column": "Lost balls after passes", "kind": "negative", "adjustment": "on_ball", "higher_is_better": False, "fmt": "0.00"},
            {"label": "Individual losses", "column": "Individual ball losses", "kind": "negative", "adjustment": "on_ball", "higher_is_better": False, "fmt": "0.00"},
            {"label": "Bad control", "column": "Bad ball control", "kind": "negative", "adjustment": "on_ball", "higher_is_better": False, "fmt": "0.00"},
            {"label": "Mistakes to chances", "column": "Mistakes leading to chances", "kind": "negative", "adjustment": "none", "higher_is_better": False, "fmt": "0.00"},
            {"label": "Mistakes to goals", "column": "Mistakes leading to goals", "kind": "negative", "adjustment": "none", "higher_is_better": False, "fmt": "0.00"},
        ],
    },
}

# Radar axes: same labels/order for Style and Performance inside each role.
# Each axis is a synthetic percentile obtained by averaging the percentiles of the listed columns/derived metrics.
RADAR_AXES = {
    "CB": [
        {"axis": "Defending", "style": ["Defensive challenges", "Tackles", "Interceptions"], "performance": ["Defensive challenges won, %", "Tackles successful, %"]},
        {"axis": "Aerial", "style": ["Air challenges"], "performance": ["Air challenges won, %"]},
        {"axis": "Recovery", "style": ["Ball recoveries", "Loose ball recoveries"], "performance": ["Mistakes leading to chances", "Mistakes leading to goals"], "inverse_performance": True},
        {"axis": "Build-up", "style": ["Passes", "Short passes", "Long passes"], "performance": ["Passes accurate, %", "Long passes accurate, %"]},
        {"axis": "Progression", "style": ["Progressive passes", "Passes forward to the final third"], "performance": ["Progressive passes accurate, %", "Passes forward to the final third accurate, %"]},
        {"axis": "Carrying", "style": ["Carry", "Final third entries through carry"], "performance": ["Lost balls", "Individual ball losses"], "inverse_performance": True},
        {"axis": "Security", "style": ["Actions", "Passes"], "performance": ["Actions successful, %", "Bad ball control"], "inverse_performance": True},
    ],
    "FB": [
        {"axis": "Progression", "style": ["Progressive passes", "Passes forward to the final third"], "performance": ["Progressive passes accurate, %", "Passes forward to the final third accurate, %"]},
        {"axis": "Carrying", "style": ["Carry", "Final third entries through carry"], "performance": ["Lost balls", "Individual ball losses"], "inverse_performance": True},
        {"axis": "Crossing", "style": ["Crosses", "Passes into the penalty box"], "performance": ["Crosses accurate, %", "Passes into the penalty box accurate, %"]},
        {"axis": "Creation", "style": ["Key passes", "Passes for a shot", "Chances created"], "performance": ["Key passes accurate, %", "xA"]},
        {"axis": "Defending", "style": ["Defensive challenges", "Tackles", "Interceptions"], "performance": ["Defensive challenges won, %", "Tackles successful, %"]},
        {"axis": "Duels", "style": ["Challenges", "Air challenges"], "performance": ["Challenges won, %", "Air challenges won, %"]},
        {"axis": "Receiving", "style": ["Open passes received", "Open passes received in the final third"], "performance": ["Actions successful, %"]},
    ],
    "MF": [
        {"axis": "Circulation", "style": ["Passes", "Short passes"], "performance": ["Passes accurate, %", "Short passes accurate, %"]},
        {"axis": "Progression", "style": ["Progressive passes", "Passes forward to the final third"], "performance": ["Progressive passes accurate, %", "Passes forward to the final third accurate, %"]},
        {"axis": "Creation", "style": ["Key passes", "Passes for a shot", "Chances created"], "performance": ["Key passes accurate, %", "xA"]},
        {"axis": "Receiving", "style": ["Open passes received", "Open passes received in the central third", "Open passes received in the final third"], "performance": ["Actions successful, %"]},
        {"axis": "Carrying", "style": ["Carry", "Final third entries through carry"], "performance": ["Lost balls", "Individual ball losses"], "inverse_performance": True},
        {"axis": "Defending", "style": ["Defensive challenges", "Interceptions", "Ball recoveries"], "performance": ["Defensive challenges won, %", "Tackles successful, %"]},
        {"axis": "Security", "style": ["Actions", "Passes"], "performance": ["Actions successful, %", "Bad ball control"], "inverse_performance": True},
    ],
    "AM": [
        {"axis": "Between Lines", "style": ["Open passes received in the final third", "Open passes received in the opponent's box"], "performance": ["Actions successful, %"]},
        {"axis": "Creation", "style": ["Key passes", "Passes for a shot", "Chances created"], "performance": ["Key passes accurate, %", "xA"]},
        {"axis": "Final Product", "style": ["Goals", "Assists", "Involvement in scoring attacks"], "performance": ["xGC (xG conversion)", "Chances successful, %"]},
        {"axis": "Combination", "style": ["Passes", "Short passes", "Progressive passes"], "performance": ["Passes accurate, %", "Short passes accurate, %"]},
        {"axis": "Progression", "style": ["Progressive passes", "Final third entries", "Carry"], "performance": ["Progressive passes accurate, %", "Passes forward to the final third accurate, %"]},
        {"axis": "Dribbling", "style": ["Dribbles", "Dribbling in the final third"], "performance": ["Dribbles successful, %", "Dribbling in the final third successful, %"]},
        {"axis": "Security", "style": ["Actions", "Passes"], "performance": ["Actions successful, %", "Lost balls"], "inverse_performance": True},
    ],
    "W": [
        {"axis": "1v1", "style": ["Dribbles", "Dribbling in the final third"], "performance": ["Dribbles successful, %", "Dribbling in the final third successful, %"]},
        {"axis": "Wide Creation", "style": ["Crosses", "Passes into the penalty box"], "performance": ["Crosses accurate, %", "Passes into the penalty box accurate, %"]},
        {"axis": "Box Threat", "style": ["Actions in opponent's box", "Open passes received in the opponent's box"], "performance": ["xGPS (xG per shot)", "Chances successful, %"]},
        {"axis": "Final Product", "style": ["Goals", "Assists", "Involvement in scoring attacks"], "performance": ["xGC (xG conversion)", "Chances successful, %"]},
        {"axis": "Receiving", "style": ["Open passes received in the final third", "Open passes received"], "performance": ["Actions successful, %"]},
        {"axis": "Progression", "style": ["Progressive passes", "Final third entries through carry", "Carry"], "performance": ["Progressive passes accurate, %", "Passes forward to the final third accurate, %"]},
        {"axis": "Defensive Work", "style": ["Defensive challenges", "Ball recoveries"], "performance": ["Defensive challenges won, %", "Tackles successful, %"]},
    ],
    "FW": [
        {"axis": "Box Threat", "style": ["Actions in opponent's box", "Open passes received in the opponent's box"], "performance": ["Chances successful, %", "xGC (xG conversion)"]},
        {"axis": "Shooting", "style": ["Shots", "Shots from the penalty area"], "performance": ["Shots on target, %", "xGPS (xG per shot)"]},
        {"axis": "Final Product", "style": ["Goals", "Assists", "Involvement in scoring attacks"], "performance": ["xGC (xG conversion)", "Chances successful, %"]},
        {"axis": "Receiving", "style": ["Open passes received", "Open passes received in the final third", "Open passes received in the opponent's box"], "performance": ["Actions successful, %"]},
        {"axis": "Duels", "style": ["Attacking challenges", "Air challenges"], "performance": ["Attacking challenges won, %", "Air challenges won, %"]},
        {"axis": "Dribbling", "style": ["Dribbles", "Dribbling in the final third"], "performance": ["Dribbles successful, %", "Dribbling in the final third successful, %"]},
        {"axis": "Link-up", "style": ["Passes", "Key passes", "Passes for a shot"], "performance": ["Passes accurate, %", "Key passes accurate, %"]},
    ],
}

DERIVED_METRICS = {
    "Goals + Assists": lambda df: df["Goals"] + df["Assists"],
    "xG + xA": lambda df: df["xG (expected goals)"] + df["xA"],
}


def sigmoid_possession_adjustment(
    raw_value: float,
    team_possession: float,
    adjustment: Adjustment,
    k: float = 8.0,
    gamma: float = 0.35,
) -> float:
    """Non-linear possession adjustment.

    team_possession must be in [0, 1], as in the uploaded Team Dataset.
    on_ball: high-possession contexts are slightly penalized; low-possession contexts are rewarded.
    off_ball: high-possession contexts are rewarded; low-possession contexts are slightly penalized.
    none: returns raw_value unchanged.
    """
    if adjustment == "none" or raw_value is None or team_possession is None:
        return raw_value

    s = 2 / (1 + exp(-k * (team_possession - 0.50))) - 1
    if adjustment == "on_ball":
        return raw_value * (1 - gamma * s)
    if adjustment == "off_ball":
        return raw_value * (1 + gamma * s)
    return raw_value
