# fitness/services/calories.py

def calculate_bmr(age: int, gender: str, height_cm: float, weight_kg: float) -> float:
    """
    Calculate Basal Metabolic Rate (BMR) using Mifflin-St Jeor formula.
    """
    gender = gender.lower()
    if gender == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    elif gender == "female":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        raise ValueError("Gender must be 'male' or 'female'")
    return round(bmr, 2)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Calculate Total Daily Energy Expenditure (TDEE) by applying activity multiplier.
    """
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "heavy": 1.725,
        "athlete": 1.9,
    }

    activity_level = activity_level.lower()
    multiplier = activity_multipliers.get(activity_level)
    if not multiplier:
        raise ValueError(f"Invalid activity level. Choose from {list(activity_multipliers.keys())}")

    tdee = bmr * multiplier
    return round(tdee, 2)


def adjust_calories_for_goal(tdee: float, goal: str) -> float:
    goal = goal.upper()
    if goal == "WEIGHT_LOSS":
        return round(tdee - 500, 2)
    elif goal == "MUSCLE_GAIN":
        return round(tdee + 400, 2)
    elif goal in ["GENERAL_FITNESS", "ENDURANCE"]:
        return tdee
    else:
        raise ValueError("Goal must be one of the fitness profile choices")
