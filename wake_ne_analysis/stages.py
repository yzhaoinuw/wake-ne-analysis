"""Shared final sleep-stage metadata for the current report workflows."""

LABEL_NAMES = {
    1: "nrem",
    2: "rem",
    3: "ma",
    4: "active_wake",
    5: "quiet_wake",
}

STATE_LABELS = {
    "nrem": "NREM",
    "rem": "REM",
    "ma": "MA",
    "active_wake": "Active Wake",
    "quiet_wake": "Quiet Wake",
}

# Exact RGB values from the upstream sleep-scoring display configuration.
STAGE_COLORS = {
    "nrem": "#FB7C7C",
    "rem": "#7BFB7B",
    "ma": "#FFFF00",
    "active_wake": "#E69F00",
    "quiet_wake": "#56B4E9",
}
