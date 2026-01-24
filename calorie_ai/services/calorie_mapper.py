CALORIE_DATABASE = {

    # 🍚 Rice & grains
    "steamed rice": 200,          # per cup
    "jeera rice": 220,            # per cup
    "fried rice": 300,            # per cup
    "brown rice": 180,            # per cup
    "quinoa": 220,                # per cup
    "oats": 150,                  # per 40g dry

    # 🫓 Indian breads
    "roti": 100,                  # per medium
    "chapati": 100,               # per medium
    "paratha": 250,               # per piece
    "layered paratha": 280,       # per piece
    "naan": 260,                  # per piece
    "butter naan": 320,           # per piece

    # 🍛 Indian curries & dals
    "dal": 180,                   # per cup
    "dal tadka": 200,             # per cup
    "rajma": 240,                 # per cup
    "chole": 260,                 # per cup
    "paneer curry": 300,          # per 150g
    "paneer butter masala": 350,  # per cup
    "vegetable curry": 180,       # per cup
    "chicken curry": 220,         # per 150g
    "butter chicken": 350,        # per cup
    "egg curry": 220,             # per cup
    "fish curry": 250,            # per cup

    # 🥩 Protein (fitness-focused)
    "boiled egg": 78,             # per egg
    "fried egg": 90,              # per egg
    "egg white": 17,              # per egg
    "grilled chicken": 165,       # per 100g
    "boiled chicken": 150,        # per 100g
    "paneer": 265,                # per 100g
    "tofu": 80,                   # per 100g
    "boiled fish": 120,           # per 100g

    # 🥗 Vegetables (low calorie)
    "salad": 80,                  # per bowl
    "mixed vegetables": 150,      # per cup
    "tomato": 20,                 # per medium
    "tomato slices": 10,          # per few slices
    "onion": 40,                  # per medium
    "onion slices": 10,           # per few slices
    "cucumber": 16,               # per cup
    "spinach": 20,                # per cup
    "broccoli": 55,               # per cup

    # 🍎 Fruits
    "apple": 95,                  # per medium
    "banana": 105,                # per medium
    "orange": 62,                 # per medium
    "mango": 135,                 # per cup
    "papaya": 60,                 # per cup
    "watermelon": 45,             # per cup

    # 🍔 Fast food
    "burger": 300,                # per regular
    "cheese burger": 350,         # per regular
    "pizza slice": 285,           # per slice
    "french fries": 365,          # per medium serving
    "sandwich": 250,              # per serving
    "grilled sandwich": 300,      # per serving
    "pasta": 350,                 # per cup
    "white sauce pasta": 400,     # per cup

    # 🍟 Snacks
    "samosa": 260,                # per piece
    "pakora": 175,                # per 4–5 pieces
    "chips": 160,                 # per small packet
    "popcorn": 120,               # per bowl
    "peanuts": 170,               # per handful

    # 🥛 Dairy
    "milk": 120,                  # per cup (full cream)
    "curd": 150,                  # per cup
    "yogurt": 130,                # per cup
    "cheese": 113,                # per slice
    "butter": 100,                # per tbsp

    # ☕ Beverages
    "tea": 40,                    # per cup
    "coffee": 80,                 # per cup
    "black coffee": 5,            # per cup
    "soft drink": 150,            # per can
    "fruit juice": 120,           # per cup

    # 🍋 Garnish / extras
    "lemon": 5,                   # per wedge
    "lime wedge": 5,              # per wedge
    "chutney": 20,                # per tbsp
    "pickle": 30,                 # per tbsp
}


def estimate_calories(food_items):
    total = 0
    breakdown = []

    for item in food_items:
        name = item["name"].lower()

        calories = CALORIE_DATABASE.get(name, 150)  # fallback
        total += calories

        breakdown.append({
            "name": item["name"],
            "quantity": item["estimated_quantity"],
            "calories": calories
        })

    return total, breakdown
