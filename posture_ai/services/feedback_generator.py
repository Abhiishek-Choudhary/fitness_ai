from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = """
You are a professional fitness coach.
You explain exercise posture feedback based only on provided data.
Do not guess or add new issues.
Keep advice encouraging and practical.
"""

def generate_feedback(exercise, score, issues, metrics):
    prompt = f"""
Exercise: {exercise}
Score: {score}/100
Detected issues: {issues}
Metrics: {metrics}

Explain:
1. What went wrong
2. Why it matters
3. How to fix it
4. One simple cue
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
