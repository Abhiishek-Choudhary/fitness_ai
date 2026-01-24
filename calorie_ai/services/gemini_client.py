import os
import json
import google.generativeai as genai
from PIL import Image

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "models/gemini-flash-latest"

def analyze_food_image(image_path: str):
    model = genai.GenerativeModel(MODEL_NAME)

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

    response = model.generate_content([prompt, image])

    return json.loads(response.text)
