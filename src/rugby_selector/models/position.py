PLAYING_POSITION_NAMES = (
    "Prop",
    "Hooker",
    "Prop",
    "Second Row",
    "Second Row",
    "Flanker",
    "Flanker",
    "No 8.",
    "Scrum Half",
    "Fly Half",
    "Wing",
    "Centre",
    "Centre",
    "Wing",
    "Full Back",
)
PLAYING_POSITION_COUNT = len(PLAYING_POSITION_NAMES)


def position_name(position: int) -> str:
    """Return the rugby name for a playing position or bench position."""
    if 1 <= position <= PLAYING_POSITION_COUNT:
        return PLAYING_POSITION_NAMES[position - 1]
    return "Bench"


def position_label(position: int) -> str:
    """Return the user-facing rugby position label."""
    return position_name(position)
