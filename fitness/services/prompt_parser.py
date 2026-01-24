import re


def parse_prompt(prompt: str):
    prompt_lower = prompt.lower()

    primary_goal = None
    secondary_goal = None
    duration_weeks = None

    if "lose" in prompt_lower or "fat" in prompt_lower:
        primary_goal = "WEIGHT_LOSS"

    if "muscle" in prompt_lower or "gain" in prompt_lower:
        secondary_goal = "MUSCLE_GAIN"

    if "stamina" in prompt_lower or "endurance" in prompt_lower:
        secondary_goal = "ENDURANCE"

    match = re.search(r'(\d+)\s*(week|weeks|month|months)', prompt_lower)
    if match:
        value = int(match.group(1))
        unit = match.group(2)

        if "month" in unit:
            duration_weeks = value * 4
        else:
            duration_weeks = value

    return {
        "primary_goal": primary_goal,
        "secondary_goal": secondary_goal,
        "duration_weeks": duration_weeks
    }
