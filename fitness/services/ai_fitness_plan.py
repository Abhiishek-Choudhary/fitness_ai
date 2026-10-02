import json

from fitness_ai.ai import extract_json, generate

SYSTEM_PROMPT = """
You are a certified fitness coach and nutritionist.
Return ONLY valid JSON.
Do not include markdown or explanations.
"""


def generate_fitness_plan(payload: dict) -> dict:
    prompt = f"""
{SYSTEM_PROMPT}

User fitness data:
{json.dumps(payload, indent=2)}

Generate a fitness plan with:
- daily_calories
- macros
- weekly_workout_plan
- cardio_plan
- foods_to_eat
- foods_to_avoid
- safety_notes
"""

    return extract_json(generate(prompt))
