"""Shared final sleep-stage metadata for the current report workflows."""

LABEL_NAMES = {
    1: "nrem",
    2: "rem",
    3: "ma",
    4: "high_alertness",
    5: "low_alertness",
}

STATE_LABELS = {
    "nrem": "NREM",
    "rem": "REM",
    "ma": "MA",
    "high_alertness": "High Alertness",
    "low_alertness": "Low Alertness",
}

# Shared PI-facing palette. High/Low Alertness are saturated; NREM/REM are muted.
STAGE_COLORS = {
    "nrem": "#77739A",
    "rem": "#9BBF9A",
    "ma": "#FFFF00",
    "high_alertness": "#E31A1C",
    "low_alertness": "#0072B2",
}

STAGE_COLORS_RGB = {
    "nrem": (119, 115, 154),
    "rem": (155, 191, 154),
    "ma": (255, 255, 0),
    "high_alertness": (227, 26, 28),
    "low_alertness": (0, 114, 178),
}
