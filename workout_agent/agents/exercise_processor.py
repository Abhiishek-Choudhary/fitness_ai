import re
import unicodedata

def extract_and_normalize_exercises(raw_exercises):
    """
    Input: list of raw exercise strings
    Output: list of normalized exercises (split combos, clean names)
    """
    processed = []

    for raw in raw_exercises:
        # Step 1: Extract sets/reps
        sets_reps_match = re.search(r'\((.*?)\)', raw)
        sets_reps_text = sets_reps_match.group(1) if sets_reps_match else None

        # Remove sets/reps from the raw string
        exercise_text = re.sub(r'\(.*?\)', '', raw).strip()

        # Step 2: Split combo exercises
        combos = re.split(r'/|&', exercise_text)

        # Step 3: Split sets/reps if multiple in combo
        # If sets_reps has '/' we split it as well
        sets_reps_list = [s.strip() for s in sets_reps_text.split('/')] if sets_reps_text else [None]

        for i, ex in enumerate(combos):
            name = normalize_exercise_name(ex)
            sr = sets_reps_list[i] if i < len(sets_reps_list) else None

            processed.append({
                "exercise_id": name.lower().replace(" ", "_"),
                "display_name": name,
                "sets_reps": sr,
                "raw": raw
            })

    return processed


def normalize_exercise_name(name):
    """
    Clean exercise name for search purposes:
    - Remove hyphens
    - Title case
    - Singularize simple plurals
    """
    name = unicodedata.normalize("NFKD", name)  # normalize unicode
    name = name.replace("-", " ").strip()

    # Basic singularization
    if name.lower().endswith("s") and len(name) > 3:
        name = name[:-1]

    # Title case
    name = " ".join([w.capitalize() for w in name.split()])

    return name


# === Example usage ===
if __name__ == "__main__":
    raw_list = [
        "Incline Dumbbell Press (3 sets x 10 reps)",
        "Pull-Ups/Lat Pulldowns (3 sets x failure/12 reps)",
        "Romanian Deadlifts (4 sets x 8 reps)"
    ]

    exercises = extract_and_normalize_exercises(raw_list)
    for e in exercises:
        print(e)
