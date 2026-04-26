import os
import json
from google import genai
from PIL import Image

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.0-flash"

def analyze_food_image(image_path: str):
    image = Image.open(image_path)

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

    response = _client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt, image],
    )

    return json.loads(response.text)
