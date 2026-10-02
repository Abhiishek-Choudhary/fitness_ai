import logging

from fitness_ai.ai import generate

logger = logging.getLogger(__name__)

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
        return generate(prompt)
    except Exception:
        logger.warning('Gemini posture feedback unavailable, using rule-based advice', exc_info=True)
        return _rule_based_feedback(exercise, score, issues)
