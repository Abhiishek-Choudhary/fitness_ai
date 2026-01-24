import os
import json
import re
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are a certified fitness coach and nutritionist.
Return ONLY valid JSON.
Do not include markdown or explanations.
"""

def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("Invalid JSON returned by Gemini")
        return json.loads(match.group())

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

    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=prompt
    )

    return extract_json(response.text)
