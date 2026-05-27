"""
Goalkeeper metric catalog for the Streamlit football scouting app.

Design choices:
- Goalkeepers are evaluated only against goalkeepers.
- Values can be raw or possession-adjusted for volume metrics.
- Quality rates and efficiency metrics are not possession-adjusted.
- Negative metrics invert the percentile: lower is better.
"""

from __future__ import annotations

BIG_FIVE_LEAGUES = ["Serie A", "Premier League", "La Liga", "Bundesliga", "Ligue 1"]

GK_GROUP_WEIGHTS = {
    "Shot Stopping": 0.35,
    "Handling": 0.15,
    "Cross Command": 0.15,
    "Sweeping": 0.10,
    "Distribution": 0.20,
    "Security": 0.05,
}

GK_CARD_GROUPS = {
    "Shot Stopping": {
        "color": "#5FFFE0",
        "icon": "🧤",
        "metrics": [
            {"label": "Goals prevented", "column": "Goals prevented", "kind": "derived", "adjustment": "none", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Goals prevented %", "column": "Goals prevented, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Shots saved %", "column": "Shots saved, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "xG per goal conceded", "column": "xG per goal conceded", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Opponent xG conversion", "column": "Opponent's xG conversion", "kind": "quality", "adjustment": "none", "higher_is_better": False, "fmt": "0.00"},
            {"label": "Close-range save %", "column": "Close-range shots saved, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Mid-range save %", "column": "Mid-range shots saved, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Long-range save %", "column": "Long-range shots saved, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Shots on target faced", "column": "Shots on target faced", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00", "score_include": False},
            {"label": "Opponent shots xG", "column": "Opponent's shots xG", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00", "score_include": False},
        ],
    },
    "Handling": {
        "color": "#7CFF8A",
        "icon": "✋",
        "metrics": [
            {"label": "Caught shots %", "column": "Caught shots, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Parried to safety %", "column": "Parried shots to safety, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Parried into danger %", "column": "Parried shots into danger, %", "kind": "negative", "adjustment": "none", "higher_is_better": False, "fmt": "%"},
            {"label": "Caught shots", "column": "Caught shots", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00", "score_include": False},
            {"label": "Parried to safety", "column": "Parried shots to safety", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00", "score_include": False},
            {"label": "Parried into danger", "column": "Parried shots into danger", "kind": "negative", "adjustment": "off_ball", "higher_is_better": False, "fmt": "0.00"},
        ],
    },
    "Cross Command": {
        "color": "#FFE66D",
        "icon": "✈",
        "metrics": [
            {"label": "Cross claim rate", "column": "Cross claim rate", "kind": "derived", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Interception success %", "column": "Successful cross and pass interception attempts, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Interception attempts", "column": "Cross and pass interception attempts", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Successful interceptions", "column": "Successful cross and pass interception attempts", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Opponent crosses", "column": "Opponent's crosses", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00", "score_include": False},
        ],
    },
    "Sweeping": {
        "color": "#A855F7",
        "icon": "↗",
        "metrics": [
            {"label": "Sweeping actions", "column": "Sweeping actions", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Successful sweeping", "column": "Sweeping actions successful", "kind": "volume", "adjustment": "off_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Sweeping success %", "column": "Sweeping actions successful, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Sweeping unsuccessful", "column": "Sweeping actions unsuccessful", "kind": "negative", "adjustment": "off_ball", "higher_is_better": False, "fmt": "0.00"},
        ],
    },
    "Distribution": {
        "color": "#2DD4FF",
        "icon": "➤",
        "metrics": [
            {"label": "Passes", "column": "Passes", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Pass accuracy %", "column": "Passes accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Open play passes", "column": "Open play passes", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Open play pass accuracy %", "column": "Open play passes accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Progressive open passes", "column": "Progressive open passes", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Long passes", "column": "Long passes", "kind": "volume", "adjustment": "on_ball", "higher_is_better": True, "fmt": "0.00"},
            {"label": "Long pass accuracy %", "column": "Long passes accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Goal-kick accuracy %", "column": "Goal kicks accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Throws accuracy %", "column": "Throws accurate, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Long distribution share", "column": "Long distribution share", "kind": "style", "adjustment": "none", "higher_is_better": True, "fmt": "%", "score_include": False},
        ],
    },
    "Security": {
        "color": "#FF4F6D",
        "icon": "🛡",
        "metrics": [
            {"label": "Actions successful %", "column": "Actions successful, %", "kind": "quality", "adjustment": "none", "higher_is_better": True, "fmt": "%"},
            {"label": "Mistakes to chances", "column": "Mistakes leading to chances", "kind": "negative", "adjustment": "none", "higher_is_better": False, "fmt": "0.00"},
            {"label": "Mistakes to goals", "column": "Mistakes leading to goals", "kind": "negative", "adjustment": "none", "higher_is_better": False, "fmt": "0.00"},
            {"label": "Yellow cards", "column": "Yellow cards", "kind": "negative", "adjustment": "none", "higher_is_better": False, "fmt": "0.00"},
            {"label": "Red cards", "column": "Red cards", "kind": "negative", "adjustment": "none", "higher_is_better": False, "fmt": "0.00"},
        ],
    },
}

GK_RADAR_AXES = [
    {
        "axis": "Shot Stopping",
        "style": [
            {"column": "Shots on target faced", "adjustment": "off_ball", "higher_is_better": True},
            {"column": "Opponent's shots xG", "adjustment": "off_ball", "higher_is_better": True},
        ],
        "performance": [
            {"column": "Goals prevented", "adjustment": "none", "higher_is_better": True},
            {"column": "Goals prevented, %", "adjustment": "none", "higher_is_better": True},
            {"column": "Shots saved, %", "adjustment": "none", "higher_is_better": True},
        ],
    },
    {
        "axis": "Handling",
        "style": [
            {"column": "Caught shots", "adjustment": "off_ball", "higher_is_better": True},
            {"column": "Parried shots to safety", "adjustment": "off_ball", "higher_is_better": True},
        ],
        "performance": [
            {"column": "Caught shots, %", "adjustment": "none", "higher_is_better": True},
            {"column": "Parried shots to safety, %", "adjustment": "none", "higher_is_better": True},
            {"column": "Parried shots into danger, %", "adjustment": "none", "higher_is_better": False},
        ],
    },
    {
        "axis": "Cross Command",
        "style": [
            {"column": "Opponent's crosses", "adjustment": "off_ball", "higher_is_better": True},
            {"column": "Cross and pass interception attempts", "adjustment": "off_ball", "higher_is_better": True},
        ],
        "performance": [
            {"column": "Cross claim rate", "adjustment": "none", "higher_is_better": True},
            {"column": "Successful cross and pass interception attempts, %", "adjustment": "none", "higher_is_better": True},
        ],
    },
    {
        "axis": "Sweeping",
        "style": [
            {"column": "Sweeping actions", "adjustment": "off_ball", "higher_is_better": True},
        ],
        "performance": [
            {"column": "Sweeping actions successful, %", "adjustment": "none", "higher_is_better": True},
            {"column": "Sweeping actions unsuccessful", "adjustment": "off_ball", "higher_is_better": False},
        ],
    },
    {
        "axis": "Build-up",
        "style": [
            {"column": "Passes", "adjustment": "on_ball", "higher_is_better": True},
            {"column": "Open play passes", "adjustment": "on_ball", "higher_is_better": True},
        ],
        "performance": [
            {"column": "Passes accurate, %", "adjustment": "none", "higher_is_better": True},
            {"column": "Open play passes accurate, %", "adjustment": "none", "higher_is_better": True},
        ],
    },
    {
        "axis": "Long Distribution",
        "style": [
            {"column": "Long passes", "adjustment": "on_ball", "higher_is_better": True},
            {"column": "Goal kicks long (40+ m)", "adjustment": "on_ball", "higher_is_better": True},
        ],
        "performance": [
            {"column": "Long passes accurate, %", "adjustment": "none", "higher_is_better": True},
            {"column": "Goal kicks long (40+ m) accurate, %", "adjustment": "none", "higher_is_better": True},
        ],
    },
]
