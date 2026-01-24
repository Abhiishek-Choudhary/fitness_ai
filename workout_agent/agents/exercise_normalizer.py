EXERCISE_ALIASES = {
    "incline dumbbell press": {
        "id": "incline_dumbbell_press",
        "display_name": "Incline Dumbbell Press"
    },
    "pull up": {
        "id": "pull_up",
        "display_name": "Pull-Up"
    },
    "lat pulldown": {
        "id": "lat_pulldown",
        "display_name": "Lat Pulldown"
    }
}

def normalize_exercise(name: str):
    key = name.lower().strip()
    if key in EXERCISE_ALIASES:
        return EXERCISE_ALIASES[key]

    return {
        "id": key.replace(" ", "_"),
        "display_name": name.title()
    }
