from __future__ import annotations

# Goalkeeper style metrics for offline clustering.
#
# Philosophy:
# - This is not a "best goalkeeper" clustering.
# - It tries to separate playing-style archetypes:
#   shot volume context, handling tendency, sweeper activity, cross/interception activity,
#   and distribution profile.
# - The script automatically skips missing columns and reports coverage.

GK_STYLE_CLUSTER_METRICS: list[str] = [
    # Shot context / workload
    "Shots faced",
    "Shots on target faced",
    "Opponent's close-range shots",
    "Opponent's mid-range shots",
    "Opponent's long-range shots",
    "Opponent's close-range shots on target",
    "Opponent's mid-range shots on target",
    "Opponent's long-range shots on target",
    "Opponent's shots xG",
    "xG per opponent's shot",

    # Handling / rebound style
    "Caught shots",
    "Parried shots to safety",
    "Parried shots into danger",
    "Caught shots, %",
    "Parried shots to safety, %",
    "Parried shots into danger, %",

    # Crosses / command of area
    "Opponent's crosses",
    "Cross and pass interception attempts",
    "Successful cross and pass interception attempts",

    # Sweeper keeper behaviour
    "Sweeping actions",
    "Sweeping actions successful",
    "Sweeping actions unsuccessful",

    # Distribution style
    "Passes",
    "Open play passes",
    "Throws",
    "Passes from set pieces",
    "Goal kicks",
    "Long passes",
    "Progressive open passes",
    "Short passes",
    "Medium passes",
    "Goal kicks short (<15 m)",
    "Goal kicks medium (15-40 m)",
    "Goal kicks long (40+ m)",

    # Derived distribution shares
    "Long pass share",
    "Open play pass share",
    "Set-piece pass share",
    "Goal kick long share",
    "Goal kick short-medium share",
    "Throw share",

    # Risk / activity
    "Actions",
    "Actions unsuccessful",
    "Mistakes leading to chances",
    "Mistakes leading to goals",
]

DEFAULT_GK_K: int = 5
