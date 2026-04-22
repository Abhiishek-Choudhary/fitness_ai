from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import FitnessProfile
from .serializers import FitnessProfileSerializer


class FitnessProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.fitness_profile
            serializer = FitnessProfileSerializer(profile)
            return Response(serializer.data)
        except FitnessProfile.DoesNotExist:
            return Response(
                {"detail": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        try:
            profile = request.user.fitness_profile
            serializer = FitnessProfileSerializer(
                profile, data=request.data
            )
        except FitnessProfile.DoesNotExist:
            serializer = FitnessProfileSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {"message": "Profile saved successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import FitnessAIPlan, UserPrompt
from .services.ai_fitness_plan import generate_fitness_plan
from .services.calories import calculate_bmr, calculate_tdee, adjust_calories_for_goal


class FitnessAIPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # 1️⃣ Get latest prompt
        try:
            prompt = UserPrompt.objects.filter(user=user).latest("created_at")
        except UserPrompt.DoesNotExist:
            return Response(
                {"error": "No prompt found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2️⃣ Get fitness profile
        try:
            profile = user.fitness_profile
        except FitnessProfile.DoesNotExist:
            return Response(
                {
                    "error": "Fitness profile not found. Please create your profile first via POST /api/fitness/profile/"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3️⃣ Calculate calories
        bmr = calculate_bmr(
            profile.age,
            profile.gender,
            profile.height_cm,
            profile.weight_kg
        )
        tdee = calculate_tdee(bmr, profile.activity_level)
        calorie_target = adjust_calories_for_goal(tdee, profile.fitness_goal)

        # 4️⃣ Build AI payload (STRUCTURED)
        ai_payload = {
            "primary_goal": prompt.primary_goal,
            "secondary_goal": prompt.secondary_goal,
            "duration_weeks": prompt.duration_weeks,
            "age": profile.age,
            "gender": profile.gender,
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg,
            "activity_level": profile.activity_level,
            "fitness_goal": profile.fitness_goal,
            "daily_calorie_target": calorie_target
        }

        # 5️⃣ Call Gemini
        try:
            ai_plan = generate_fitness_plan(ai_payload)
        except Exception as e:
            return Response(
                {"error": "AI generation failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 6️⃣ Save plan
        plan = FitnessAIPlan.objects.create(user=user)
        plan.set_plan(ai_plan)
        plan.save()

        return Response(
            {
                "calorie_target": calorie_target,
                "ai_plan": ai_plan
            },
            status=status.HTTP_200_OK
        )


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import FitnessAIPlan


class FitnessAIPlanGetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        section = request.query_params.get("section", "summary")

        plan = FitnessAIPlan.objects.filter(user=user).first()

        if not plan:
            return Response(
                {"error": "No AI plan found"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = plan.get_plan()

        response = self.filter_plan(data, section)

        return Response(response, status=status.HTTP_200_OK)

    def filter_plan(self, data: dict, section: str) -> dict:
        """Return only requested sections"""

        macros = data.get("macros", {})

        nutrition = {
            "daily_calories": data.get("daily_calories"),
            "protein_grams": macros.get("protein_grams"),
            "carbohydrates_grams": macros.get("carbohydrates_grams"),
            "fats_grams": macros.get("fats_grams"),
        }

        workout = {
            "weekly_workout_plan": data.get("weekly_workout_plan", [])
        }

        cardio = {
            "cardio_plan": data.get("cardio_plan", {})
        }

        diet = {
            "foods_to_eat": data.get("foods_to_eat", []),
            "foods_to_avoid": data.get("foods_to_avoid", [])
        }

        if section == "nutrition":
            return nutrition

        if section == "workout":
            return workout

        if section == "cardio":
            return cardio

        if section == "diet":
            return diet

        if section == "full":
            return {
                **nutrition,
                **workout,
                **cardio,
                **diet,
                "safety_notes": data.get("safety_notes", [])
            }

        # default summary
        return {
            **nutrition,
            **workout,
            **cardio,
            **diet
        }


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import FitnessAIPlan, UserPrompt
from .services.calories import calculate_bmr, calculate_tdee, adjust_calories_for_goal
from .services.ai_fitness_plan import generate_fitness_plan  # your AI service

class FitnessAIPlanRegenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # 1️⃣ Get latest prompt
        try:
            prompt = UserPrompt.objects.filter(user=user).latest("created_at")
        except UserPrompt.DoesNotExist:
            return Response(
                {"error": "No prompt found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2️⃣ Get fitness profile
        try:
            profile = user.fitness_profile
        except FitnessProfile.DoesNotExist:
            return Response(
                {
                    "error": "Fitness profile not found. Please create your profile first via POST /api/fitness/profile/"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3️⃣ Recalculate calories
        bmr = calculate_bmr(profile.age, profile.gender, profile.height_cm, profile.weight_kg)
        tdee = calculate_tdee(bmr, profile.activity_level)
        calorie_target = adjust_calories_for_goal(tdee, profile.fitness_goal)

        # 4️⃣ Build AI payload
        ai_payload = {
            "primary_goal": prompt.primary_goal,
            "secondary_goal": prompt.secondary_goal,
            "duration_weeks": prompt.duration_weeks,
            "age": profile.age,
            "gender": profile.gender,
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg,
            "activity_level": profile.activity_level,
            "fitness_goal": profile.fitness_goal,
            "daily_calorie_target": calorie_target
        }

        # 5️⃣ Call AI
        try:
            new_plan = generate_fitness_plan(ai_payload)
        except Exception as e:
            return Response(
                {"error": "AI generation failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 6️⃣ Save new plan in DB
        plan = FitnessAIPlan.objects.create(user=user)
        plan.set_plan(new_plan)
        plan.save()

        # 7️⃣ Filter response
        filtered_response = {
            "daily_calories": new_plan.get("daily_calories"),
            "macros": new_plan.get("macros"),
            "weekly_workout_plan": new_plan.get("weekly_workout_plan"),
            "cardio_plan": new_plan.get("cardio_plan"),
            "foods_to_eat": new_plan.get("foods_to_eat"),
            "foods_to_avoid": new_plan.get("foods_to_avoid")
        }

        return Response(
            {
                "calorie_target": calorie_target,
                "ai_plan": filtered_response
            },
            status=status.HTTP_200_OK
        )

    
from .models import UserPrompt
from .services.prompt_parser import parse_prompt
from .serializers import PromptSerializer


class PromptIntakeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PromptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prompt_text = serializer.validated_data["prompt"]

        parsed_data = parse_prompt(prompt_text)

        UserPrompt.objects.create(
            user=request.user,
            prompt_text=prompt_text,
            primary_goal=parsed_data["primary_goal"] or "",
            secondary_goal=parsed_data["secondary_goal"] or "",
            duration_weeks=parsed_data["duration_weeks"]
        )

        return Response({
            "prompt": prompt_text,
            "parsed_data": parsed_data
        })

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import FitnessProfile
from .services.calories import calculate_bmr, calculate_tdee, adjust_calories_for_goal


class CalorieCalculatorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.fitness_profile
        except FitnessProfile.DoesNotExist:
            return Response({"detail": "Fitness profile not found."}, status=404)

        try:
            bmr = calculate_bmr(profile.age, profile.gender, profile.height_cm, profile.weight_kg)
            tdee = calculate_tdee(bmr, profile.activity_level)
            calorie_target = adjust_calories_for_goal(tdee, profile.fitness_goal)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response({
            "BMR": bmr,
            "TDEE": tdee,
            "calorie_target": calorie_target
        })

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from workout.models import WorkoutSession
from .services.calories import calculate_bmr, calculate_tdee, adjust_calories_for_goal


class NetCaloriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.fitness_profile
        except FitnessProfile.DoesNotExist:
            return Response({"error": "Fitness profile not found"}, status=404)

        # Step 1: Calculate BMR, TDEE, and Calorie Target
        try:
            bmr = calculate_bmr(profile.age, profile.gender, profile.height_cm, profile.weight_kg)
            tdee = calculate_tdee(bmr, profile.activity_level)
            calorie_target = adjust_calories_for_goal(tdee, profile.fitness_goal)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        # Step 2: Sum calories burned today
        today = timezone.now().date()
        sessions_today = WorkoutSession.objects.filter(user=request.user, date=today)
        calories_burned_today = sum([session.calories_burned for session in sessions_today])

        # Step 3: Calculate net calories
        net_calories = round(calorie_target - calories_burned_today, 2)

        return Response({
            "BMR": bmr,
            "TDEE": tdee,
            "calorie_target": calorie_target,
            "calories_burned_today": calories_burned_today,
            "net_calories": net_calories
        })
