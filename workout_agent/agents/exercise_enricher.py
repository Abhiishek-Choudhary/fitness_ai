from workout_agent.agents.exercise_processor import extract_and_normalize_exercises
from workout_agent.services.youtube_service import search_exercise_video

def enrich_workout_plan(ai_plan):
    """
    Input: Gemini AI JSON plan
    Output: Video-enriched weekly workout plan
    """
    enriched_plan = []

    weekly_plan = ai_plan.get("weekly_workout_plan", [])

    for day_plan in weekly_plan:
        day_name = day_plan.get("day")
        raw_exercises = day_plan.get("exercises", [])

        # Step 1: Extract & normalize exercises
        exercises = extract_and_normalize_exercises(raw_exercises)

        # Step 2: Enrich each exercise with video
        for ex in exercises:
            videos = search_exercise_video(ex["display_name"])
            ex["videos"] = videos

        # Step 3: Append enriched day
        enriched_plan.append({
            "day": day_name,
            "focus": day_plan.get("focus"),
            "duration_minutes": day_plan.get("duration_minutes"),
            "notes": day_plan.get("notes"),
            "exercises": exercises
        })

    # Return enriched plan
    return {
        "calorie_target": ai_plan.get("calorie_target"),
        "weekly_workout_plan": enriched_plan,
        "macros": ai_plan.get("macros"),
        "cardio_plan": ai_plan.get("cardio_plan"),
        "foods_to_eat": ai_plan.get("foods_to_eat"),
        "foods_to_avoid": ai_plan.get("foods_to_avoid"),
        "safety_notes": ai_plan.get("safety_notes")
    }
