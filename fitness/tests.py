from django.test import TestCase
from .services.calories import calculate_bmr, calculate_tdee, adjust_calories_for_goal
from .services.prompt_parser import parse_prompt


# ---------------------------------------------------------------------------
# BMR Tests
# ---------------------------------------------------------------------------

class TestCalculateBMR(TestCase):

    def test_male_bmr(self):
        result = calculate_bmr(age=25, gender='male', height_cm=175, weight_kg=70)
        # (10*70) + (6.25*175) - (5*25) + 5 = 700 + 1093.75 - 125 + 5 = 1673.75
        self.assertAlmostEqual(result, 1673.75)

    def test_female_bmr(self):
        result = calculate_bmr(age=30, gender='female', height_cm=165, weight_kg=60)
        # (10*60) + (6.25*165) - (5*30) - 161 = 600 + 1031.25 - 150 - 161 = 1320.25
        self.assertAlmostEqual(result, 1320.25)

    def test_gender_case_insensitive(self):
        upper = calculate_bmr(age=25, gender='Male', height_cm=175, weight_kg=70)
        lower = calculate_bmr(age=25, gender='male', height_cm=175, weight_kg=70)
        self.assertEqual(upper, lower)

    def test_invalid_gender_raises(self):
        with self.assertRaises(ValueError):
            calculate_bmr(age=25, gender='other', height_cm=175, weight_kg=70)

    def test_returns_float(self):
        result = calculate_bmr(age=25, gender='male', height_cm=175, weight_kg=70)
        self.assertIsInstance(result, float)


# ---------------------------------------------------------------------------
# TDEE Tests
# ---------------------------------------------------------------------------

class TestCalculateTDEE(TestCase):

    def test_sedentary(self):
        result = calculate_tdee(bmr=1600.0, activity_level='sedentary')
        self.assertAlmostEqual(result, round(1600.0 * 1.2, 2))

    def test_light(self):
        result = calculate_tdee(bmr=1600.0, activity_level='light')
        self.assertAlmostEqual(result, round(1600.0 * 1.375, 2))

    def test_moderate(self):
        result = calculate_tdee(bmr=1600.0, activity_level='moderate')
        self.assertAlmostEqual(result, round(1600.0 * 1.55, 2))

    def test_heavy(self):
        result = calculate_tdee(bmr=1600.0, activity_level='heavy')
        self.assertAlmostEqual(result, round(1600.0 * 1.725, 2))

    def test_athlete(self):
        result = calculate_tdee(bmr=1600.0, activity_level='athlete')
        self.assertAlmostEqual(result, round(1600.0 * 1.9, 2))

    def test_activity_level_case_insensitive(self):
        upper = calculate_tdee(bmr=1600.0, activity_level='Moderate')
        lower = calculate_tdee(bmr=1600.0, activity_level='moderate')
        self.assertEqual(upper, lower)

    def test_invalid_activity_level_raises(self):
        with self.assertRaises(ValueError):
            calculate_tdee(bmr=1600.0, activity_level='superhuman')


# ---------------------------------------------------------------------------
# Goal Adjustment Tests
# ---------------------------------------------------------------------------

class TestAdjustCaloriesForGoal(TestCase):

    def test_weight_loss_deducts_500(self):
        result = adjust_calories_for_goal(tdee=2000.0, goal='WEIGHT_LOSS')
        self.assertAlmostEqual(result, 1500.0)

    def test_muscle_gain_adds_400(self):
        result = adjust_calories_for_goal(tdee=2000.0, goal='MUSCLE_GAIN')
        self.assertAlmostEqual(result, 2400.0)

    def test_general_fitness_unchanged(self):
        result = adjust_calories_for_goal(tdee=2000.0, goal='GENERAL_FITNESS')
        self.assertAlmostEqual(result, 2000.0)

    def test_endurance_unchanged(self):
        result = adjust_calories_for_goal(tdee=2000.0, goal='ENDURANCE')
        self.assertAlmostEqual(result, 2000.0)

    def test_goal_case_insensitive(self):
        result = adjust_calories_for_goal(tdee=2000.0, goal='weight_loss')
        self.assertAlmostEqual(result, 1500.0)

    def test_invalid_goal_raises(self):
        with self.assertRaises(ValueError):
            adjust_calories_for_goal(tdee=2000.0, goal='BULK')


# ---------------------------------------------------------------------------
# Prompt Parser Tests
# ---------------------------------------------------------------------------

class TestParsePrompt(TestCase):

    def test_weight_loss_primary_goal(self):
        result = parse_prompt("I want to lose weight and burn fat")
        self.assertEqual(result['primary_goal'], 'WEIGHT_LOSS')

    def test_muscle_gain_secondary_goal(self):
        result = parse_prompt("I want to lose fat but also gain muscle")
        self.assertEqual(result['primary_goal'], 'WEIGHT_LOSS')
        self.assertEqual(result['secondary_goal'], 'MUSCLE_GAIN')

    def test_endurance_secondary_goal(self):
        result = parse_prompt("I want to lose weight and build endurance")
        self.assertEqual(result['secondary_goal'], 'ENDURANCE')

    def test_stamina_maps_to_endurance(self):
        result = parse_prompt("Improve my stamina")
        self.assertEqual(result['secondary_goal'], 'ENDURANCE')

    def test_duration_in_weeks(self):
        result = parse_prompt("I want to lose weight in 8 weeks")
        self.assertEqual(result['duration_weeks'], 8)

    def test_duration_in_months_converted_to_weeks(self):
        result = parse_prompt("Lose fat in 3 months")
        self.assertEqual(result['duration_weeks'], 12)

    def test_no_duration_returns_none(self):
        result = parse_prompt("I want to lose weight")
        self.assertIsNone(result['duration_weeks'])

    def test_no_goal_returns_none(self):
        result = parse_prompt("I want to stay healthy")
        self.assertIsNone(result['primary_goal'])

    def test_returns_dict_with_required_keys(self):
        result = parse_prompt("some prompt")
        self.assertIn('primary_goal', result)
        self.assertIn('secondary_goal', result)
        self.assertIn('duration_weeks', result)
