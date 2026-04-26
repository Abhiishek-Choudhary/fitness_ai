"""Generate AI-powered improvement suggestions using Gemini."""
import os
import json
from google import genai

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))


def generate_ai_analysis(report_data: dict, period: str, period_start: str, period_end: str) -> str:
    profile = report_data['profile']
    workouts = report_data['workouts']['stats']
    nutrition = report_data['nutrition']['stats']
    progress = report_data['progress']
    balance = report_data['calorie_balance']

    prompt = f"""
You are an expert fitness coach and nutritionist. Analyze the following {period} fitness data
for {period_start} to {period_end} and provide a structured, actionable improvement report.

## User Profile
- Age: {profile.get('age', 'N/A')} | Gender: {profile.get('gender', 'N/A')}
- Height: {profile.get('height_cm', 'N/A')} cm | Weight: {profile.get('weight_kg', 'N/A')} kg
- Goal: {profile.get('fitness_goal', 'N/A')} | Level: {profile.get('fitness_level', 'N/A')}
- Activity Level: {profile.get('activity_level', 'N/A')}

## Workout Summary
- Total Sessions: {workouts['total_sessions']}
- Total Duration: {workouts['total_minutes']} minutes
- Total Calories Burned: {workouts['total_calories_burned']} kcal
- Workout Types: {json.dumps(report_data['workouts']['by_type'], indent=2)}

## Nutrition Summary
- Total Calories Consumed: {nutrition['total_calories_in']} kcal
- Avg Daily Calories: {nutrition['avg_daily_calories']} kcal
- Total Protein: {nutrition['total_protein']} g
- Total Carbs: {nutrition['total_carbs']} g
- Total Fat: {nutrition['total_fat']} g
- Days with food logs: {nutrition['days_with_food_log']}

## Progress
- Start Weight: {progress['start_weight']} kg
- End Weight: {progress['end_weight']} kg
- Weight Change: {progress['weight_change']} kg

## Calorie Balance
- Consumed: {balance['total_consumed']} kcal
- Burned: {balance['total_burned']} kcal
- Net: {balance['net']} kcal

Provide your response in the following exact sections:

**OVERALL ASSESSMENT**
[2-3 sentences on overall performance this period]

**WHAT YOU DID WELL**
[3-4 bullet points of specific positives]

**AREAS TO IMPROVE**
[3-4 bullet points of specific, actionable improvements]

**WORKOUT RECOMMENDATIONS**
[3-4 specific workout adjustments for next period]

**NUTRITION RECOMMENDATIONS**
[3-4 specific dietary changes with numbers where possible]

**NEXT PERIOD GOALS**
[3 SMART goals for the next {period}]

Keep language motivating, specific, and based only on the data provided.
""".strip()

    try:
        response = _client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return (
            f"AI analysis could not be generated at this time ({str(e)}). "
            "Please review your data above and consult your fitness plan for guidance."
        )
