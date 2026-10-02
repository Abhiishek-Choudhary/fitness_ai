from fitness_ai.ai import extract_json, generate


def analyze_food_image(image_path: str):
    prompt = """
    You are a food nutrition assistant.

    Analyze the food image and return ONLY valid JSON:

    {
      "items": [
        {
          "name": "food name",
          "estimated_quantity": "quantity with unit"
        }
      ]
    }

    Rules:
    - Detect cooked food
    - Use common household units
    - Do not add explanations
    - Do not add markdown
    """

    return extract_json(generate(prompt, image_path=image_path))
