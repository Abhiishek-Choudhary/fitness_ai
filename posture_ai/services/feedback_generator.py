import os
from google import genai
from google.genai.errors import ClientError

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are a professional fitness coach.
You explain exercise posture feedback based only on provided data.
Do not guess or add new issues.
Keep advice encouraging and practical."""

_ISSUE_ADVICE = {
    "Insufficient elbow bend": (
        "Your elbows didn't bend enough during the push-up. "
        "Full range of motion builds more strength and muscle. "
        "Aim to lower your chest until your upper arms are parallel to the floor. "
        "Cue: 'chest to the floor'."
    ),
    "Hip sag detected": (
        "Your hips dropped during the movement. "
        "This strains your lower back and removes core engagement. "
        "Squeeze your glutes and brace your core to keep your body in a straight line. "
        "Cue: 'squeeze your glutes'."
    ),
}

def _rule_based_feedback(exercise, score, issues):
    if not issues:
        return (
            f"Great {exercise.replace('_', ' ')}! Score: {score}/100. "
            "Your form looks solid — keep it up."
        )
    parts = [f"Here's feedback on your {exercise.replace('_', ' ')} (score: {score}/100):\n"]
    for i, issue in enumerate(issues, 1):
        advice = _ISSUE_ADVICE.get(issue, f"Work on correcting: {issue}.")
        parts.append(f"{i}. {advice}")
    return "\n".join(parts)

def generate_feedback(exercise, score, issues, metrics):
    prompt = f"""{SYSTEM_PROMPT}

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
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except (ClientError, Exception):
        return _rule_based_feedback(exercise, score, issues)
